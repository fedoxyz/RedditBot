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

#from logger import logger

options = Options()
options.add_argument('--start-maximized')
options.add_argument("--window-size=1440,900")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

chrome_path = '/usr/bin/google-chrome-stable'

options.binary_location = chrome_path

driver = uc.Chrome(headless=False,use_subprocess=False, options=options)

reddit_login_l = "https://www.reddit.com/login/"

driver.get(reddit_login_l)

username = "username"
password = "password"

wait_10 = WebDriverWait(driver, 10)

username_input = wait_10.until(EC.visibility_of_element_located((By.ID, 'login-username')))
password_input = wait_10.until(EC.visibility_of_element_located((By.ID, 'login-password')))

username_input.send_keys(username)
password_input.send_keys(password)

#driver.execute_script("""
#    const overlay = document.querySelector('shreddit-overlay-display');
#    const signupDrawer = overlay.shadowRoot.querySelector('shreddit-signup-drawer');
#    const slotter = signupDrawer.shadowRoot.querySelector('shreddit-slotter');
#    
#    const button = slotter.shadowRoot.querySelector('button[rpl]');
#    if (button) {
#        button.click();
#    }
#""")

login_button = wait_10.until(EC.visibility_of_element_located((By.TAG_NAME, 'button')))
login_button.click()


