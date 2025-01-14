from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
import json
from proxy import proxies

def find_in_shadow(driver, selector):
    script = """
    function findInShadowRoots(selector, root = document) {
        // First try regular DOM
        let element = root.querySelector(selector);
        if (element) return element;
        
        // If not found, recursively search through shadow roots
        const elements = root.querySelectorAll('*');
        for (const elem of elements) {
            if (elem.shadowRoot) {
                element = findInShadowRoots(selector, elem.shadowRoot);
                if (element) return element;
            }
        }
        return null;
    }
    return findInShadowRoots(arguments[0]);
    """
    return driver.execute_script(script, selector)

def get_options(proxy=None):
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument("--window-size=1440,900")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    chrome_path = '/usr/bin/google-chrome-stable'
    options.binary_location = chrome_path

    if proxy:
        print("proxy is true")
        if len(proxy) > 2:
            print("proxy length is more than 2")
            ip, port, username, password = proxy
            proxies_extension = proxies(username, password, ip, port)
            options.add_extension(proxies_extension)
    else:
        pass

    return options

def wait(driver, time):
    return WebDriverWait(driver, time)

 

def parse_account(username):
    file_path = f"./accounts/{username}.txt"
    with open(file_path, 'r') as f:
        # Read the first two lines of the file
        lines = [f.readline().strip() for _ in range(2)]
        
        # Assign the cookies and proxy
        cookies = lines[0]
        proxy = lines[1]
    
    proxy_parts = proxy.strip().split(':')
    #ip, port, username, password = proxy_parts
#    proxy_formatted = f"{username}:{password}@{ip}:{port}"

    return cookies, proxy_parts




def parse_cookies(cookies_str):
    print(type(cookies_str))
    print(f"cookie - {cookies_str}")
    if isinstance(cookies_str, str):
        cookies = json.loads(cookies_str)
    else:
        cookies = cookies_str

    selenium_cookies = []
    
    for cookie in cookies:
        selenium_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie.get('path', '/'),
            'secure': cookie.get('secure', False),
            'httpOnly': cookie.get('httpOnly', False)
        }
        
        selenium_cookies.append(selenium_cookie)
    
    return selenium_cookies

