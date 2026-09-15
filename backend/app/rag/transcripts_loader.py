import os
import glob
import re
from typing import List, Dict, Any
import yaml
from backend.app.core.config import settings
from backend.app.core.logging import logger


class TranscriptChunkData:
    def __init__(
        self,
        episode_id: str,
        episode_title: str,
        guest_name: str,
        episode_url: str,
        publication_date: str,
        chunk_index: int,
        content: str,
        token_count: int
    ):
        self.episode_id = episode_id
        self.episode_title = episode_title
        self.guest_name = guest_name
        self.episode_url = episode_url
        self.publication_date = publication_date
        self.chunk_index = chunk_index
        self.content = content
        self.token_count = token_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "episode_title": self.episode_title,
            "guest_name": self.guest_name,
            "episode_url": self.episode_url,
            "publication_date": self.publication_date,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "token_count": self.token_count,
        }


def parse_transcript_file(file_path: str) -> Dict[str, Any]:
    """Parses YAML frontmatter and transcript body from a markdown file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        raw_text = f.read()

    frontmatter = {}
    body = raw_text

    # Match YAML frontmatter between --- and ---
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, re.DOTALL)
    if match:
        fm_text, body = match.groups()
        try:
            frontmatter = yaml.safe_load(fm_text) or {}
        except Exception as e:
            logger.warning(f"Error parsing frontmatter in {file_path}: {e}")

    # Fallback metadata from directory name
    dir_name = os.path.basename(os.path.dirname(file_path))
    guest = frontmatter.get("guest") or dir_name.replace("-", " ").title()
    title = frontmatter.get("title") or f"Interview with {guest}"
    url = frontmatter.get("youtube_url") or ""
    pub_date = str(frontmatter.get("publish_date") or "")
    keywords = frontmatter.get("keywords") or []

    return {
        "episode_id": dir_name,
        "guest_name": guest,
        "episode_title": title,
        "episode_url": url,
        "publication_date": pub_date,
        "keywords": keywords,
        "body": body.strip(),
    }


def chunk_transcript(
    parsed: Dict[str, Any],
    target_chunk_words: int = 400,
    overlap_words: int = 60
) -> List[TranscriptChunkData]:
    """Splits transcript text into overlapping chunks with metadata context."""
    body = parsed["body"]
    # Remove large headings if repeated
    body = re.sub(r"^# .*\n", "", body)
    body = re.sub(r"^## Transcript\s*\n", "", body)

    # Split by paragraphs or speaker blocks
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    
    chunks: List[TranscriptChunkData] = []
    current_words: List[str] = []
    chunk_idx = 0

    for para in paragraphs:
        para_words = para.split()
        if not para_words:
            continue

        if len(current_words) + len(para_words) > target_chunk_words and current_words:
            # Create chunk
            chunk_text = " ".join(current_words)
            chunks.append(
                TranscriptChunkData(
                    episode_id=parsed["episode_id"],
                    episode_title=parsed["episode_title"],
                    guest_name=parsed["guest_name"],
                    episode_url=parsed["episode_url"],
                    publication_date=parsed["publication_date"],
                    chunk_index=chunk_idx,
                    content=chunk_text,
                    token_count=len(current_words)
                )
            )
            chunk_idx += 1
            # Keep overlap
            current_words = current_words[-overlap_words:] + para_words
        else:
            current_words.extend(para_words)

    # Add final chunk if any
    if current_words:
        chunk_text = " ".join(current_words)
        chunks.append(
            TranscriptChunkData(
                episode_id=parsed["episode_id"],
                episode_title=parsed["episode_title"],
                guest_name=parsed["guest_name"],
                episode_url=parsed["episode_url"],
                publication_date=parsed["publication_date"],
                chunk_index=chunk_idx,
                content=chunk_text,
                token_count=len(current_words)
            )
        )

    return chunks


def load_all_transcripts(
    transcripts_dir: str = None,
    max_episodes: int = None
) -> List[Dict[str, Any]]:
    """Discovers and parses all transcript files in the archive."""
    base_dir = transcripts_dir or settings.TRANSCRIPTS_DIR
    search_path = os.path.join(base_dir, "episodes", "*", "*.md")
    files = glob.glob(search_path)
    
    if not files:
        # Check direct folder
        search_path = os.path.join(base_dir, "*", "*.md")
        files = glob.glob(search_path)

    logger.info(f"Found {len(files)} transcript markdown files in {base_dir}")
    if max_episodes and max_episodes < len(files):
        files = files[:max_episodes]

    results = []
    for fp in files:
        parsed = parse_transcript_file(fp)
        if parsed["body"]:
            results.append(parsed)

    return results
