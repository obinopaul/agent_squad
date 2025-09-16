import os
from openai import OpenAI, AsyncOpenAI
from typing import Dict, Any, Tuple

from dotenv import load_dotenv
load_dotenv(verbose=True)

from langchain_openai import ChatOpenAI

from src.logger import logger
from src.models.litellm import LiteLLMModel
from src.models.openaillm import OpenAIServerModel
from src.models.hfllm import InferenceClientModel
from src.models.restful import (RestfulModel,
                                RestfulTranscribeModel,
                                RestfulImagenModel,
                                RestfulVeoPridictModel,
                                RestfulVeoFetchModel,
                                RestfulResponseModel)
from src.utils import Singleton
from src.proxy.local_proxy import HTTP_CLIENT, ASYNC_HTTP_CLIENT

custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}
PLACEHOLDER = "PLACEHOLDER"


class ModelManager(metaclass=Singleton):
    def __init__(self):
        self.registed_models: Dict[str, Any] = {}
        
    def init_models(self, use_local_proxy: bool = False):
        self._register_openai_models(use_local_proxy=use_local_proxy)
        self._register_anthropic_models(use_local_proxy=use_local_proxy)
        self._register_google_models(use_local_proxy=use_local_proxy)
        self._register_qwen_models(use_local_proxy=use_local_proxy)
        self._register_langchain_models(use_local_proxy=use_local_proxy)
        self._register_vllm_models(use_local_proxy=use_local_proxy)
        self._register_deepseek_models(use_local_proxy=use_local_proxy)

    def _check_local_api_key(self, local_api_key_name: str, remote_api_key_name: str) -> str:
        api_key = os.getenv(local_api_key_name, PLACEHOLDER)
        if api_key == PLACEHOLDER:
            logger.warning(f"Local API key {local_api_key_name} is not set, using remote API key {remote_api_key_name}")
            api_key = os.getenv(remote_api_key_name, PLACEHOLDER)
        return api_key
    
    def _check_local_api_base(self, local_api_base_name: str, remote_api_base_name: str) -> str:
        api_base = os.getenv(local_api_base_name, PLACEHOLDER)
        if api_base == PLACEHOLDER:
            logger.warning(f"Local API base {local_api_base_name} is not set, using remote API base {remote_api_base_name}")
            api_base = os.getenv(remote_api_base_name, PLACEHOLDER)
        return api_base
    
    def _register_openai_models(self, use_local_proxy: bool = False):
        # gpt-4o, gpt-4.1, o1, o3, gpt-4o-search-preview
        if use_local_proxy:
            logger.info("Using local proxy for OpenAI models")
            api_key = self._check_local_api_key(local_api_key_name="SKYWORK_API_KEY",
                                                remote_api_key_name="OPENAI_API_KEY")
            
            # gpt-4o
            model_name = "gpt-4o"
            model_id = "openai/gpt-4o"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_AZURE_US_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = LiteLLMModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
            
            # gpt-4.1
            model_name = "gpt-4.1"
            model_id = "openai/gpt-4.1"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_AZURE_US_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = LiteLLMModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
            
            # o1
            model_name = "o1"
            model_id = "openai/o1"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_AZURE_US_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = LiteLLMModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
            
            # o3
            model_name = "o3"
            model_id = "openai/o3"

            model = RestfulModel(
                api_base=self._check_local_api_base(local_api_base_name="SKYWORK_AZURE_US_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE"),
                api_type="chat/completions",
                api_key=api_key,
                model_id=model_id,
                http_client=HTTP_CLIENT,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
            
            # gpt-4o-search-preview
            model_name = "gpt-4o-search-preview"
            model_id = "gpt-4o-search-preview"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_OPENROUTER_US_API_BASE", 
                                                    remote_api_base_name="OPENAI_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = LiteLLMModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            # wisper
            model_name = "whisper"
            model_id = "whisper"
            model = RestfulTranscribeModel(
                api_base=self._check_local_api_base(local_api_base_name="SKYWORK_AZURE_BJ_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE"),
                api_key=api_key,
                api_type="whisper",
                model_id=model_id,
                http_client=HTTP_CLIENT,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            # deep research
            model_name = "o3-deep-research"
            model_id = "o3-deep-research"

            model = RestfulResponseModel(
                api_base=self._check_local_api_base(local_api_base_name="SKYWORK_SHUBIAOBIAO_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE"),
                api_key=api_key,
                api_type="responses",
                model_id=model_id,
                http_client=HTTP_CLIENT,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
            
            # gpt-5
            model_name = "gpt-5"
            model_id = "openai/gpt-5"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_AZURE_US_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = LiteLLMModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
            
        else:
            logger.info("Using remote API for OpenAI models")
            api_key = self._check_local_api_key(local_api_key_name="OPENAI_API_KEY", 
                                                remote_api_key_name="OPENAI_API_KEY")
            api_base = self._check_local_api_base(local_api_base_name="OPENAI_API_BASE", 
                                                    remote_api_base_name="OPENAI_API_BASE")
            
            models = [
                {
                    "model_name": "gpt-4o",
                    "model_id": "gpt-4o",
                },
                {
                    "model_name": "gpt-4.1",
                    "model_id": "gpt-4.1",
                },
                {
                    "model_name": "o1",
                    "model_id": "o1",
                },
                {
                    "model_name": "o3",
                    "model_id": "o3",
                },
                {
                    "model_name": "gpt-4o-search-preview",
                    "model_id": "gpt-4o-search-preview",
                },
            ]
            
            for model in models:
                model_name = model["model_name"]
                model_id = model["model_id"]
                model = LiteLLMModel(
                    model_id=model_id,
                    api_key=api_key,
                    api_base=api_base,
                    custom_role_conversions=custom_role_conversions,
                )
                self.registed_models[model_name] = model
    
            
    def _register_anthropic_models(self, use_local_proxy: bool = False):
        # claude37-sonnet, claude37-sonnet-thinking
        if use_local_proxy:
            logger.info("Using local proxy for Anthropic models")
            api_key = self._check_local_api_key(local_api_key_name="SKYWORK_API_KEY", 
                                                remote_api_key_name="ANTHROPIC_API_KEY")
            
            # claude37-sonnet
            model_name = "claude37-sonnet"
            model_id = "claude37-sonnet"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_OPENROUTER_US_API_BASE",
                                                    remote_api_base_name="ANTHROPIC_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
            
            # claude37-sonnet-thinking
            model_name = "claude-3.7-sonnet-thinking"
            model_id = "claude-3.7-sonnet-thinking"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_OPENROUTER_US_API_BASE",
                                                    remote_api_base_name="ANTHROPIC_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            # claude-4-sonnet
            model_name = "claude-4-sonnet"
            model_id = "claude-4-sonnet"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_OPENROUTER_US_API_BASE",
                                                    remote_api_base_name="ANTHROPIC_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

        else:
            logger.info("Using remote API for Anthropic models")
            api_key = self._check_local_api_key(local_api_key_name="ANTHROPIC_API_KEY", 
                                                remote_api_key_name="ANTHROPIC_API_KEY")
            api_base = self._check_local_api_base(local_api_base_name="ANTHROPIC_API_BASE", 
                                                    remote_api_base_name="ANTHROPIC_API_BASE")
            
            models = [
                {
                    "model_name": "claude37-sonnet",
                    "model_id": "claude-3-7-sonnet-20250219",
                },
                {
                    "model_name": "claude37-sonnet-thinking",
                    "model_id": "claude-3-7-sonnet-20250219",
                },
            ]
            
            for model in models:
                model_name = model["model_name"]
                model_id = model["model_id"]
                model = LiteLLMModel(
                    model_id=model_id,
                    api_key=api_key,
                    api_base=api_base,
                    custom_role_conversions=custom_role_conversions,
                )
                self.registed_models[model_name] = model
            
    def _register_google_models(self, use_local_proxy: bool = False):
        if use_local_proxy:
            logger.info("Using local proxy for Google models")
            api_key = self._check_local_api_key(local_api_key_name="SKYWORK_API_KEY", 
                                                remote_api_key_name="GOOGLE_API_KEY")
            
            # gemini-2.5-pro
            model_name = "gemini-2.5-pro"
            model_id = "gemini-2.5-pro-preview-06-05"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._check_local_api_base(local_api_base_name="SKYWORK_OPENROUTER_BJ_API_BASE",
                                                    remote_api_base_name="GOOGLE_API_BASE"),
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            # imagen
            model_name = "imagen"
            model_id = "imagen-3.0-generate-001"
            model = RestfulImagenModel(
                api_base=self._check_local_api_base(local_api_base_name="SKYWORK_GOOGLE_API_BASE",
                                                    remote_api_base_name="GOOGLE_API_BASE"),
                api_key=api_key,
                api_type="imagen",
                model_id=model_id,
                http_client=HTTP_CLIENT,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            # veo3
            model_name = "veo3-predict"
            model_id = "veo-3.0-generate-preview"
            model = RestfulVeoPridictModel(
                api_base=self._check_local_api_base(local_api_base_name="SKYWORK_GOOGLE_API_BASE",
                                                    remote_api_base_name="GOOGLE_API_BASE"),
                api_key=api_key,
                api_type="veo/predict",
                model_id=model_id,
                http_client=HTTP_CLIENT,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            model_name = "veo3-fetch"
            model_id = "veo-3.0-generate-preview"
            model = RestfulVeoFetchModel(
                api_base=self._check_local_api_base(local_api_base_name="SKYWORK_GOOGLE_API_BASE",
                                                    remote_api_base_name="GOOGLE_API_BASE"),
                api_key=api_key,
                api_type="veo/fetch",
                model_id=model_id,
                http_client=HTTP_CLIENT,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            
        else:
            logger.info("Using remote API for Google models")
            api_key = self._check_local_api_key(local_api_key_name="GOOGLE_API_KEY", 
                                                remote_api_key_name="GOOGLE_API_KEY")
            api_base = self._check_local_api_base(local_api_base_name="GOOGLE_API_BASE", 
                                                    remote_api_base_name="GOOGLE_API_BASE")
            
            models = [
                {
                    "model_name": "gemini-2.5-pro",
                    "model_id": "gemini-2.5-pro-preview-06-05",
                },
            ]
            
            for model in models:
                model_name = model["model_name"]
                model_id = model["model_id"]
                model = LiteLLMModel(
                    model_id=model_id,
                    api_key=api_key,
                    # api_base=api_base,
                    custom_role_conversions=custom_role_conversions,
                )
                self.registed_models[model_name] = model
                
    def _register_qwen_models(self, use_local_proxy: bool = False):
        # qwen2.5-7b-instruct
        models = [
            {
                "model_name": "qwen2.5-7b-instruct",
                "model_id": "Qwen/Qwen2.5-7B-Instruct",
            },
            {
                "model_name": "qwen2.5-14b-instruct",
                "model_id": "Qwen/Qwen2.5-14B-Instruct",
            },
            {
                "model_name": "qwen2.5-32b-instruct",
                "model_id": "Qwen/Qwen2.5-32B-Instruct",
            },
        ]
        for model in models:
            model_name = model["model_name"]
            model_id = model["model_id"]
            
            model = InferenceClientModel(
                model_id=model_id,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

    def _register_langchain_models(self, use_local_proxy: bool = False):
        # langchain models
        models = [
            {
                "model_name": "langchain-gpt-4o",
                "model_id": "gpt-4o",
            },
            {
                "model_name": "langchain-gpt-4.1",
                "model_id": "gpt-4.1",
            },
            {
                "model_name": "langchain-o3",
                "model_id": "o3",
            },
        ]

        if use_local_proxy:
            logger.info("Using local proxy for LangChain models")
            api_key = self._check_local_api_key(local_api_key_name="SKYWORK_API_KEY",
                                                remote_api_key_name="OPENAI_API_KEY")
            api_base = self._check_local_api_base(local_api_base_name="SKYWORK_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE")

            for model in models:
                model_name = model["model_name"]
                model_id = model["model_id"]

                model = ChatOpenAI(
                    model=model_id,
                    api_key=api_key,
                    base_url=api_base,
                    http_client=HTTP_CLIENT,
                    http_async_client=ASYNC_HTTP_CLIENT,
                )
                self.registed_models[model_name] = model

        else:
            logger.info("Using remote API for LangChain models")
            api_key = self._check_local_api_key(local_api_key_name="OPENAI_API_KEY",
                                                remote_api_key_name="OPENAI_API_KEY")
            api_base = self._check_local_api_base(local_api_base_name="OPENAI_API_BASE",
                                                    remote_api_base_name="OPENAI_API_BASE")

            for model in models:
                model_name = model["model_name"]
                model_id = model["model_id"]

                model = ChatOpenAI(
                    model=model_id,
                    api_key=api_key,
                    base_url=api_base,
                )
                self.registed_models[model_name] = model
    def _register_vllm_models(self, use_local_proxy: bool = False):
        # qwen
        api_key = self._check_local_api_key(local_api_key_name="QWEN_API_KEY", 
                                                remote_api_key_name="QWEN_API_KEY")
        api_base = self._check_local_api_base(local_api_base_name="QWEN_API_BASE", 
                                                    remote_api_base_name="QWEN_API_BASE")
        models = [
            {
                "model_name": "Qwen",
                "model_id": "Qwen",
            }
        ]
        for model in models:
            model_name = model["model_name"]
            model_id = model["model_id"]
            
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=api_base,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

        # Qwen-VL
        api_key_VL = self._check_local_api_key(local_api_key_name="QWEN_VL_API_KEY", 
                                                remote_api_key_name="QWEN_VL_API_KEY")
        api_base_VL = self._check_local_api_base(local_api_base_name="QWEN_VL_API_BASE", 
                                                    remote_api_base_name="QWEN_VL_API_BASE")
        models = [
            {
                "model_name": "Qwen-VL",
                "model_id": "Qwen-VL",
            }
        ]
        for model in models:
            model_name = model["model_name"]
            model_id = model["model_id"]

            client = AsyncOpenAI(
                api_key=api_key_VL,
                base_url=api_base_VL,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

    def _register_deepseek_models(self, use_local_proxy: bool = False):
        # deepseek models
        if use_local_proxy:
            # deepseek-chat
            logger.info("Using local proxy for DeepSeek models")
            api_key = self._check_local_api_key(local_api_key_name="SKYWORK_API_KEY",
                                                remote_api_key_name="SKYWORK_API_KEY")
            api_base = self._check_local_api_base(local_api_base_name="SKYWORK_DEEPSEEK_API_BASE",
                                                  remote_api_base_name="SKYWORK_API_BASE")

            model_name = "deepseek-chat"
            model_id = "deepseek-chat"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=api_base,
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model

            # deepseek-reasoner
            api_key = self._check_local_api_key(local_api_key_name="SKYWORK_API_KEY",
                                                remote_api_key_name="SKYWORK_API_KEY")
            api_base = self._check_local_api_base(local_api_base_name="SKYWORK_DEEPSEEK_API_BASE",
                                                    remote_api_base_name="SKYWORK_API_BASE")

            model_name = "deepseek-reasoner"
            model_id = "deepseek-reasoner"
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=api_base,
                http_client=ASYNC_HTTP_CLIENT,
            )
            model = OpenAIServerModel(
                model_id=model_id,
                http_client=client,
                custom_role_conversions=custom_role_conversions,
            )
            self.registed_models[model_name] = model
        else:
            logger.warning("DeepSeek models are not supported in remote API mode.")