from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, ElementClickInterceptedException

from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as  uc

from utils import parse_account, parse_cookies, get_options, wait, set_cookies, find_in_shadow

#from logger import logger


cookies, proxy, username, password = parse_account("user")

options = get_options()

driver = uc.Chrome(headless=False,use_subprocess=False, options=options)

set_cookies(driver, cookies)


reddit_login_l = "https://www.reddit.com/login/"
driver.get(reddit_login_l)


wait_10 = wait(driver, 10)


# USERNAME LOGIN 
username_input = wait_10.until(EC.visibility_of_element_located((By.ID, 'login-username')))
password_input = wait_10.until(EC.visibility_of_element_located((By.ID, 'login-password')))
username_input.send_keys(username)
password_input.send_keys(password)


# SHADOW BUTTON
driver.execute_script("""
    const overlay = document.querySelector('shreddit-overlay-display');
    const signupDrawer = overlay.shadowRoot.querySelector('shreddit-signup-drawer');
    const slotter = signupDrawer.shadowRoot.querySelector('shreddit-slotter');
    
    const button = slotter.shadowRoot.querySelector('button[rpl]');
    if (button) {
        button.click();
    }
""")
# -------------------------------------

# NORMAL BUTTON
login_button = wait_10.until(EC.visibility_of_element_located((By.TAG_NAME, 'button')))
login_button.click()

user = wait_10.until(EC.visibility_of_element_located((By.TAG_NAME, 'faceplate-dropdown-menu')))



# COMMENT REPLY
comment_l = ''

driver.switch_to.window(driver.window_handles[-1])
driver.get(comment_l)

#reply
comment = wait_10.until(EC.presence_of_element_located((
    By.CSS_SELECTOR, "shreddit-comment"
)))

# Find and click the Reply button within this comment
reply_button = comment.find_element(By.XPATH, 
    ".//button[.//span[contains(text(), 'Reply')]]"
)
reply_button.click()

# ---------------------------------

text = "a good day, sir"

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




upvote_button = find_in_shadow(driver, 'button[rpl][aria-pressed="false"]', comment)



from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT
from reddit_api import RedditAPI
from comments_monitor import RedditCommentMonitor

reddit_api = RedditAPI(CLIENT_ID, CLIENT_SECRET, USER_AGENT)

monitor = RedditCommentMonitor(reddit_api)

monitor.start_monitoring("")

monitor.get_comments()







def parse_account(username):
    file_path = f"../accounts/{username}.txt"
    with open(file_path, 'r') as f:
        # Read the first two lines of the file
        lines = [f.readline().strip() for _ in range(3)]
        # Assign the cookies and proxy
        cookies = lines[0]
        proxy = lines[1]
        username, password = lines[2].split(":")
    
    proxy_parts = proxy.strip().split(':')
    #ip, port, username, password = proxy_parts
#    proxy_formatted = f"{username}:{password}@{ip}:{port}"

    return parse_cookies(cookies), proxy_parts, username, password


def vote(reddit_name, post_id, vote_type, comment_id = None):
    if comment_id:
        link = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}/comment/{comment_id}/"
    else:
        link = f"https://www.reddit.com/r/{reddit_name}/comments/{post_id}/"
    
    driver.get(link)
    wait_10 = wait(driver, 10)

    if comment_id:
        comment = wait_10.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "shreddit-comment"
        )))
        button = find_in_shadow(driver, f'button[{vote_type}]', comment)
    else:
        button = find_in_shadow(driver, f'button[{vote_type}]')

    button.click()


