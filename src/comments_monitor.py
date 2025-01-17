import time
from typing import List, Set
from threading import Thread
from logger import logger
from groq_api import GroqAPI
from dataclasses import dataclass
from config import GROQ_API
from threading_utils import thread_safe, with_retry
import threading

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

    @with_retry(max_retries=3, delay=2.0)
    def check_sentiment(self):
        if self.sentiment == -1:
            result = self._groq_api.analyze_sentiment(self.content)
            self.sentiment = result
        else:
            logger.debug("The comment is already checked for its sentiment")
            return

class RedditCommentMonitor:
    def __init__(self, reddit_api):
        self.reddit_api = reddit_api
        self.comments: List[Comment] = []
        self.comment_ids: Set[str] = set()
        self.is_monitoring = False
        self.monitor_thread = None

    @thread_safe
    def start_monitoring(self, post_url: str):
        """Start monitoring the post in a separate thread"""
        self.post_url = post_url  # Store URL for potential restarts
        self.is_monitoring = True
        self.monitor_thread = Thread(target=self._monitor_comments, args=(post_url,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Monitoring of post has started")

    @thread_safe
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
            logger.info("Monitoring stopped")

    @with_retry(max_retries=3, delay=2.0)
    def _monitor_comments(self, post_url: str):
        while self.is_monitoring:
            try:
                submission = self.reddit_api.get_submission(post_url)
                submission.comments.replace_more(limit=None)
                all_comments = submission.comments.list()
                
                new_comments = []
                new_comment_ids = set()
                
                for reddit_comment in all_comments:
                    comment = Comment.from_reddit_comment(reddit_comment)
                    
                    # Check if this comment already exists in the previous comments list
                    existing_comment = next((
                        existing for existing in self.comments 
                        if existing.comment_id == comment.comment_id
                    ), None)
                    
                    if existing_comment:
                        # Preserve the existing sentiment if the comment was already analyzed
                        comment.sentiment = existing_comment.sentiment
                    
                    new_comments.append(comment)
                    new_comment_ids.add(comment.comment_id)
                
                with self._thread_lock():
                    self.comments = new_comments
                    self.comment_ids = new_comment_ids
                
                time.sleep(30)
            
            except Exception as e:
                logger.error(f"Monitoring error: {str(e)}")
                time.sleep(60)
                continue

    @thread_safe
    def get_comments(self) -> List[Comment]:
        """Get the current list of comments"""
        return self.comments.copy()  # Return a copy to prevent concurrent modification

    @thread_safe
    def get_comment_by_id(self, comment_id: str) -> Comment | None:
        """Get a specific comment by its ID"""
        for comment in self.comments:
            if comment.comment_id == comment_id:
                return comment
        return None

    @thread_safe
    def get_comments_by_author(self, author: str) -> List[Comment]:
        """Get all comments by a specific author"""
        return [comment for comment in self.comments if comment.author == author]

    @thread_safe
    def get_comments_above_score(self, min_score: int) -> List[Comment]:
        """Get all comments with score above the specified threshold"""
        return [comment for comment in self.comments if comment.score >= min_score]

    def _thread_lock(self):
        """Context manager for thread-safe operations"""
        if not hasattr(self, '_lock'):
            self._lock = threading.Lock()
        return self._lock
