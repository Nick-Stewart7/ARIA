from strands import Agent
from strands.models.ollama import OllamaModel
from strands.models.anthropic import AnthropicModel
from dotenv import load_dotenv
import os

class ModelProviderHandler():
    def __init__(self):
        load_dotenv()
        provider = os.getenv("PROVIDER")
        self.provider = provider
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.api_key = anthropic_key or None
    
    def _create_bedrock(self, model_id = None):
        #todo create bedrock model provider with model options | we just use strands default atm
        pass
    
    def _create_ollama(self, model_id = None):
        model = OllamaModel(
            host="http://localhost:11434",
            model_id="qwen3.5:9b"
        )
        return model

    def _create_anthropic(self, model_id=None):

        model = AnthropicModel(
            client_args={
                "api_key": self.api_key,
            },
            # **model_config
            max_tokens=16000,
            #todo change model id to dynamic user choice
            model_id="claude-sonnet-5",
            params={}
        )

        return model

    def create(self, model_id=None):
        if self.provider == "api":
            model = self._create_anthropic()
        elif self.provider == "ollama":
            model = self._create_ollama()
        else:
            #todo: make actual bedrock provider - needs AWS creds and model options
            model = "us.anthropic.claude-opus-4-6-v1"
        return model
