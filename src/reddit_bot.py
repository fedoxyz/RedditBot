from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from utils import parse_account, set_cookies, wait, find_in_shadow, get_options 
from logger import logger
from threading_utils import thread_safe, with_retry
from queue import Empty
import os

class RedditBot:
    def __init__(self, username):
        self.cookies, self.proxy, self.username, self.password = parse_account(username)
        logger.info(f"{username} successfully parsed.")

        # Create unique Chrome directory for this instance
        chrome_data_dir = f"chrome_data/{username}"
        os.makedirs(chrome_data_dir, exist_ok=True)

        options = get_options(self.proxy)
        options.add_argument(f'--user-data-dir={chrome_data_dir}')
        
        # Use unique driver path for each instance
        driver_path = f"/tmp/chromedriver_{username}"
        
        self.driver = uc.Chrome(
            headless=False, 
            use_subprocess=False,
            options=options,
            driver_executable_path=driver_path,
            user_multi_procs=True  # Allow multiple processes
        )
        set_cookies(self.driver, self.cookies)


    @with_retry(max_retries=3, delay=1.0)
    def login_password(self):
        """Thread-safe login with retry mechanism"""
        reddit_login_l = "https://www.reddit.com/login/"

        self.driver.get(reddit_login_l)
        
        wait_10 = wait(self.driver, 10)
        
        try:
            wait_10.until(
            EC.presence_of_element_located(
                (By.XPATH, "//auth-flow-modal[@pagename='logged-in-redirect']")
            )
        )
            return
        except:
            pass

        username_input = wait_10.until(EC.visibility_of_element_located((By.ID, 'login-username')))
        password_input = wait_10.until(EC.visibility_of_element_located((By.ID, 'login-password')))
        
        username_input.send_keys(self.username)
        password_input.send_keys(self.password)

        try:
            login_button = wait_10.until(EC.visibility_of_element_located((By.TAG_NAME, 'button')))
            login_button.click()
            
        except Exception:
            self.driver.execute_script("""
                const overlay = document.querySelector('shreddit-overlay-display');
                const signupDrawer = overlay.shadowRoot.querySelector('shreddit-signup-drawer');
                const slotter = signupDrawer.shadowRoot.querySelector('shreddit-slotter');
                
                const button = slotter.shadowRoot.querySelector('button[rpl]');
                if (button) {
                    button.click();
               }
            """)
        
        # VERIFY THAT LOGGED IN
        wait_10.until(EC.visibility_of_element_located((By.TAG_NAME, 'faceplate-dropdown-menu')))

    @with_retry(max_retries=3, delay=1.0)
    def comment(self, reddit_name, post_id, text, is_reply=False, comment_id=None):
        """Thread-safe comment posting with retry mechanism"""
        if is_reply:
            comment_l = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}/comment/{comment_id}/"
        else:
            comment_l = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}/"

        wait_10 = wait(self.driver, 10)
         
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(comment_l)

        if is_reply:
            comment = wait_10.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "shreddit-comment"
            )))
            
            reply_button = comment.find_element(By.XPATH, 
                ".//button[.//span[contains(text(), 'Reply')]]"
            )
            reply_button.click()
            
            editor = wait_10.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "div[data-lexical-editor='true']"
            )))
            editor.click()
            editor.send_keys(text)
            
            submit_button = comment.find_element(By.XPATH,
                ".//button[@slot='submit-button'][.//span[contains(text(), 'Comment')]]"
            )
            submit_button.click()

        else: 
            editor = wait_10.until(EC.visibility_of_element_located((
                By.CSS_SELECTOR, "div[data-lexical-editor='true']"
            )))
            editor.click()
            editor.send_keys(text) 
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[slot='submit-button']")
            submit_button.click()

    @with_retry(max_retries=3, delay=1.0)
    def create_post(self, reddit_name, title, body):
        """Thread-safe post creation with retry mechanism"""
        create_post_url = f"https://www.reddit.com/r/{reddit_name}/submit/?type=TEXT"
        wait_10 = wait(self.driver, 10)
        
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(create_post_url)
        
        title_input = wait_10.until(EC.visibility_of_element_located((
            By.XPATH, "//textarea[@name='title']"
        )))
        title_input.send_keys(title)
        
        rich_text_button = wait_10.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(., 'Switch to Rich Text Editor')]"
        )))
        rich_text_button.click()
        
        body_input = wait_10.until(EC.visibility_of_element_located((
            By.XPATH, "//textarea[@placeholder='Body']"
        )))
        body_input.send_keys(body)
        
        post_button = wait_10.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@id='inner-post-submit-button']"
        )))
        post_button.click()

    @with_retry(max_retries=2, delay=1.0)
    def vote(self, reddit_name, post_id, vote_type, comment_id=None):
        """Thread-safe voting with retry mechanism"""
        if comment_id:
            link = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}/comment/{comment_id}/"
        else:
            link = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}/"
        
        logger.debug(f"Link for voting is {link}")
        self.driver.switch_to.window(self.driver.window_handles[-1])

        self.driver.get(link)
        wait_10 = wait(self.driver, 10)

        if comment_id:
            comment = wait_10.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "shreddit-comment"
            )))
            
            # If comment is hidden then return
            try:
                show_hidden = find_in_shadow(self.driver, f'button[rpl]', comment)
                if show_hidden:
                    return
            except:
                pass

            button = find_in_shadow(self.driver, f'button[{vote_type}]', comment)
        else:
            button = find_in_shadow(self.driver, f'button[{vote_type}]')

        button.click()

    def __del__(self):
        """Clean up resources when bot is destroyed"""
        try:
            # Remove driver from queue
            if hasattr(self, 'driver'):
                try:
                    driver_queue.get_nowait()  # Remove our driver from queue
                except Empty:
                    pass
                self.driver.quit()
        except:
            pass
