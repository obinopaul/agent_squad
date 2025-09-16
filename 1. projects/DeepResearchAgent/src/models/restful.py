import json
from typing import Dict, List, Optional, Any
from collections.abc import Generator
from openai.types.chat import ChatCompletion
import requests
import os
from PIL import Image

from src.models.base import (ApiModel,
                             Model,
                             ChatMessage,
                             tool_role_conversions,
                             ChatMessageStreamDelta,
                             ChatMessageToolCallStreamDelta)
from src.models.message_manager import MessageManager
from src.logger import TokenUsage, logger
from src.utils import encode_image_base64


class RestfulClient():
    def __init__(self,
                 api_base: str,
                 api_key: str,
                 api_type: str = "chat/completions",
                 model_id: str = "o3",
                 http_client=None):
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        self.model_id = model_id

        self.http_client = http_client

    def completion(self,
                   model,
                   messages,
                   **kwargs):

        headers = {
            "app_key": self.api_key,
            "Content-Type": "application/json"
        }

        model = model.split("/")[-1]
        data = {
            "model": model,
            "messages": messages,
        }

        # Add any additional kwargs to the data
        if kwargs:
            data.update(kwargs)

        response = requests.post(
            f"{self.api_base}/{self.api_type}",
            json=data,
            headers=headers,
        )

        return response.json()

class RestfulResponseClient():
    def __init__(self,
                 api_base: str,
                 api_key: str,
                 api_type: str = "responses",
                 model_id: str = "o3",
                 http_client=None):
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        self.model_id = model_id

        self.http_client = http_client

    def completion(self,
                   model,
                   input,
                   tools,
                   **kwargs):

        headers = {
            "app_key": self.api_key,
            "Content-Type": "application/json"
        }

        model = model.split("/")[-1]
        data = {
            "model": model,
            "input": input,
            "tools": tools,
            "stream": False,
        }

        # Add any additional kwargs to the data
        if kwargs:
            data.update(kwargs)

        response = requests.post(
            f"{self.api_base}/{self.api_type}",
            json=data,
            headers=headers,
        )

        response_text = response.text
        for line in response_text.split('\n'):
            if line.strip():
                try:
                    json_line = line.strip()
                    if json_line.startswith("data: ") and "response.completed" in json_line:
                        json_line = json_line.replace("data: ", "").strip()
                        res = json.loads(json_line)['response']
                        return res
                except Exception as e:
                    logger.error(f"Error parsing line: {line}, error: {e}")


class RestfulTranscribeClient():
    def __init__(self,
                 api_base: str,
                 api_key: str,
                 api_type: str = "wisper",
                 model_id: str = "wisper",
                 http_client=None):
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        self.model_id = model_id

        self.http_client = http_client

    def completion(self,
                   model,
                   file_stream,
                   **kwargs):

        files = {'file': file_stream}
        headers = {
            "app_key": self.api_key,
        }
        response = requests.post(f"{self.api_base}/{self.api_type}", headers=headers, files=files)

        return response.json()

class RestfulImagenClient():
    def __init__(self,
                 api_base: str,
                 api_key: str,
                 api_type: str = "imagen",
                 model_id: str = "imagen",
                 http_client=None):
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        self.model_id = model_id

        self.http_client = http_client

    def completion(self,
                   model,
                   prompt: str,
                   **kwargs):
        headers = {
            "app_key": self.api_key,
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1
            }
        }

        # Add any additional kwargs to the data
        if kwargs:
            data.update(kwargs)

        response = requests.post(
            f"{self.api_base}/{self.api_type}",
            json=data,
            headers=headers,
        )

        return response.json()


class RestfulVeoPredictClient():
    def __init__(self,
                 api_base: str,
                 api_key: str,
                 api_type: str = "veo/predict",
                 model_id: str = "veo3",
                 http_client=None):
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        self.model_id = model_id

        self.http_client = http_client

    def completion(self,
                   model,
                   prompt: str,
                   image: str = None,
                   **kwargs):
        headers = {
            "app_key": self.api_key,
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1
            }
        }

        if image and os.path.exists(image):
            img = Image.open(image)
            image_data = {
                "bytesBase64Encoded": encode_image_base64(img),
                "mimeType": "image/png"
            }
            data["instances"][0]["image"] = image_data

        # Add any additional kwargs to the data
        if kwargs:
            data.update(kwargs)

        response = requests.post(
            f"{self.api_base}/{self.api_type}",
            json=data,
            headers=headers,
        )

        return response.json()

class RestfulVeoFetchClient():
    def __init__(self,
                 api_base: str,
                 api_key: str,
                 api_type: str = "veo/fetch",
                 model_id: str = "veo3",
                 http_client=None):
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        self.model_id = model_id

        self.http_client = http_client

    def completion(self,
                   model,
                   name: str,
                   **kwargs):
        headers = {
            "app_key": self.api_key,
            "Content-Type": "application/json"
        }

        data = {
            "operationName": name,
        }

        # Add any additional kwargs to the data
        if kwargs:
            data.update(kwargs)

        response = requests.post(
            f"{self.api_base}/{self.api_type}",
            json=data,
            headers=headers,
        )

        return response.json()

class RestfulModel(ApiModel):
    """This model connects to an OpenAI-compatible API server.

    Parameters:
        model_id (`str`):
            The model identifier to use on the server (e.g. "gpt-3.5-turbo").
        api_base (`str`, *optional*):
            The base URL of the OpenAI-compatible API server.
        api_key (`str`, *optional*):
            The API key to use for authentication.
        organization (`str`, *optional*):
            The organization to use for the API request.
        project (`str`, *optional*):
            The project to use for the API request.
        client_kwargs (`dict[str, Any]`, *optional*):
            Additional keyword arguments to pass to the OpenAI client (like organization, project, max_retries etc.).
        custom_role_conversions (`dict[str, str]`, *optional*):
            Custom role conversion mapping to convert message roles in others.
            Useful for specific models that do not support specific message roles like "system".
        flatten_messages_as_text (`bool`, default `False`):
            Whether to flatten messages as text.
        **kwargs:
            Additional keyword arguments to pass to the OpenAI API.
    """

    def __init__(
        self,
        model_id: str,
        api_base: Optional[str] = None,
        api_type: str = "chat/completions",
        api_key: Optional[str] = None,
        custom_role_conversions: dict[str, str] | None = None,
        flatten_messages_as_text: bool = False,
        http_client=None,
        **kwargs,
    ):
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        flatten_messages_as_text = (
            flatten_messages_as_text
            if flatten_messages_as_text is not None
            else model_id.startswith(("ollama", "groq", "cerebras"))
        )

        self.http_client = http_client

        self.message_manager = MessageManager(model_id=model_id)

        super().__init__(
            model_id=model_id,
            custom_role_conversions=custom_role_conversions,
            flatten_messages_as_text=flatten_messages_as_text,
            **kwargs,
        )

    def create_client(self):
        return RestfulClient(api_base=self.api_base,
                             api_key=self.api_key,
                             api_type=self.api_type,
                             model_id=self.model_id,
                             http_client=self.http_client)

    def _prepare_completion_kwargs(
            self,
            messages: list[ChatMessage],
            stop_sequences: list[str] | None = None,
            response_format: dict[str, str] | None = None,
            tools_to_call_from: list[Any] | None = None,
            custom_role_conversions: dict[str, str] | None = None,
            convert_images_to_image_urls: bool = False,
            tool_choice: str | dict | None = "required",  # Configurable tool_choice parameter
            **kwargs,
    ) -> dict[str, Any]:
        """
        Prepare parameters required for model invocation, handling parameter priorities.

        Parameter priority from high to low:
        1. Explicitly passed kwargs
        2. Specific parameters (stop_sequences, response_format, etc.)
        3. Default values in self.kwargs
        """
        # Clean and standardize the message list
        flatten_messages_as_text = kwargs.pop("flatten_messages_as_text", self.flatten_messages_as_text)
        messages_as_dicts = self.message_manager.get_clean_message_list(
            messages,
            role_conversions=custom_role_conversions or tool_role_conversions,
            convert_images_to_image_urls=convert_images_to_image_urls,
            flatten_messages_as_text=flatten_messages_as_text,
        )
        # Use self.kwargs as the base configuration
        completion_kwargs = {
            **self.kwargs,
            "messages": messages_as_dicts,
        }

        # Handle specific parameters
        if stop_sequences is not None:
            completion_kwargs["stop"] = stop_sequences
        if response_format is not None:
            completion_kwargs["response_format"] = response_format

        # Handle tools parameter
        if tools_to_call_from:
            tools_config = {
                "tools": [self.message_manager.get_tool_json_schema(tool, model_id=self.model_id) for tool in
                          tools_to_call_from],
            }
            if tool_choice is not None:
                tools_config["tool_choice"] = tool_choice
            completion_kwargs.update(tools_config)

        # Finally, use the passed-in kwargs to override all settings
        completion_kwargs.update(kwargs)

        completion_kwargs = self.message_manager.get_clean_completion_kwargs(completion_kwargs)

        return completion_kwargs

    def generate_stream(self,
                        messages: list[ChatMessage],
                        stop_sequences: list[str] | None = None,
                        response_format: dict[str, str] | None = None,
                        tools_to_call_from: list[Any] | None = None,
                        **kwargs,
                        )-> Generator[ChatMessageStreamDelta]:

        completion_kwargs = self._prepare_completion_kwargs(
            messages=messages,
            stop_sequences=stop_sequences,
            response_format=response_format,
            tools_to_call_from=tools_to_call_from,
            model=self.model_id,
            custom_role_conversions=self.custom_role_conversions,
            convert_images_to_image_urls=True,
            **kwargs,
        )

        for event in self.client.completion(**completion_kwargs, stream=True, stream_options={"include_usage": True}):
            if getattr(event, "usage", None):
                self._last_input_token_count = event.usage.prompt_tokens
                self._last_output_token_count = event.usage.completion_tokens
                yield ChatMessageStreamDelta(
                    content="",
                    token_usage=TokenUsage(
                        input_tokens=event.usage.prompt_tokens,
                        output_tokens=event.usage.completion_tokens,
                    ),
                )
            if event.choices:
                choice = event.choices[0]
                if choice.delta:
                    yield ChatMessageStreamDelta(
                        content=choice.delta.content,
                        tool_calls=[
                            ChatMessageToolCallStreamDelta(
                                index=delta.index,
                                id=delta.id,
                                type=delta.type,
                                function=delta.function,
                            )
                            for delta in choice.delta.tool_calls
                        ]
                        if choice.delta.tool_calls
                        else None,
                    )
                else:
                    if not getattr(choice, "finish_reason", None):
                        raise ValueError(f"No content or tool calls in event: {event}")


    async def generate(
        self,
        messages: list[ChatMessage],
        stop_sequences: list[str] | None = None,
        response_format: dict[str, str] | None = None,
        tools_to_call_from: list[Any] | None = None,
        **kwargs,
    ) -> ChatMessage:

        completion_kwargs = self._prepare_completion_kwargs(
            messages=messages,
            stop_sequences=stop_sequences,
            response_format=response_format,
            tools_to_call_from=tools_to_call_from,
            model=self.model_id,
            convert_images_to_image_urls=True,
            custom_role_conversions=self.custom_role_conversions,
            **kwargs,
        )

        # Async call to the LiteLLM client for completion
        response = self.client.completion(**completion_kwargs)

        response = ChatCompletion.model_validate(response)

        self._last_input_token_count = response.usage.prompt_tokens
        self._last_output_token_count = response.usage.completion_tokens
        return ChatMessage.from_dict(
            response.choices[0].message.model_dump(include={"role", "content", "tool_calls"}),
            raw=response,
            token_usage=TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            ),
        )

    async def __call__(self, *args, **kwargs) -> ChatMessage:
        """
        Call the model with the given arguments.
        This is a convenience method that calls `generate` with the same arguments.
        """
        return await self.generate(*args, **kwargs)


class RestfulTranscribeModel(ApiModel):
    """This model connects to an OpenAI-compatible API server for transcription.

    Parameters:
        model_id (`str`):
            The model identifier to use on the server (e.g. "whisper-1").
        api_base (`str`, *optional*):
            The base URL of the OpenAI-compatible API server.
        api_key (`str`, *optional*):
            The API key to use for authentication.
        **kwargs:
            Additional keyword arguments to pass to the OpenAI API.
    """

    def __init__(self,
                 model_id: str,
                 api_base: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_type: str = "wisper",
                 http_client=None,
                 **kwargs):
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type

        self.http_client = http_client

        super().__init__(model_id=model_id, **kwargs)

    def create_client(self):
        return RestfulTranscribeClient(api_base=self.api_base,
                                       api_key=self.api_key,
                                       api_type=self.api_type,
                                       model_id=self.model_id,
                                       http_client=self.http_client)

    def generate(
        self,
        file_stream: Any,
        **kwargs,
    ) -> str:
        """
        Generate a transcription from the given file stream.

        Parameters:
            file_stream (Any): The file stream to transcribe.
            **kwargs: Additional keyword arguments for the transcription request.

        Returns:
            ChatMessage: The transcription result.
        """
        response = self.client.completion(
            model=self.model_id,
            file_stream=file_stream,
            **kwargs,
        )

        return response.get("text", "No transcription available.")

    def __call__(self, *args, **kwargs) -> str:
        """
        Call the model with the given arguments.
        This is a convenience method that calls `generate` with the same arguments.
        """
        return self.generate(*args, **kwargs)


class RestfulImagenModel(ApiModel):
    """This model connects to an OpenAI-compatible API server for transcription.

    Parameters:
        model_id (`str`):
            The model identifier to use on the server (e.g. "whisper-1").
        api_base (`str`, *optional*):
            The base URL of the OpenAI-compatible API server.
        api_key (`str`, *optional*):
            The API key to use for authentication.
        **kwargs:
            Additional keyword arguments to pass to the OpenAI API.
    """

    def __init__(self,
                 model_id: str,
                 api_base: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_type: str = "imagen",
                 http_client=None,
                 **kwargs):
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type

        self.http_client = http_client

        super().__init__(model_id=model_id, **kwargs)

    def create_client(self):
        return RestfulImagenClient(api_base=self.api_base,
                                   api_key=self.api_key,
                                   api_type=self.api_type,
                                   model_id=self.model_id,
                                   http_client=self.http_client)

    def generate(
        self,
        prompt: str,
        **kwargs,
    ) -> str:
        """
        Generate a transcription from the given file stream.

        Parameters:
            file_stream (Any): The file stream to transcribe.
            **kwargs: Additional keyword arguments for the transcription request.

        Returns:
            ChatMessage: The transcription result.
        """
        response = self.client.completion(
            model=self.model_id,
            prompt=prompt,
            **kwargs,
        )

        base64 = response['resp_data']['predictions'][0]["bytesBase64Encoded"]

        return base64

    def __call__(self, *args, **kwargs) -> str:
        """
        Call the model with the given arguments.
        This is a convenience method that calls `generate` with the same arguments.
        """
        return self.generate(*args, **kwargs)


class RestfulVeoPridictModel(ApiModel):
    """This model connects to an OpenAI-compatible API server for transcription.

    Parameters:
        model_id (`str`):
            The model identifier to use on the server (e.g. "veo-3").
        api_base (`str`, *optional*):
            The base URL of the OpenAI-compatible API server.
        api_key (`str`, *optional*):
            The API key to use for authentication.
        **kwargs:
            Additional keyword arguments to pass to the OpenAI API.
    """

    def __init__(self,
                 model_id: str,
                 api_base: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_type: str = "veo/predict",
                 http_client=None,
                 **kwargs):


        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type

        self.http_client = http_client

        super().__init__(model_id=model_id, **kwargs)

    def create_client(self):
        return RestfulVeoPredictClient(api_base=self.api_base,
                                       api_key=self.api_key,
                                       api_type=self.api_type,
                                       model_id=self.model_id,
                                       http_client=self.http_client)

    def generate(
        self,
        prompt: str,
        image: str = None,
        **kwargs,
    ) -> str:
        """
        Generate a transcription from the given file stream.

        Parameters:
            file_stream (Any): The file stream to transcribe.
            **kwargs: Additional keyword arguments for the transcription request.

        Returns:
            ChatMessage: The transcription result.
        """
        logger.info(f"Generating with model {self.model_id} using prompt: {prompt} and image: {image}, please wait...")
        response = self.client.completion(
            model=self.model_id,
            prompt=prompt,
            image=image,
            **kwargs,
        )

        name = response['resp_data']['name']

        return name

    def __call__(self, *args, **kwargs) -> str:
        """
        Call the model with the given arguments.
        This is a convenience method that calls `generate` with the same arguments.
        """
        return self.generate(*args, **kwargs)

class RestfulVeoFetchModel(ApiModel):
    """This model connects to an OpenAI-compatible API server for transcription.

    Parameters:
        model_id (`str`):
            The model identifier to use on the server (e.g. "veo-3").
        api_base (`str`, *optional*):
            The base URL of the OpenAI-compatible API server.
        api_key (`str`, *optional*):
            The API key to use for authentication.
        **kwargs:
            Additional keyword arguments to pass to the OpenAI API.
    """

    def __init__(self,
                 model_id: str,
                 api_base: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_type: str = "veo/fetch",
                 http_client=None,
                 **kwargs):

        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type

        self.http_client = http_client

        super().__init__(model_id=model_id, **kwargs)

    def create_client(self):
        return RestfulVeoFetchClient(api_base=self.api_base,
                                       api_key=self.api_key,
                                       api_type=self.api_type,
                                       model_id=self.model_id,
                                       http_client=self.http_client)

    def generate(
        self,
        name: str,
        **kwargs,
    ) -> str:
        """
        Generate a transcription from the given file stream.

        Parameters:
            file_stream (Any): The file stream to transcribe.
            **kwargs: Additional keyword arguments for the transcription request.

        Returns:
            ChatMessage: The transcription result.
        """
        logger.info(f"Fetching with model {self.model_id} using name: {name}, please wait...")
        response = self.client.completion(
            model=self.model_id,
            name=name,
            **kwargs,
        )

        base64 = response['resp_data']['response']["videos"][0]["bytesBase64Encoded"]

        return base64

    def __call__(self, *args, **kwargs) -> str:
        """
        Call the model with the given arguments.
        This is a convenience method that calls `generate` with the same arguments.
        """
        return self.generate(*args, **kwargs)


class RestfulResponseModel(ApiModel):
    """This model connects to an OpenAI-compatible API server.

    Parameters:
        model_id (`str`):
            The model identifier to use on the server (e.g. "gpt-3.5-turbo").
        api_base (`str`, *optional*):
            The base URL of the OpenAI-compatible API server.
        api_key (`str`, *optional*):
            The API key to use for authentication.
        organization (`str`, *optional*):
            The organization to use for the API request.
        project (`str`, *optional*):
            The project to use for the API request.
        client_kwargs (`dict[str, Any]`, *optional*):
            Additional keyword arguments to pass to the OpenAI client (like organization, project, max_retries etc.).
        custom_role_conversions (`dict[str, str]`, *optional*):
            Custom role conversion mapping to convert message roles in others.
            Useful for specific models that do not support specific message roles like "system".
        flatten_messages_as_text (`bool`, default `False`):
            Whether to flatten messages as text.
        **kwargs:
            Additional keyword arguments to pass to the OpenAI API.
    """

    def __init__(
        self,
        model_id: str,
        api_base: Optional[str] = None,
        api_type: str = "chat/completions",
        api_key: Optional[str] = None,
        custom_role_conversions: dict[str, str] | None = None,
        flatten_messages_as_text: bool = False,
        http_client=None,
        **kwargs,
    ):
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.api_type = api_type
        flatten_messages_as_text = (
            flatten_messages_as_text
            if flatten_messages_as_text is not None
            else model_id.startswith(("ollama", "groq", "cerebras"))
        )

        self.http_client = http_client

        self.message_manager = MessageManager(model_id=model_id)

        super().__init__(
            model_id=model_id,
            custom_role_conversions=custom_role_conversions,
            flatten_messages_as_text=flatten_messages_as_text,
            **kwargs,
        )

    def create_client(self):
        return RestfulResponseClient(api_base=self.api_base,
                             api_key=self.api_key,
                             api_type=self.api_type,
                             model_id=self.model_id,
                             http_client=self.http_client)

    def _prepare_completion_kwargs(
            self,
            messages: list[ChatMessage],
            stop_sequences: list[str] | None = None,
            response_format: dict[str, str] | None = None,
            tools_to_call_from: list[Any] | None = None,
            custom_role_conversions: dict[str, str] | None = None,
            convert_images_to_image_urls: bool = False,
            tool_choice: str | dict | None = "required",  # Configurable tool_choice parameter
            **kwargs,
    ) -> dict[str, Any]:
        """
        Prepare parameters required for model invocation, handling parameter priorities.

        Parameter priority from high to low:
        1. Explicitly passed kwargs
        2. Specific parameters (stop_sequences, response_format, etc.)
        3. Default values in self.kwargs
        """
        # Clean and standardize the message list
        flatten_messages_as_text = kwargs.pop("flatten_messages_as_text", self.flatten_messages_as_text)
        messages_as_dicts = self.message_manager.get_clean_message_list(
            messages,
            role_conversions=custom_role_conversions or tool_role_conversions,
            convert_images_to_image_urls=convert_images_to_image_urls,
            flatten_messages_as_text=flatten_messages_as_text,
        )
        # Use self.kwargs as the base configuration
        completion_kwargs = {
            **self.kwargs,
            "input": messages_as_dicts,
        }

        # Handle specific parameters
        if stop_sequences is not None:
            completion_kwargs["stop"] = stop_sequences
        if response_format is not None:
            completion_kwargs["response_format"] = response_format

        completion_kwargs['tools'] = [
            {"type": "web_search_preview"},
            {
                "type": "code_interpreter",
                "container": {"type": "auto"}
            }
        ]

        # Handle tools parameter
        if tools_to_call_from:
            tools_config = {
                "tools": [self.message_manager.get_tool_json_schema(tool, model_id=self.model_id) for tool in
                          tools_to_call_from],
            }
            if tool_choice is not None:
                tools_config["tool_choice"] = tool_choice
            completion_kwargs.update(tools_config)

        # Finally, use the passed-in kwargs to override all settings
        completion_kwargs.update(kwargs)

        completion_kwargs = self.message_manager.get_clean_completion_kwargs(completion_kwargs)

        return completion_kwargs

    def generate_stream(self,
                        messages: list[ChatMessage],
                        stop_sequences: list[str] | None = None,
                        response_format: dict[str, str] | None = None,
                        tools_to_call_from: list[Any] | None = None,
                        **kwargs,
                        )-> Generator[ChatMessageStreamDelta]:

        completion_kwargs = self._prepare_completion_kwargs(
            messages=messages,
            stop_sequences=stop_sequences,
            response_format=response_format,
            tools_to_call_from=tools_to_call_from,
            model=self.model_id,
            custom_role_conversions=self.custom_role_conversions,
            convert_images_to_image_urls=True,
            **kwargs,
        )

        for event in self.client.completion(**completion_kwargs, stream=True, stream_options={"include_usage": True}):
            if getattr(event, "usage", None):
                self._last_input_token_count = event.usage.prompt_tokens
                self._last_output_token_count = event.usage.completion_tokens
                yield ChatMessageStreamDelta(
                    content="",
                    token_usage=TokenUsage(
                        input_tokens=event.usage.prompt_tokens,
                        output_tokens=event.usage.completion_tokens,
                    ),
                )
            if event.choices:
                choice = event.choices[0]
                if choice.delta:
                    yield ChatMessageStreamDelta(
                        content=choice.delta.content,
                        tool_calls=[
                            ChatMessageToolCallStreamDelta(
                                index=delta.index,
                                id=delta.id,
                                type=delta.type,
                                function=delta.function,
                            )
                            for delta in choice.delta.tool_calls
                        ]
                        if choice.delta.tool_calls
                        else None,
                    )
                else:
                    if not getattr(choice, "finish_reason", None):
                        raise ValueError(f"No content or tool calls in event: {event}")


    async def generate(
        self,
        messages: list[ChatMessage],
        stop_sequences: list[str] | None = None,
        response_format: dict[str, str] | None = None,
        tools_to_call_from: list[Any] | None = None,
        **kwargs,
    ) -> ChatMessage:

        completion_kwargs = self._prepare_completion_kwargs(
            messages=messages,
            stop_sequences=stop_sequences,
            response_format=response_format,
            tools_to_call_from=tools_to_call_from,
            model=self.model_id,
            convert_images_to_image_urls=True,
            custom_role_conversions=self.custom_role_conversions,
            **kwargs,
        )

        # Async call to the LiteLLM client for completion
        response = self.client.completion(**completion_kwargs)

        self._last_input_token_count = response["usage"]["input_tokens"]
        self._last_output_token_count = response["usage"]["output_tokens"]

        res_dict = response["output"][-1]
        res_dict['content'] = res_dict['content'][-1]['text']
        res_dict['tool_calls'] = []

        return ChatMessage.from_dict(
            res_dict,
            raw=response,
            token_usage=TokenUsage(
                input_tokens=response["usage"]["input_tokens"],
                output_tokens=response["usage"]["output_tokens"],
            ),
        )

    async def __call__(self, *args, **kwargs) -> ChatMessage:
        """
        Call the model with the given arguments.
        This is a convenience method that calls `generate` with the same arguments.
        """
        return await self.generate(*args, **kwargs)