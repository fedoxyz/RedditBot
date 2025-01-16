import time
from typing import List, Set
from threading import Thread
from comment import Comment

class RedditCommentMonitor:
    def __init__(self, reddit_api):
        self.reddit_api = reddit_api
        self.comments: List[Comment] = []
        self.comment_ids: Set[str] = set()
        self.is_monitoring = False
        self.monitor_thread = None

    def start_monitoring(self, post_url: str):
        """Start monitoring the post in a separate thread"""
        self.is_monitoring = True
        self.monitor_thread = Thread(target=self._monitor_comments, args=(post_url,))
        self.monitor_thread.daemon = True  # Thread will stop when main program stops
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()


    def _monitor_comments(self, post_url: str):
        while self.is_monitoring:
            try:
                submission = self.reddit_api.get_submission(post_url)
                submission.comments.replace_more(limit=None)
                all_comments = submission.comments.list()
                
                # Create fresh list of current comments
                new_comments = []
                new_comment_ids = set()
                
                for reddit_comment in all_comments:
                    comment = Comment.from_reddit_comment(reddit_comment)
                    new_comments.append(comment)
                    new_comment_ids.add(comment.comment_id)
                
                # Replace the old lists with new ones
                self.comments = new_comments
                self.comment_ids = new_comment_ids
                
                time.sleep(30)
                
            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(60)
                continue

    def get_comments(self) -> List[Comment]:
        """Get the current list of comments"""
        return self.comments

    def get_comment_by_id(self, comment_id: str) -> Comment | None:
        """Get a specific comment by its ID"""
        for comment in self.comments:
            if comment.comment_id == comment_id:
                return comment
        return None

    def get_comments_by_author(self, author: str) -> List[Comment]:
        """Get all comments by a specific author"""
        return [comment for comment in self.comments if comment.author == author]

    def get_comments_above_score(self, min_score: int) -> List[Comment]:
        """Get all comments with score above the specified threshold"""
        return [comment for comment in self.comments if comment.score >= min_score]
