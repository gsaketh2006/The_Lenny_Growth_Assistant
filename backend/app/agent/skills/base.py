from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from backend.app.agent.providers import BaseLLMClient
from backend.app.models.schemas import GroundingResult, ArtifactBase


class BaseSkill(ABC):
    """Base interface for an Agent Skill."""

    name: str
    description: str

    @abstractmethod
    async def execute_stream(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        grounding: GroundingResult,
        llm: BaseLLMClient
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes the skill and yields stream events:
        - {"type": "chunk", "content": "..."}
        - {"type": "artifact", "artifact": ArtifactBase}
        """
        pass
