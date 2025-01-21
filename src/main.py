from reddit_bot import RedditBot
from comments_monitor import RedditCommentMonitor
from reddit_api import RedditAPI
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT
from logger import logger
from voting_system import setup_voting_system
import os
import sys
import time
from threading_utils import run_in_threads


def setup_bots():
    """Setup bot instances from account files"""
    accounts_dir = "accounts"
    bots = []
    
    # First create all bot instances and initialize browsers sequentially
    for filename in os.listdir(accounts_dir):
        if filename.endswith(".txt"):
            account_name = filename[:-4]
            try:
                bot = RedditBot(account_name)
                # Verify browser is ready by trying a simple operation
                try:
                    # Try to get a blank page first to verify browser works
                    bot.driver.get("about:blank")
                    time.sleep(1)  # Short wait after successful connection
                    bots.append(bot)
                    logger.info(f"Created and verified bot instance for {account_name}")
                except Exception as e:
                    logger.error(f"Browser verification failed for {account_name}: {str(e)}")
                    if hasattr(bot, 'driver'):
                        bot.driver.quit()
                    continue
                
            except Exception as e:
                logger.error(f"Failed to create bot {account_name}: {str(e)}")
                continue
                
    # Login all bots in parallel
    if bots:
        successful_bots = run_in_threads(bots, "login_password", synchronize=True)
        logger.info(f"Successfully logged in {len(successful_bots)} bots")
        return successful_bots
    
    return []

def get_target_info():
    """Get subreddit and post information from user"""
    logger.info("Enter target information:")
    
    while True:
        reddit_name = input("Enter subreddit name: ").strip()
        if reddit_name:
            break
        logger.error("Subreddit name cannot be empty")
    
    while True:
        post_id = input("Enter post ID: ").strip()
        if post_id:
            break
        logger.error("Post ID cannot be empty")
    
    return reddit_name, post_id

def process_comments(monitor, voting_system, reddit_name, post_id):
    """Process new comments and create voting tasks"""
    comments = monitor.get_comments()
    for comment in comments:
        if comment.sentiment == -1:
            comment.check_sentiment()
            vote_type = "downvote" if comment.sentiment == 0 else "upvote"
            
            voting_system.add_vote_task(
                comment.comment_id,
                post_id,
                reddit_name,
                vote_type
            )

def main():
    try:
        # Get target information
        reddit_name, post_id = get_target_info()
        
        # Setup APIs
        logger.info("Initializing APIs...")
        reddit_api = RedditAPI(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
        
        # Setup bots
        bots = setup_bots()
        if not bots:
            logger.error("No bots were loaded successfully. Exiting...")
            return 1
        
        # Setup and start monitor
        logger.info("Setting up monitoring...")
        monitor = RedditCommentMonitor(reddit_api)
        post_link = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}"
        monitor.start_monitoring(post_link)
        
        # Setup and start voting system
        logger.info("Initializing voting system...")
        voting_system = setup_voting_system(reddit_api)
        
        # Add bots to voting system
        for bot in bots:
            voting_system.add_bot(bot)
        
        
        try:
            while True:
                process_comments(monitor, voting_system, reddit_name, post_id)
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            
        finally:
            pass
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
