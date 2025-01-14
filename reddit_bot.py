from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as  uc

from utils import parse_account, wait, find_in_shadow, get_options, parse_cookies 

from logger import logger


class RedditBot:
    def __init__(self, username):
        self.username = username
        self.password = "123"
        self.cookies, self.proxy = parse_account(username)
        self.cookies = parse_cookies(self.cookies)
        

        options = get_options(self.proxy)
        self.driver = uc.Chrome(headless=False,use_subprocess=False, options=options)

        for cookie in self.cookies:
            self.driver.add_cookie(cookie)
    
    def login_cookies(self):
        reddit_login_l = "https://www.reddit.com/login/"

    def login_password(self):
        reddit_login_l = "https://www.reddit.com/login/"

        self.driver.get(reddit_login_l)
        
        wait_10 = wait(self.driver, 10)

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

        finally:
            return
       
    def comment(self, reddit_name, post_id, text, is_reply = False, comment_id = None):
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
            
            # Find and click the Reply button within this comment
            reply_button = comment.find_element(By.XPATH, 
                ".//button[.//span[contains(text(), 'Reply')]]"
            )
            reply_button.click()
            
            # Wait for and find the contenteditable div that appears after clicking reply
            editor = wait_10.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "div[data-lexical-editor='true']"
            )))
            editor.click()
            editor.send_keys(text)
            
            # Find and click the Comment submit button
            submit_button = comment.find_element(By.XPATH,
                ".//button[@slot='submit-button'][.//span[contains(text(), 'Comment')]]"
            )
            submit_button.click()

        else: 
             editor = wait_10.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-lexical-editor='true']")))
             editor.click()
             editor.send_keys(text) 
             submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[slot='submit-button']")
             submit_button.click()

    def create_post(self, reddit_name, title, body):
        create_post_url = f"https://www.reddit.com/r/{reddit_name}/submit/?type=TEXT"
        wait_10 = wait(self.driver, 10)
        
        # Switch to last tab and navigate to URL
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(create_post_url)
        
        # Find and fill title input
        title_input = wait_10.until(EC.visibility_of_element_located((
            By.XPATH, "//textarea[@name='title']"
        )))
        title_input.send_keys(title)
        
        # Click the "Switch to Rich Text Editor" button
        rich_text_button = wait_10.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(., 'Switch to Rich Text Editor')]"
        )))
        rich_text_button.click()
        
        # Find and fill body input
        body_input = wait_10.until(EC.visibility_of_element_located((
            By.XPATH, "//textarea[@placeholder='Body']"
        )))
        body_input.send_keys(body)
        
        # Click the Post button
        post_button = wait_10.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@id='inner-post-submit-button']"
        )))
        post_button.click()

    



