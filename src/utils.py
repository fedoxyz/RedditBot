from selenium.webdriver.support.wait import WebDriverWait
import json
from proxy import proxies
import os, zipfile
from pathlib import Path
import undetected_chromedriver as uc

def find_in_shadow(driver, selector, root_element=None):
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
    return findInShadowRoots(arguments[0], arguments[1] || document);
    """
    return driver.execute_script(script, selector, root_element)


def get_options(proxy=None):
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument("--window-size=1440,900")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    chrome_path = '/usr/bin/google-chrome-stable'
    options.binary_location = chrome_path

    if proxy:
        print("proxy is true")
        if len(proxy) > 2: # IF AUTH REQUIRED
            print("proxy length is more than 2")
            ip, port, username, password = proxy
            proxies_extension = proxies(username, password, ip, port)
            with zipfile.ZipFile(proxies_extension, 'r') as zip_ref:
                zip_ref.extractall("proxies_extension")
            current_dir = os.getcwd()  # Gets the current working directory
            extension_path = os.path.join(current_dir, "proxies_extension")
            print(extension_path)
            options.add_argument(f'--load-extension={extension_path}')
            #options.add_extension(proxies_extension)
        else:
            ip, port = proxy
            options.add_argument(f'--proxy-server=http://{ip}:{port}')
    else:
        pass

    return options

def wait(driver, time):
    return WebDriverWait(driver, time)

 

def parse_account(username):
    file_path = f"./accounts/{username}.txt"
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




def parse_cookies(cookies_str):
    if cookies_str == "null":
        return "null"
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

def set_cookies(driver, cookies):
    """
    Sets cookies efficiently with special handling for __Host- and __Secure- prefixed cookies.
    Groups cookies by domain and sets them with minimal navigation.
    
    Args:
        driver: Selenium WebDriver instance
        cookies: List of cookie dictionaries with 'domain' and other required fields
    """
    if cookies == "null":
        return
    def prepare_cookie(cookie):
        """Prepare cookie according to its prefix requirements"""
        cookie_copy = cookie.copy()
        
        if cookie['name'].startswith('__Host-'):
            # __Host- cookies must:
            cookie_copy['secure'] = True
            cookie_copy['path'] = '/'
            # Remove domain as it must be set for current host only
            if 'domain' in cookie_copy:
                del cookie_copy['domain']
                
        elif cookie['name'].startswith('__Secure-'):
            # __Secure- cookies must:
            cookie_copy['secure'] = True
            
        return cookie_copy

    # Group cookies by domain
    domain_cookies = {}
    for cookie in cookies:
        cookie_domain = cookie['domain']
        # Remove leading dot for root domains
        if cookie_domain.startswith('.'):
            cookie_domain = cookie_domain[1:]
            
        if cookie_domain not in domain_cookies:
            domain_cookies[cookie_domain] = []
        domain_cookies[cookie_domain].append(cookie)
    
    # Now set all cookies for each domain with a single navigation
    for domain, domain_cookies_list in domain_cookies.items():
        try:
            # Always use HTTPS for secure cookies
            url = f'https://{domain}'
            driver.get(url)
        except Exception as e:
            print(f"Failed to access {domain}: {str(e)}")
            continue
        
        # Set all cookies for this domain
        for cookie in domain_cookies_list:
            try:
                prepared_cookie = prepare_cookie(cookie)
                driver.add_cookie(prepared_cookie)
            except Exception as e:
                print(f"Failed to set cookie {cookie['name']} for {domain}: {str(e)}")
                # If failed, try without domain for __Host- cookies
                if cookie['name'].startswith('__Host-'):
                    try:
                        prepared_cookie = prepare_cookie(cookie)
                        # Force remove domain for __Host- cookies
                        if 'domain' in prepared_cookie:
                            del prepared_cookie['domain']
                        driver.add_cookie(prepared_cookie)
                        print(f"Successfully set {cookie['name']} after removing domain")
                    except Exception as e2:
                        print(f"Still failed to set {cookie['name']}: {str(e2)}")

def set_cookies_cdp(driver, cookies):
    # Enable network tracking
    driver.execute_cdp_cmd('Network.enable', {})
    
    for cookie in cookies:
        # Prepare cookie parameters
        cookie_params = {
            'name': cookie['name'],
            'value': cookie['value'],
            'path': cookie.get('path', '/'),
            'secure': cookie.get('secure', True)
        }
        
        # Handle domain
        domain = cookie['domain']
        if domain.startswith('.'):
            cookie_params['domain'] = domain
        else:
            cookie_params['domain'] = domain
            
        # Handle special cookie prefixes
        if cookie['name'].startswith('__Host-'):
            cookie_params['secure'] = True
            cookie_params['path'] = '/'
            # For __Host- cookies, we must not include the domain
            del cookie_params['domain']
            
        elif cookie['name'].startswith('__Secure-'):
            cookie_params['secure'] = True
            
        # Optional parameters
        if 'httpOnly' in cookie:
            cookie_params['httpOnly'] = cookie['httpOnly']
        if 'sameSite' in cookie:
            cookie_params['sameSite'] = cookie['sameSite']
        if 'expires' in cookie:
            cookie_params['expires'] = cookie['expires']
            
        try:
            driver.execute_cdp_cmd('Network.setCookie', cookie_params)
        except Exception as e:
            print(f"Failed to set cookie {cookie['name']}: {str(e)}")

def save_voting_history(comment_id: str, bot_username: str):
    """Save voting record to a file"""
    history_file = Path("voting_history.json")
    
    # Load existing history
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
    else:
        history = {}
    
    # Update history
    if comment_id not in history:
        history[comment_id] = []
    history[comment_id].append(bot_username)
    
    # Save updated history
    with open(history_file, 'w') as f:
        json.dump(history, f)

def has_bot_voted(comment_id: str, bot_username: str) -> bool:
    """Check if bot has already voted on this comment"""
    history_file = Path("voting_history.json")
    
    if not history_file.exists():
        return False
        
    with open(history_file, 'r') as f:
        history = json.load(f)
        return comment_id in history and bot_username in history[comment_id]
