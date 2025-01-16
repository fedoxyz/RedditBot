from reddit_bot import RedditBot
from comments_monitor import RedditCommentMonitor
from reddit_api import RedditAPI

from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT

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

bots = setup_bots()

reddit_api = RedditAPI(CLIENT_ID, CLIENT_SECRET, USER_AGENT)

monitor = RedditCommentMonitor(reddit_api)

monitor.start_monitoring("https://www.reddit.com/r/DragonsDogma2/comments/1i2bz7s/me_and_da_bois_waiting_for_meat_to_finish_cooking/")
