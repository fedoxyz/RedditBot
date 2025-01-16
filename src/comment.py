from groq_api import GroqAPI
from dataclasses import dataclass
from config import GROQ_API
from logger import logger

@dataclass
class Comment:
    _groq_api = GroqAPI(GROQ_API)

    def __init__(self, comment_id: str, content: str, author: str, score: int, created_utc: float):
        self.comment_id = comment_id
        self.content = content
        self.author = author
        self.score = score
        self.created_utc = created_utc
        self.sentiment = -1

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

    def check_sentiment(self):
        if self.sentiment == -1:
            result = self._groq_api.analyze_sentiment(self.content)
            self.sentiment = result

        else:
            logger.info("The comment is already checked for its sentiment")



