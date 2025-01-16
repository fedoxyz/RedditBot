import os
from dataclasses import dataclass
from dotenv import load_dotenv
from logger import logger


load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT")
DEBUG = os.getenv("DEBUG")
GROQ_API = os.getenv("GROQ_API")

@dataclass
class Comment:
    comment_id: str
    content: str
    author: str
    score: int
    created_utc: float
    mood: str = "unknown"

    def update_score(self, new_score: int):
        self.score = new_score

    @classmethod
    def from_reddit_comment(cls, comment):
        return cls(
            comment_id=comment.id,
            content=comment.body,
            author=comment.author.name if comment.author else "[deleted]",
            score=comment.score,
            created_utc=comment.created_utc
        )

    def __eq__(self, other):
        if isinstance(other, Comment):
            return self.comment_id == other.comment_id
        return False

    def __hash__(self):
        return hash(self.comment_id)

    def check_mood(self):
        if self.mood is "unknown":
            mood = call_llm(self.content)
            self.mood = mood

        else:
            logger.info("The comment is already checked for its mood")


