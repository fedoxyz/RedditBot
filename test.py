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

from utils import parse_account, parse_cookies, get_options, wait

#from logger import logger


cookies, proxy = parse_account("Dear_Reindeer6751")
cookies = parse_cookies(cookies)

options = get_options()

driver = uc.Chrome(headless=False,use_subprocess=False, options=options)




reddit_login_l = "https://www.reddit.com/login/"

driver.get(reddit_login_l)

for cookie in cookies:
    print(f"{cookie["domain"]}")
    driver.add_cookie(cookie)


reddit = "https://www.reddit.com"

driver.get(reddit)

#driver.get(reddit_login_l)


wait_10 = wait(driver, 10)


# USERNAME LOGIN 
username = "xi8ted@gmail.com"
password = "0780fedoxer28"
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



# COMMENT REPLY
comment_l = 'https://www.reddit.com/r/castaneda/comments/1hyu5vm/comment/m6kgus0/'

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


cookies, proxy = parse_account(username)
cookies = parse_cookies(cookies)


options = get_options(proxy)

for cookie in cookies:
    driver.add_cookie(cookie)

