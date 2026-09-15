from typing import List, Dict, Any, AsyncGenerator
from backend.app.agent.skills.base import BaseSkill
from backend.app.agent.providers import BaseLLMClient
from backend.app.models.schemas import GroundingResult, ArtifactBase


class Ship30EssaySkill(BaseSkill):
    name = "ship30_essay"
    description = (
        "Converts grounded podcast wisdom into a ~1,250-word, high-engagement essay "
        "following the proven Ship 30 for 30 online writing methodology."
    )

    async def execute_stream(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        grounding: GroundingResult,
        llm: BaseLLMClient
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if grounding.is_refusal:
            yield {
                "type": "chunk",
                "content": (
                    f"⚠️ **Insufficient Grounding for Essay Generation**\n\n"
                    f"{grounding.refusal_reason}\n\n"
                    f"Cannot draft a grounded Ship 30 for 30 essay without relevant podcast source transcripts."
                )
            }
            return

        # Build context from retrieved chunks
        context_blocks = []
        for i, cit in enumerate(grounding.citations, start=1):
            context_blocks.append(
                f"[Source {i} | Guest: {cit.guest_name} | Episode: '{cit.episode_title}']\n"
                f"{cit.snippet}\n"
            )
        context_text = "\n---\n".join(context_blocks)

        system_prompt = (
            "You are an elite ghostwriter and growth operator trained in the Ship 30 for 30 digital writing methodology.\n"
            "Your mission: Transform the provided Lenny's Podcast transcript insights into a publication-ready, ~1,250-word essay.\n\n"
            "SHIP 30 FOR 30 WRITING RULES:\n"
            "1. THE HOOK: Open with a bold, curiosity-driven headline followed by a 2-sentence hook stating the high-stakes problem and the unexpected solution.\n"
            "2. 1-3-1 CADENCE: Use short paragraphs with rhythmic spacing. Alternate single punchy sentences with 3-sentence explanations.\n"
            "3. 3-5 THEMATIC SECTIONS: Divide the essay into 3 to 5 clear subheadings (e.g., '1. The Loop That Replaced the Funnel', '2. Why Most Retention Curves Flatten Too Early').\n"
            "4. REAL GROUNDED EXAMPLES: Ground every point in the provided podcast context. Cite the guest (e.g., 'As Brian Balfour explained on Lenny's Podcast...') and quote them verbatim.\n"
            "5. NO FLUFF: Every sentence must teach a tactical lesson, framework, or counter-intuitive insight.\n"
            "6. THE 24-HOUR ACTION TAKEAWAY: End with a concrete, 1-step action the reader can implement in their product team tomorrow.\n"
            "7. FORMAT: Output clean, rich Markdown with bold highlights and bullet points.\n\n"
            f"TRANSCRIPT SOURCES:\n{context_text}"
        )

        user_prompt = f"Write a comprehensive ~1,250-word Ship 30 for 30–style essay addressing: {query}"
        messages = [{"role": "user", "content": user_prompt}]

        yield {
            "type": "chunk",
            "content": "✍️ **Generating Ship 30 for 30 Thought Leadership Essay...**\n\nMounting live essay preview in the Artifact Viewer beside this chat.\n\n---\n\n"
        }

        full_essay_tokens = []
        async for token in llm.generate_stream(messages, system_prompt=system_prompt, temperature=0.5):
            full_essay_tokens.append(token)
            yield {"type": "chunk", "content": token}

        full_essay_content = "".join(full_essay_tokens)
        
        # Extract title from first line or markdown header
        first_line = full_essay_content.split("\n")[0].replace("#", "").strip()
        essay_title = first_line if first_line else "Growth Strategy Essay (Ship 30 Framework)"

        # Emit live artifact event for the sandboxed viewer
        artifact = ArtifactBase(
            title=essay_title[:80],
            artifact_type="markdown",
            content=full_essay_content,
            structured_data={
                "framework": "Ship 30 for 30",
                "word_count": len(full_essay_content.split()),
                "sources_used": [c.guest_name for c in grounding.citations]
            },
            version=1
        )
        yield {"type": "artifact", "artifact": artifact}


ship30_essay_skill = Ship30EssaySkill()
