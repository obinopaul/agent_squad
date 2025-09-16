"""
Daytona Tools for Isolated Code Execution
This module provides custom tools for interacting with Daytona sandboxes
for secure code execution in isolated environments.
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class DaytonaSandboxManager:
    """Manager class for Daytona sandbox operations."""
    
    def __init__(self):
        self.current_sandbox = None
        self.sandbox_id = None
    
    def is_authenticated(self) -> bool:
        """Check if Daytona CLI is authenticated."""
        try:
            result = subprocess.run(
                ["daytona", "profile", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with Daytona (requires manual login)."""
        if self.is_authenticated():
            return {"status": "success", "message": "Already authenticated"}
        
        return {
            "status": "error", 
            "message": "Please run 'daytona login' manually to authenticate"
        }


class CreateSandboxTool(BaseTool):
    """Tool to create a new Daytona sandbox."""
    
    name: str = "create_daytona_sandbox"
    description: str = """Create a new Daytona sandbox for isolated code execution.
    Parameters:
    - target: Target region (default: 'us')
    - snapshot: Snapshot for the sandbox (optional)
    - auto_stop_interval: Auto-stop interval in minutes (default: 15)
    - auto_archive_interval: Auto-archive interval in minutes (default: 10080)
    """
    
    def _run(self, target: str = "us", snapshot: str = "", 
             auto_stop_interval: str = "15", auto_archive_interval: str = "10080") -> str:
        """Create a Daytona sandbox."""
        try:
            cmd = ["daytona", "create"]
            
            if snapshot:
                cmd.extend(["--snapshot", snapshot])
            
            cmd.extend([
                "--target", target,
                "--auto-stop", auto_stop_interval,
                "--auto-archive", auto_archive_interval
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return f"Sandbox created successfully: {result.stdout.strip()}"
            else:
                return f"Error creating sandbox: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Error: Sandbox creation timed out"
        except Exception as e:
            return f"Error creating sandbox: {str(e)}"


class DestroySandboxTool(BaseTool):
    """Tool to destroy a Daytona sandbox."""
    
    name: str = "destroy_daytona_sandbox"
    description: str = "Destroy an existing Daytona sandbox by name or ID."
    
    def _run(self, sandbox_name: str) -> str:
        """Destroy a Daytona sandbox."""
        try:
            result = subprocess.run(
                ["daytona", "delete", sandbox_name, "-y"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return f"Sandbox '{sandbox_name}' destroyed successfully"
            else:
                return f"Error destroying sandbox: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Error: Sandbox destruction timed out"
        except Exception as e:
            return f"Error destroying sandbox: {str(e)}"


class ExecuteCommandTool(BaseTool):
    """Tool to execute commands in a Daytona sandbox."""
    
    name: str = "execute_command_in_sandbox"
    description: str = """Execute a shell command in the active Daytona sandbox.
    Returns stdout, stderr, and exit code.
    """
    
    def _run(self, command: str, sandbox_name: str = "") -> str:
        """Execute a command in the sandbox."""
        try:
            cmd = ["daytona", "exec"]
            if sandbox_name:
                cmd.extend([sandbox_name])
            cmd.extend(["--", "bash", "-c", command])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            output = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return json.dumps(output, indent=2)
            
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Command execution timed out"})
        except Exception as e:
            return json.dumps({"error": f"Command execution failed: {str(e)}"})


class CodeExecutionTool(BaseTool):
    """Tool to execute Python code in a Daytona sandbox."""
    
    name: str = "execute_python_code"
    description: str = """Execute Python code in the active Daytona sandbox.
    The code will be executed in an isolated environment.
    """
    
    def _run(self, code: str, sandbox_name: str = "") -> str:
        """Execute Python code in the sandbox."""
        try:
            # Escape the code for shell execution
            escaped_code = code.replace('"', '\\"').replace('$', '\\$')
            python_command = f'python3 -c "{escaped_code}"'
            
            cmd = ["daytona", "exec"]
            if sandbox_name:
                cmd.extend([sandbox_name])
            cmd.extend(["--", "bash", "-c", python_command])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            output = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "code_executed": code
            }
            
            return json.dumps(output, indent=2)
            
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Code execution timed out"})
        except Exception as e:
            return json.dumps({"error": f"Code execution failed: {str(e)}"})


class FileUploadTool(BaseTool):
    """Tool to upload files to a Daytona sandbox."""
    
    name: str = "upload_file_to_sandbox"
    description: str = """Upload a file to the Daytona sandbox.
    Parameters:
    - file_path: Path where the file should be created in the sandbox
    - content: Content of the file
    - encoding: Encoding of the file (default: 'text')
    - overwrite: Whether to overwrite if file exists (default: True)
    """
    
    def _run(self, file_path: str, content: str, encoding: str = "text", 
             overwrite: bool = True, sandbox_name: str = "") -> str:
        """Upload a file to the sandbox."""
        try:
            # Create a temporary file locally
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as tmp_file:
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                # Use daytona cp to copy file to sandbox
                cmd = ["daytona", "cp", tmp_file_path]
                if sandbox_name:
                    cmd.append(f"{sandbox_name}:{file_path}")
                else:
                    cmd.append(f":{file_path}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return f"File uploaded successfully to {file_path}"
                else:
                    return f"Error uploading file: {result.stderr.strip()}"
                    
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
        except Exception as e:
            return f"Error uploading file: {str(e)}"


class FileDownloadTool(BaseTool):
    """Tool to download files from a Daytona sandbox."""
    
    name: str = "download_file_from_sandbox"
    description: str = """Download a file from the Daytona sandbox.
    Returns the file content as text or indicates if it's binary.
    """
    
    def _run(self, file_path: str, sandbox_name: str = "") -> str:
        """Download a file from the sandbox."""
        try:
            import tempfile
            
            # Create a temporary file to download to
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp_file:
                tmp_file_path = tmp_file.name
            
            try:
                # Use daytona cp to copy file from sandbox
                cmd = ["daytona", "cp"]
                if sandbox_name:
                    cmd.append(f"{sandbox_name}:{file_path}")
                else:
                    cmd.append(f":{file_path}")
                cmd.append(tmp_file_path)
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Read the downloaded file
                    try:
                        with open(tmp_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        return f"File content from {file_path}:\n{content}"
                    except UnicodeDecodeError:
                        return f"File {file_path} appears to be binary and cannot be displayed as text"
                else:
                    return f"Error downloading file: {result.stderr.strip()}"
                    
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                
        except Exception as e:
            return f"Error downloading file: {str(e)}"


class ListSandboxesTool(BaseTool):
    """Tool to list available Daytona sandboxes."""
    
    name: str = "list_daytona_sandboxes"
    description: str = "List all available Daytona sandboxes with their status."
    
    def _run(self) -> str:
        """List all Daytona sandboxes."""
        try:
            result = subprocess.run(
                ["daytona", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return f"Available sandboxes:\n{result.stdout}"
            else:
                return f"Error listing sandboxes: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Error: Listing sandboxes timed out"
        except Exception as e:
            return f"Error listing sandboxes: {str(e)}"


class GitCloneTool(BaseTool):
    """Tool to clone Git repositories in a Daytona sandbox."""
    
    name: str = "git_clone_in_sandbox"
    description: str = """Clone a Git repository in the Daytona sandbox.
    Parameters:
    - url: Repository URL
    - path: Target directory (optional)
    - branch: Branch to clone (optional)
    """
    
    def _run(self, url: str, path: str = "", branch: str = "", sandbox_name: str = "") -> str:
        """Clone a Git repository in the sandbox."""
        try:
            git_command = f"git clone"
            if branch:
                git_command += f" -b {branch}"
            git_command += f" {url}"
            if path:
                git_command += f" {path}"
            
            cmd = ["daytona", "exec"]
            if sandbox_name:
                cmd.extend([sandbox_name])
            cmd.extend(["--", "bash", "-c", git_command])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return f"Repository cloned successfully:\n{result.stdout}"
            else:
                return f"Error cloning repository: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Error: Git clone timed out"
        except Exception as e:
            return f"Error cloning repository: {str(e)}"


def get_daytona_tools() -> List[BaseTool]:
    """Get all Daytona tools for the isolated environment agent."""
    return [
        CreateSandboxTool(),
        DestroySandboxTool(),
        ExecuteCommandTool(),
        CodeExecutionTool(),
        FileUploadTool(),
        FileDownloadTool(),
        ListSandboxesTool(),
        GitCloneTool()
    ]


# Summary of all Daytona actions available:
DAYTONA_ACTIONS = {
    "sandbox_management": [
        "create_daytona_sandbox - Create a new sandbox",
        "destroy_daytona_sandbox - Remove an existing sandbox",
        "list_daytona_sandboxes - List all available sandboxes"
    ],
    "code_execution": [
        "execute_python_code - Execute Python code in isolated environment",
        "execute_command_in_sandbox - Run shell commands in sandbox"
    ],
    "file_operations": [
        "upload_file_to_sandbox - Upload files to sandbox",
        "download_file_from_sandbox - Download files from sandbox"
    ],
    "git_operations": [
        "git_clone_in_sandbox - Clone Git repositories in sandbox"
    ],
    "additional_capabilities": [
        "Preview URLs for web applications",
        "Language Server Protocol support",
        "Log streaming",
        "Directory operations (create, list, move, delete)",
        "File info retrieval"
    ]
}