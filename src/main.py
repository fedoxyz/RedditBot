from reddit_bot import RedditBot
from comments_monitor import RedditCommentMonitor
from reddit_api import RedditAPI
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT
from logger import logger
from voting_system import setup_voting_system
import os
import sys
import time
from control_system import setup_control_system, run_control_system
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
        run_in_threads(bots, "login_password", synchronize=True)
        logger.info("Started parallel login for all bots")
    
    # Filter out any failed bots
    active_bots = [bot for bot in bots if hasattr(bot, 'driver')]
    logger.info(f"Successfully set up {len(active_bots)} bots")
    return active_bots

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
        
        control_system = setup_control_system(voting_system, monitor)
        control_thread = run_control_system(control_system)
        
        try:
            while True:
                process_comments(monitor, voting_system, reddit_name, post_id)
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            control_system.stop_all()
            
        finally:
            control_thread.join(timeout=1.0)
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
