from pathlib import Path
import json
import threading
from queue import Queue, Empty
from typing import List
import time
from logger import logger
from threading_utils import thread_safe, with_retry, run_in_threads
from dataclasses import dataclass

@dataclass
class VoteTask:
    comment_id: str
    post_id: str
    subreddit: str
    vote_type: str
    timestamp: float = time.time()

class VotingSystem:
    def __init__(self, reddit_api):
        self.reddit_api = reddit_api
        self.vote_queue = Queue()
        self.bots = []
        self.running = True
        self.history_file = Path("voting_history.json")
        self._load_history()
        self.vote_thread = None

    @thread_safe
    def _load_history(self):
        """Load voting history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except json.JSONDecodeError:
                logger.error("Corrupted voting history file. Creating new history.")
                self.history = {}
        else:
            self.history = {}

    @thread_safe
    def save_voting_history(self, comment_id: str, bot_username: str):
        """Save voting record to history"""
        if comment_id not in self.history:
            self.history[comment_id] = []
        self.history[comment_id].append(bot_username)
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            logger.error(f"Failed to save voting history: {str(e)}")

    @thread_safe
    def has_bot_voted(self, comment_id: str, bot_username: str) -> bool:
        """Check if bot has already voted on this comment"""
        return comment_id in self.history and bot_username in self.history[comment_id]

    def add_bot(self, bot):
        """Add a bot to the voting system"""
        self.bots.append(bot)
        logger.debug(f"Added bot {bot.username} to voting system")

    @with_retry(max_retries=3, delay=1.0)
    def process_vote(self, bot, task: VoteTask):
        """Process a vote task for a single bot"""
        try:
            # Skip if bot already voted
            if self.has_bot_voted(task.comment_id, bot.username):
                logger.debug(f"Bot {bot.username} already voted on {task.comment_id}")
                return

            # Execute vote
            bot.vote(
                task.subreddit,
                task.post_id,
                task.vote_type,
                task.comment_id
            )

            # Save voting record
            self.save_voting_history(task.comment_id, bot.username)
            logger.info(f"Bot {bot.username} voted {task.vote_type} on {task.comment_id}")

        except Exception as e:
            logger.error(f"Vote failed for {bot.username} on {task.comment_id}: {str(e)}")
            raise

    def _process_vote_queue(self):
        """Main worker loop processing votes"""
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.vote_queue.get(timeout=1)
                
                # Process votes in parallel using bound method
                bound_method = lambda bot: self.process_vote(bot, task)
                run_in_threads(self.bots, bound_method, synchronize=True)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in vote worker: {str(e)}")
                time.sleep(1)

    @thread_safe
    def start(self):
        """Start the voting system"""
        if not self.vote_thread or not self.vote_thread.is_alive():
            self.running = True
            self.vote_thread = threading.Thread(target=self._process_vote_queue)
            self.vote_thread.daemon = True
            self.vote_thread.start()
            logger.info("Voting system started")

    @thread_safe
    def stop(self):
        """Stop the voting system"""
        self.running = False
        if self.vote_thread and self.vote_thread.is_alive():
            self.vote_thread.join(timeout=1.0)
        logger.info("Voting system stopped")

    def add_vote_task(self, comment_id: str, post_id: str, subreddit: str, vote_type: str):
        """Add a new vote task to the queue"""
        task = VoteTask(
            comment_id=comment_id,
            post_id=post_id,
            subreddit=subreddit,
            vote_type=vote_type
        )
        self.vote_queue.put(task)
        logger.debug(f"Added vote task for comment {comment_id}")

def setup_voting_system(reddit_api):
    """Setup and start the voting system"""
    voting_system = VotingSystem(reddit_api)
    voting_system.start()
    return voting_system
