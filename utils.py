from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
import json
from proxy import proxies
import os, sys, zipfile
import undetected_chromedriver as uc

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
    options = uc.ChromeOptions()
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
            with zipfile.ZipFile(proxies_extension, 'r') as zip_ref:
                zip_ref.extractall("proxies_extension")
            current_dir = os.getcwd()  # Gets the current working directory
            extension_path = os.path.join(current_dir, "proxies_extension")
            print(extension_path)
            options.add_argument(f'--load-extension={extension_path}')
            #options.add_extension(proxies_extension)
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

