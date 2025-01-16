import praw

class RedditAPI:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    
    def get_submission(self, post_url: str):
        """Get a submission object from URL"""
        return self.reddit.submission(url=post_url)
    
    def get_reddit_instance(self):
        """Get the PRAW Reddit instance"""
        return self.reddit






