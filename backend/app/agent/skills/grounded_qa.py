from typing import List, Dict, Any, AsyncGenerator
from backend.app.agent.skills.base import BaseSkill
from backend.app.agent.providers import BaseLLMClient
from backend.app.models.schemas import GroundingResult


class GroundedQASkill(BaseSkill):
    name = "grounded_qa"
    description = "Answers product management and growth questions strictly grounded in Lenny's podcast transcripts."

    async def execute_stream(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        grounding: GroundingResult,
        llm: BaseLLMClient
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # Handle Insufficient Grounding / Refusal
        if grounding.is_refusal:
            yield {
                "type": "chunk",
                "content": (
                    f"⚠️ **Insufficient Grounding in Lenny's Podcast Archive**\n\n"
                    f"{grounding.refusal_reason}\n\n"
                    f"*Tip: Try asking about PM frameworks, growth loops, B2B PLG, retention inflection points, "
                    f"pricing experiments, or specific guests like Brian Balfour, Elena Verna, Shreyas Doshi, or Marty Cagan.*"
                )
            }
            return

        # Build context from retrieved chunks
        context_blocks = []
        for i, cit in enumerate(grounding.citations, start=1):
            context_blocks.append(
                f"[Source {i} | Guest: {cit.guest_name} | Episode: '{cit.episode_title}' | Score: {cit.similarity_score}]\n"
                f"{cit.snippet}\n"
            )
        context_text = "\n---\n".join(context_blocks)

        system_prompt = (
            "You are 'The Lenny Growth Assistant', an elite Forward Deployed Product & Growth expert.\n"
            "Your knowledge base is STRICTLY grounded in Lenny Rachitsky's podcast and newsletter transcripts.\n\n"
            "CRITICAL OPERATING RULES:\n"
            "1. Ground every claim directly in the provided transcript context.\n"
            "2. Cite the specific guest and episode title whenever you reference a concept or framework.\n"
            "3. Use bracketed citation markers like [^1], [^2] corresponding to the provided Source numbers.\n"
            "4. Quote key phrases directly from guests when highlighting tactical metrics or contrarian principles.\n"
            "5. If a specific nuance was not discussed in the provided sources, explicitly state: 'This specific nuance was not detailed in the episode.' Never invent details.\n"
            "6. Provide structured, executive-ready formatting: clear bold takeaways, actionable bullets, and concise conclusions.\n\n"
            f"RELEVANT PODCAST TRANSCRIPT SOURCES:\n{context_text}"
        )

        messages = list(chat_history)
        messages.append({"role": "user", "content": query})

        async for token in llm.generate_stream(messages, system_prompt=system_prompt, temperature=0.3):
            yield {"type": "chunk", "content": token}


grounded_qa_skill = GroundedQASkill()
