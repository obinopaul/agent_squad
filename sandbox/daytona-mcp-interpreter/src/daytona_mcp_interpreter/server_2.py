#!/usr/bin/env python
import shlex
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import time
import uuid
import base64
import mimetypes
import tempfile
import urllib.parse
from typing import List, Optional, Any, Union

import aiofiles
from dotenv import load_dotenv

# Use the asynchronous version of the Daytona SDK
from daytona_sdk import AsyncDaytona, DaytonaConfig, CreateSandboxFromSnapshotParams
from daytona_sdk.models.workspace import Workspace
from daytona_sdk.models.sandbox import SandboxState
from daytona_api_client.api.toolbox_api import ToolboxApi
from daytona_sdk.common.process import ExecuteResponse
from daytona_sdk.filesystem import FileSystem # Async filesystem

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource


# Custom exception classes for better error handling
class DaytonaError(Exception):
    """Base exception class for all Daytona-related errors."""
    pass

class WorkspaceError(DaytonaError):
    """Exception raised for workspace-related errors."""
    pass

class WorkspaceInitializationError(WorkspaceError):
    """Exception raised when workspace initialization fails."""
    pass

class WorkspaceNotFoundError(WorkspaceError):
    """Exception raised when a workspace is not found."""
    pass

class WorkspaceQuotaExceededError(WorkspaceError):
    """Exception raised when CPU quota is exceeded."""
    pass

class FileSystemError(DaytonaError):
    """Exception raised for filesystem-related errors."""
    pass

class FileNotAccessibleError(FileSystemError):
    """Exception raised when a file cannot be accessed."""
    pass

class FileTooLargeError(FileSystemError):
    """Exception raised when a file is too large to process."""
    pass

class CommandExecutionError(DaytonaError):
    """Exception raised when a command execution fails."""
    pass

class ConfigurationError(DaytonaError):
    """Exception raised for configuration-related errors."""
    pass

class NetworkError(DaytonaError):
    """Exception raised for network-related errors."""
    pass

# Initialize mimetypes
mimetypes.init()

# Configure logging
LOG_FILE = '/tmp/daytona-interpreter.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# File to track workspace ID across multiple processes
WORKSPACE_TRACKING_FILE = '/tmp/daytona-workspace.json'
WORKSPACE_LOCK_FILE = '/tmp/daytona-workspace.lock'

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

def setup_logging() -> logging.Logger:
    """Configure logging with file and console output"""
    logger = logging.getLogger("daytona-interpreter")
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        # File handler
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger


def normalize_path(path: str) -> str:
    """
    Normalize a path to ensure proper UTF-8 encoding and handling of URL-encoded characters.
    """
    try:
        # First, ensure the path is properly URL-decoded
        return urllib.parse.unquote(path)
    except Exception as e:
        logging.getLogger("daytona-interpreter").error(f"Error normalizing path '{path}': {str(e)}")
        return path  # Return original path if decoding fails

class Config:
    """Server configuration class that loads environment variables for MCP Daytona setup"""
    def __init__(self):
        try:
            load_dotenv()
            logger = logging.getLogger("daytona-interpreter")
            
            # Required API key for authentication
            self.api_key = os.getenv('MCP_DAYTONA_API_KEY')
            if not self.api_key:
                raise ConfigurationError("MCP_DAYTONA_API_KEY environment variable is required")

            # Optional configuration with defaults
            self.server_url = os.getenv('MCP_DAYTONA_SERVER_URL', 'https://app.daytona.io/api')
            if not self.server_url.startswith(('http://', 'https://')):
                self.server_url = f"https://{self.server_url}"
            
            self.target = os.getenv('MCP_DAYTONA_TARGET', 'eu')
            
            timeout_str = os.getenv('MCP_DAYTONA_TIMEOUT', '180.0')
            try:
                self.timeout = float(timeout_str)
            except ValueError:
                self.timeout = 180.0
            
            self.verify_ssl = os.getenv('MCP_VERIFY_SSL', 'false').lower() == 'true'
            self._log_config()
            
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize configuration: {str(e)}") from e

    def _log_config(self) -> None:
        """Logs the current configuration settings excluding sensitive information."""
        logger = logging.getLogger("daytona-interpreter")
        logger.debug("Configuration Loaded:")
        logger.debug(f"  Server URL: {self.server_url}")
        logger.debug(f"  Target: {self.target}")
        logger.debug(f"  Timeout: {self.timeout}")

class DaytonaInterpreter:
    """
    MCP Server for executing code and shell commands in Daytona workspaces.
    """

    def __init__(self, logger: logging.Logger, config: Config):
        self.logger = logger
        self.config = config

        # Initialize Daytona SDK async client
        self.daytona = AsyncDaytona(
            config=DaytonaConfig(
                api_key=self.config.api_key,
                api_url=self.config.server_url,
                target=self.config.target
            )
        )

        self.workspace: Optional[Workspace] = None
        self.filesystem: Optional[FileSystem] = None
        self.workspace_root_dir: Optional[str] = None

        self.server = Server("daytona-interpreter")
        self.setup_handlers()

        @self.server.list_resources()
        async def list_resources():
            return []

        @self.server.list_prompts()
        async def list_prompts():
            return []

        self.logger.info("Initialized DaytonaInterpreter with Async Daytona SDK and MCP Server")

    def setup_notification_handlers(self):
        """Configure handlers for MCP protocol notifications."""
        async def handle_shutdown(params: dict[str, Any]) -> None:
            self.logger.info("Received shutdown notification, initiating cleanup.")
            asyncio.create_task(self.cleanup_workspace())

        async def handle_cancelled(params: dict[str, Any]) -> None:
            self.logger.info(f"Received cancelled notification: {params}")

        # Register handlers
        self.server.notification_handlers["notifications/shutdown"] = handle_shutdown
        self.server.notification_handlers["notifications/cancelled"] = handle_cancelled

    def setup_handlers(self):
        """Configure server request handlers for tool listing and execution."""
        self.setup_notification_handlers()

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Defines the available tools for the MCP client."""
            return [
                Tool(
                    name="shell_exec",
                    description="Execute shell commands in the ephemeral Daytona Linux environment. Returns stdout, stderr, and exit code.",
                    inputSchema={
                        "type": "object",
                        "properties": {"command": {"type": "string", "description": "Shell command to execute."}},
                        "required": ["command"]
                    }
                ),
                Tool(
                    name="list_files",
                    description="List files and directories at a given path in the workspace. Returns a structured list of file information.",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "The directory path to list. Defaults to the workspace root."}},
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="file_download",
                    description="Download files from the Daytona workspace. Handles text, binary, and image files automatically.",
                    inputSchema={
                        "type": "object",
                        "properties": {"file_path": {"type": "string", "description": "Path to the file in the workspace"}},
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="file_upload",
                    description="Upload files to the Daytona workspace from text or base64-encoded content.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to create the file in the workspace."},
                            "content": {"type": "string", "description": "Content to write (text or base64)."},
                            "encoding": {"type": "string", "description": "'text' (default) or 'base64'."}
                        },
                        "required": ["file_path", "content"]
                    }
                ),
                Tool(
                    name="create_directory",
                    description="Create a new directory at the specified path. Creates parent directories if they don't exist.",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "The full path of the directory to create."}},
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="delete_file",
                    description="Delete a file or an empty directory from the workspace.",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "The path to the file or directory to delete."}},
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="git_clone",
                    description="Clone a Git repository into the Daytona workspace.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {"type": "string", "description": "URL of the Git repository."},
                            "target_path": {"type": "string", "description": "Optional target directory."},
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="web_preview",
                    description="Generate an accessible preview URL for a web application running in the workspace.",
                    inputSchema={
                        "type": "object",
                        "properties": {"port": {"type": "integer", "description": "The port number the server is running on."}},
                        "required": ["port"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
            """Handle tool execution requests from MCP."""
            if not self.workspace:
                raise WorkspaceError("Workspace is not initialized.")
            
            try:
                if name == "shell_exec":
                    command = arguments.get("command")
                    if not command: raise ValueError("Command is required")
                    result = await self.execute_command(command)
                    return [TextContent(type="text", text=result)]

                elif name == "list_files":
                    path = arguments.get("path", self.workspace_root_dir or ".")
                    result = await self._tool_list_files(normalize_path(path))
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                elif name == "file_download":
                    file_path = arguments.get("file_path")
                    if not file_path: raise ValueError("file_path is required")
                    return await self._tool_file_download(normalize_path(file_path))

                elif name == "file_upload":
                    file_path = arguments.get("file_path")
                    content = arguments.get("content")
                    encoding = arguments.get("encoding", "text")
                    if not file_path or content is None: raise ValueError("file_path and content are required")
                    result = await self._tool_file_upload(normalize_path(file_path), content, encoding)
                    return [TextContent(type="text", text=result)]

                elif name == "create_directory":
                    path = arguments.get("path")
                    if not path: raise ValueError("path is required")
                    result = await self._tool_create_directory(normalize_path(path))
                    return [TextContent(type="text", text=result)]
                
                elif name == "delete_file":
                    path = arguments.get("path")
                    if not path: raise ValueError("path is required")
                    result = await self._tool_delete_file(normalize_path(path))
                    return [TextContent(type="text", text=result)]

                elif name == "git_clone":
                    repo_url = arguments.get("repo_url")
                    target_path = arguments.get("target_path")
                    if not repo_url: raise ValueError("repo_url is required")
                    result = await self._tool_git_clone(repo_url, target_path)
                    return [TextContent(type="text", text=result)]

                elif name == "web_preview":
                    port = arguments.get("port")
                    if port is None: raise ValueError("Port is required")
                    result = await self._tool_web_preview(int(port))
                    return [TextContent(type="text", text=result)]
                    
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                self.logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {e}")]

    async def _wait_for_command_exec_ready(self, max_wait_seconds: int = 60):
        """Poll the workspace until it is ready to accept commands."""
        self.logger.info(f"Waiting for workspace {self.workspace.id} to become responsive...")
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                response = await self.workspace.process.exec("echo 'ready'")
                if response.exit_code == 0:
                    self.logger.info(f"Workspace {self.workspace.id} is ready.")
                    return
            except Exception as e:
                self.logger.debug(f"Workspace not ready, connection failed: {e}")
            await asyncio.sleep(2.0)
        raise WorkspaceInitializationError(f"Workspace did not become responsive within {max_wait_seconds} seconds.")

    async def initialize_workspace(self) -> None:
        """Initialize or reuse a Daytona workspace, handling different states."""
        if self.workspace:
            return

        with FileLock(WORKSPACE_LOCK_FILE):
            workspace_id, _ = await get_active_workspace()
            if workspace_id:
                try:
                    self.logger.info(f"Found active workspace ID: {workspace_id}")
                    self.workspace = await self.daytona.get(workspace_id)
                    
                    # If workspace is stopped or archived, start it
                    if self.workspace.state in [SandboxState.STOPPED, SandboxState.ARCHIVED]:
                        self.logger.info(f"Workspace {self.workspace.id} is {self.workspace.state.value}, starting it...")
                        await self.daytona.start(self.workspace)
                        self.workspace = await self.daytona.get(self.workspace.id) # Refresh state

                    await self._wait_for_command_exec_ready()
                    
                except Exception as e:
                    self.logger.warning(f"Failed to reuse workspace {workspace_id}: {e}. Creating a new one.")
                    await clear_active_workspace()
                    self.workspace = None # Reset before creating a new one

            if not self.workspace:
                self.logger.info("Creating a new Daytona workspace...")
                params = CreateSandboxFromSnapshotParams(language="python", os_user="workspace")
                self.workspace = await self.daytona.create(params)
                await self._wait_for_command_exec_ready()
                await set_active_workspace(self.workspace.id)
            
            # Common setup for both new and reused workspaces
            self.filesystem = self.workspace.fs
            response = await self.workspace.process.exec("echo $HOME")
            self.workspace_root_dir = response.result.strip() if response.exit_code == 0 else "/home/workspace"
            self.logger.info(f"Workspace root directory set to: {self.workspace_root_dir}")

    async def execute_command(self, command: str) -> str:
        """Execute a shell command in the workspace."""
        if '&&' in command or command.strip().startswith('cd '):
            command_to_run = f'/bin/sh -c {shlex.quote(command)}'
        else:
            command_to_run = command.strip()

        self.logger.debug(f"Executing command: {command_to_run}")
        response = await self.workspace.process.exec(command_to_run)
        
        result = {
            "stdout": str(response.result).strip(),
            "stderr": "",  # Note: Daytona SDK currently merges stdout/stderr
            "exit_code": response.exit_code
        }
        self.logger.info(f"Command completed with exit code: {result['exit_code']}")
        return json.dumps(result, indent=2)

    async def cleanup_workspace(self) -> None:
        """Clean up the Daytona workspace by deleting it."""
        if not self.workspace:
            return
        
        workspace_id = self.workspace.id
        self.logger.info(f"Starting cleanup for workspace: {workspace_id}")
        
        try:
            with FileLock(WORKSPACE_LOCK_FILE):
                active_id, _ = await get_active_workspace()
                if active_id and active_id == workspace_id:
                    await self.daytona.delete(self.workspace)
                    await clear_active_workspace()
                    self.logger.info(f"Successfully deleted workspace: {workspace_id}")
        except Exception as e:
            self.logger.error(f"Error during workspace cleanup: {e}", exc_info=True)
        finally:
            self.workspace = None
            self.filesystem = None

    async def _tool_list_files(self, path: str) -> List[dict]:
        """Implementation for the list_files tool."""
        self.logger.info(f"Listing files at path: {path}")
        files = await self.filesystem.list_files(path)
        return [
            {
                "name": f.name,
                "path": os.path.join(path, f.name),
                "is_dir": f.is_dir,
                "size": f.size,
            }
            for f in files
        ]

    async def _tool_file_download(self, file_path: str) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Implementation for the file_download tool."""
        self.logger.info(f"Downloading file: {file_path}")
        file_content = await self.filesystem.download_file(file_path)
        
        # Process content for different file types
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

        if mime_type.startswith("image/"):
            base64_content = base64.b64encode(file_content).decode('utf-8')
            return [ImageContent(type="image", data=base64_content, mimeType=mime_type)]
        
        try:
            # Try to decode as text
            text_content = file_content.decode('utf-8')
            return [TextContent(type="text", text=text_content)]
        except UnicodeDecodeError:
            # Fallback to binary resource
            base64_content = base64.b64encode(file_content).decode('utf-8')
            return [EmbeddedResource(
                type="resource",
                resource={"uri": f"file://{file_path}", "data": base64_content, "mimeType": mime_type}
            )]

    async def _tool_file_upload(self, file_path: str, content: str, encoding: str) -> str:
        """Implementation for the file_upload tool."""
        self.logger.info(f"Uploading file to: {file_path} with encoding: {encoding}")
        if encoding.lower() == "base64":
            binary_content = base64.b64decode(content)
        else:
            binary_content = content.encode('utf-8')
        
        await self.filesystem.upload_file(binary_content, file_path)
        return f"File '{file_path}' uploaded successfully ({len(binary_content)} bytes)."

    async def _tool_create_directory(self, path: str) -> str:
        """Implementation for the create_directory tool."""
        self.logger.info(f"Creating directory: {path}")
        await self.filesystem.create_folder(path)
        return f"Directory '{path}' created successfully."

    async def _tool_delete_file(self, path: str) -> str:
        """Implementation for the delete_file tool."""
        self.logger.info(f"Deleting file or directory: {path}")
        await self.filesystem.delete_file(path)
        return f"Path '{path}' deleted successfully."

    async def _tool_git_clone(self, repo_url: str, target_path: Optional[str]) -> str:
        """Implementation for the git_clone tool."""
        self.logger.info(f"Cloning repository: {repo_url}")
        target_dir = target_path if target_path else ''
        command = f"git clone {shlex.quote(repo_url)} {shlex.quote(target_dir)}"
        return await self.execute_command(command)

    async def _tool_web_preview(self, port: int) -> str:
        """Implementation for the web_preview tool."""
        self.logger.info(f"Generating web preview for port: {port}")
        # The async SDK might have a simpler way, but manual construction is reliable
        try:
            # Extract node domain from provider metadata (JSON)
            node_domain = json.loads(self.workspace.instance.info.provider_metadata)['nodeDomain']
            preview_url = f"http://{port}-{self.workspace.id}.{node_domain}"
            return json.dumps({"status": "success", "preview_url": preview_url})
        except Exception as e:
            self.logger.error(f"Could not generate preview URL: {e}")
            raise NetworkError(f"Failed to generate preview URL. Ensure the workspace provider metadata is available. Error: {e}")

    async def run(self) -> None:
        """Main server execution loop."""
        try:
            await self.initialize_workspace()
            async with stdio_server() as streams:
                self.logger.info("MCP server running with stdio communication")
                await self.server.run(streams[0], streams[1], self.server.create_initialization_options())
        except Exception as e:
            self.logger.error(f"Server run failed: {e}", exc_info=True)
        finally:
            self.logger.info("Server shutting down, cleaning up workspace...")
            await self.cleanup_workspace()

# Simple file-based lock for inter-process coordination.
class FileLock:
    def __init__(self, lock_file, timeout_seconds=10):
        self.lock_file = lock_file
        self.lock_fd = None
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger("daytona-interpreter")

    def acquire(self):
        start_time = time.time()
        while time.time() - start_time < self.timeout_seconds:
            try:
                self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.lock_fd, str(os.getpid()).encode())
                return True
            except OSError:
                time.sleep(0.2)
        return False

    def release(self):
        if self.lock_fd is not None:
            os.close(self.lock_fd)
            try:
                os.unlink(self.lock_file)
            except OSError:
                pass
            self.lock_fd = None

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock on {self.lock_file} within {self.timeout_seconds}s")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

# Asynchronous helpers for workspace tracking file
async def get_active_workspace():
    try:
        if os.path.exists(WORKSPACE_TRACKING_FILE):
            async with aiofiles.open(WORKSPACE_TRACKING_FILE, 'r') as f:
                content = await f.read()
                data = json.loads(content)
                return data.get('workspace_id'), data.get('created_at')
    except Exception as e:
        logging.getLogger("daytona-interpreter").error(f"Failed to read workspace tracking file: {e}")
    return None, None

async def set_active_workspace(workspace_id: str):
    data = {'workspace_id': workspace_id, 'created_at': int(time.time()), 'pid': os.getpid()}
    try:
        async with aiofiles.open(WORKSPACE_TRACKING_FILE, 'w') as f:
            await f.write(json.dumps(data))
    except Exception as e:
        logging.getLogger("daytona-interpreter").error(f"Failed to write workspace tracking file: {e}")

async def clear_active_workspace():
    try:
        if os.path.exists(WORKSPACE_TRACKING_FILE):
            os.unlink(WORKSPACE_TRACKING_FILE)
    except Exception as e:
        logging.getLogger("daytona-interpreter").error(f"Failed to remove workspace tracking file: {e}")

async def main():
    logger = setup_logging()
    logger.addHandler(logging.StreamHandler(sys.stderr)) # Also log to stderr for visibility
    
    interpreter = None
    try:
        config = Config()
        interpreter = DaytonaInterpreter(logger, config)
        await interpreter.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Server interrupted. Shutting down.")
    except Exception as e:
        logger.critical(f"A fatal error occurred: {e}", exc_info=True)
    finally:
        if interpreter:
            await interpreter.cleanup_workspace()
        logger.info("Server shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass