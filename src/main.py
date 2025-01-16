from reddit_bot import RedditBot
from comments_monitor import RedditCommentMonitor
from reddit_api import RedditAPI
from utils import save_voting_history, has_bot_voted
import time

from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT

from logger import logger

import os

def setup_bots():
    bots = []
    # Get all txt files from accounts folder
    accounts_dir = "accounts"
    for filename in os.listdir(accounts_dir):
        if filename.endswith(".txt"):
            # Remove .txt extension
            account_name = filename[:-4]
            # Create bot instance
            bot = RedditBot(account_name)
            bot.login_password()
            bots.append(bot)
    return bots

def main(reddit_name, post_id):
    bots = setup_bots()
    reddit_api = RedditAPI(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    monitor = RedditCommentMonitor(reddit_api)
    post_link = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}"
    monitor.start_monitoring(post_link)
    
    while True:
        comments = monitor.get_comments()
        for comment in comments:
            if comment.sentiment == -1:
                comment.check_sentiment()
                if comment.sentiment == 0:
                    vote_type = "downvote"
                else:
                    vote_type = "upvote"
                
                for bot in bots:
                    # Check if bot hasn't voted yet
                    if not has_bot_voted(comment.comment_id, bot.username):
                        bot.vote(reddit_name, post_id, vote_type, comment.comment_id)
                        save_voting_history(comment.comment_id, bot.username)
                        logger.info(f"Bot {bot.username} voted {vote_type} on comment {comment.comment_id}")

        time.sleep(30)
