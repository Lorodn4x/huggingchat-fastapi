from hugchat import hugchat
from hugchat.login import Login
import logging

logger = logging.getLogger(__name__)

class HuggingChatManager:
    def __init__(self, default_model="meta-llama/Meta-Llama-3.1-70B-Instruct"):
        self.default_model = default_model
        self.login = Login()
        self.login.login()
        self.chat = hugchat.Chat(self.login)
        self.chat.set_model(self.default_model)
        logger.info(f"Connected to HuggingChat with model: {self.default_model}")

    def set_model(self, model_name):
        self.chat.set_model(model_name)
        logger.info(f"Model changed to: {model_name}")

    def get_model(self):
        return self.chat.get_model()

    def chat_stream(self, messages, stream=True, **kwargs):
        if stream:
            return self.chat.stream(messages, **kwargs)
        else:
            return self.chat.completions(messages, **kwargs)

    def chat_completions(self, messages, **kwargs):
        return self.chat.completions(messages, **kwargs)

    def get_models(self):
        return self.chat.get_models()

    def __del__(self):
        self.chat.logout()
        logger.info("Disconnected from HuggingChat")