from pydantic import BaseModel, PrivateAttr
from typing import Type

from langchain_google_genai import ChatGoogleGenerativeAI

import os
from dotenv import load_dotenv
from configs.config import settings

load_dotenv()


class LLMClient:
    _model: str = PrivateAttr()
    _temperature: float = PrivateAttr()
    _llm: ChatGoogleGenerativeAI = PrivateAttr()

    def __init__(
        self,
        model=None,
        temperature=None,
        use_resoning_model=False,
    ):
        # Determine model
        if model is None:
            self._model = (
                settings.get("resoning_model")
                if use_resoning_model
                else settings.get("normal_model")
            )
        else:
            self._model = model

        # Determine temperature
        self._temperature = temperature or settings.get("temperature")

        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        # Initialize LLM
        self._llm = ChatGoogleGenerativeAI(
            model=self._model,
            temperature=self._temperature,
            api_key=api_key,
        )

    def invoke(self, prompt: str, **kwargs) -> str:
        response = self._llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def get_structured_response(
        self,
        prompt: str,
        schema: Type[BaseModel],
    ) -> BaseModel:
        structured_llm = self._llm.with_structured_output(schema)
        response = structured_llm.invoke(prompt)
        return response
