from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from pathlib import Path
# Add imports for alternative methods
import requests
from urllib3 import ProxyManager, PoolManager
import urllib3
import random
import time
from urllib.parse import urljoin, urlparse

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")
# Add environment variables for alternative proxy methods
AZURE_PROXY_URL = os.getenv("AZURE_PROXY_URL", None)
PROXY_USERNAME = os.getenv("PROXY_USERNAME", None)
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", None)

# ProxyScrape rotating proxy settings
PROXYSCRAPE_PROXY_LIST = os.getenv("PROXYSCRAPE_PROXY_LIST", "")
PROXYSCRAPE_SCHEME = os.getenv("PROXYSCRAPE_SCHEME", "http")
PROXYSCRAPE_HOST = os.getenv("PROXYSCRAPE_HOST", None)
PROXYSCRAPE_PORT = os.getenv("PROXYSCRAPE_PORT", None)
PROXYSCRAPE_USERNAME = os.getenv("PROXYSCRAPE_USERNAME", None)
PROXYSCRAPE_PASSWORD = os.getenv("PROXYSCRAPE_PASSWORD", None)


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


PROXYSCRAPE_RETRIES = _safe_int(os.getenv("PROXYSCRAPE_RETRIES", "6"), 6)


def _mask_proxy_url(proxy_url):
    try:
        parsed = urlparse(proxy_url)
        if not parsed.hostname:
            return "invalid-proxy"
        port = f":{parsed.port}" if parsed.port else ""
        scheme = parsed.scheme or "http"
        return f"{scheme}://{parsed.hostname}{port}"
    except Exception:
        return "invalid-proxy"


def _normalize_proxy_url(proxy_url):
    raw = (proxy_url or "").strip()
    if not raw:
        return None

    if "://" not in raw:
        raw = f"{PROXYSCRAPE_SCHEME}://{raw}"

    parsed = urlparse(raw)
    if not parsed.hostname:
        return None

    username = parsed.username or PROXYSCRAPE_USERNAME
    password = parsed.password or PROXYSCRAPE_PASSWORD
    auth = f"{username}:{password}@" if username and password else ""
    port = f":{parsed.port}" if parsed.port else ""
    scheme = parsed.scheme or PROXYSCRAPE_SCHEME

    return f"{scheme}://{auth}{parsed.hostname}{port}"


def _build_single_proxyscrape_proxy():
    if not PROXYSCRAPE_HOST or not PROXYSCRAPE_PORT:
        return None

    auth = ""
    if PROXYSCRAPE_USERNAME and PROXYSCRAPE_PASSWORD:
        auth = f"{PROXYSCRAPE_USERNAME}:{PROXYSCRAPE_PASSWORD}@"

    return f"{PROXYSCRAPE_SCHEME}://{auth}{PROXYSCRAPE_HOST}:{PROXYSCRAPE_PORT}"


def _get_proxyscrape_proxy_pool():
    proxies = []

    if PROXYSCRAPE_PROXY_LIST:
        # Accept comma, semicolon, or newline separated proxy entries.
        normalized_list = (
            PROXYSCRAPE_PROXY_LIST.replace(";", "\n").replace(",", "\n").splitlines()
        )
        for item in normalized_list:
            proxy_url = _normalize_proxy_url(item)
            if proxy_url and proxy_url not in proxies:
                proxies.append(proxy_url)

    single_proxy = _build_single_proxyscrape_proxy()
    if single_proxy and single_proxy not in proxies:
        proxies.append(single_proxy)

    return proxies

def scrape_website(website):
    if not SBR_WEBDRIVER:
        print("SBR_WEBDRIVER is not configured.")
        return None

    print(f"SBR_WEBDRIVER: {SBR_WEBDRIVER}")
    print("Connecting to Scraping Browser...")
    try:
        sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
        with Remote(sbr_connection, options=ChromeOptions()) as driver:
            driver.get(website)
            print("Waiting captcha to solve...")
            solve_res = driver.execute(
                "executeCdpCommand",
                {
                    "cmd": "Captcha.waitForSolve",
                    "params": {"detectTimeout": 10000},
                },
            )
            print("Captcha solve status:", solve_res["value"]["status"])
            print("Navigated! Scraping page content...")
            html = driver.page_source
            return html
    except WebDriverException as exc:
        print(f"Selenium could not open {website}: {exc}")
        return None

# New alternative methods using different proxy approaches

def scrape_with_urllib3_proxy(website):
    """
    Use urllib3's ProxyManager to make requests through a proxy
    """
    print(f"Using proxy: {AZURE_PROXY_URL}")
    if not AZURE_PROXY_URL:
        print("No proxy URL configured. Using direct connection.")
        http = PoolManager()
    else:
        # Configure proxy with authentication if provided
        proxy_headers = {}
        if PROXY_USERNAME and PROXY_PASSWORD:
            auth = urllib3.util.request.make_headers(
                proxy_basic_auth=f"{PROXY_USERNAME}:{PROXY_PASSWORD}"
            )
            proxy_headers.update(auth)
        
        http = ProxyManager(AZURE_PROXY_URL, headers=proxy_headers)
    
    try:
        # Add random user agent to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml',
        }
        
        response = http.request('GET', website, headers=headers, timeout=30.0)
        return response.data.decode('utf-8')
    except Exception as e:
        print(f"Error fetching {website}: {str(e)}")
        return None

def scrape_with_requests(website, use_proxy=True):
    """
    Use requests library with proxy support
    """
    proxies = {}
    if use_proxy and AZURE_PROXY_URL:
        if PROXY_USERNAME and PROXY_PASSWORD:
            proxy_with_auth = AZURE_PROXY_URL.replace('http://', f'http://{PROXY_USERNAME}:{PROXY_PASSWORD}@')
            proxies = {
                "http": proxy_with_auth,
                "https": proxy_with_auth
            }
        else:
            proxies = {
                "http": AZURE_PROXY_URL,
                "https": AZURE_PROXY_URL
            }
    
    try:
        # Add random delay and user agent to avoid detection
        time.sleep(random.uniform(1, 3))
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml',
        }
        
        response = requests.get(
            website, 
            proxies=proxies, 
            headers=headers,
            timeout=30
        )
        return response.text
    except Exception as e:
        print(f"Error fetching {website}: {str(e)}")
        return None


def scrape_with_proxyscrape_pool(website, retries=None):
    """
    Use a rotating pool of ProxyScrape proxies with retry support.
    """
    proxy_pool = _get_proxyscrape_proxy_pool()
    if not proxy_pool:
        print(
            "ProxyScrape selected but no proxy pool is configured. "
            "Set PROXYSCRAPE_PROXY_LIST or PROXYSCRAPE_HOST/PORT."
        )
        return None

    attempt_count = max(1, retries if retries is not None else PROXYSCRAPE_RETRIES)
    last_error = None

    for attempt in range(1, attempt_count + 1):
        proxy_url = random.choice(proxy_pool)
        proxy_label = _mask_proxy_url(proxy_url)
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }

        try:
            time.sleep(random.uniform(0.5, 1.5))
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            ]
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml",
            }

            response = requests.get(
                website,
                proxies=proxies,
                headers=headers,
                timeout=45,
            )
            response.raise_for_status()
            print(f"ProxyScrape success on attempt {attempt} via {proxy_label}")
            return response.text
        except Exception as exc:
            last_error = exc
            print(
                f"ProxyScrape attempt {attempt}/{attempt_count} failed via "
                f"{proxy_label}: {exc}"
            )

    print(f"ProxyScrape failed for {website}: {last_error}")
    return None

def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Get text or further process the content
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content

def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
    ]


def _domain_tail(hostname):
    if not hostname:
        return ""
    parts = hostname.split(".")
    if len(parts) < 2:
        return hostname
    return ".".join(parts[-2:])


def extract_candidate_detail_links(html_content, base_url, protein_name, max_links=2):
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    base_host = urlparse(base_url).netloc
    base_tail = _domain_tail(base_host)
    protein_term = (protein_name or "").lower().strip()

    keywords = [
        "sequence",
        "entry",
        "protein",
        "record",
        "uniprot",
        "interpro",
        "structure",
        "gene",
        "details",
    ]

    scored = {}

    for anchor in soup.find_all("a", href=True):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue

        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)
        if parsed.scheme not in {"http", "https"}:
            continue

        target_host = parsed.netloc
        if base_tail and _domain_tail(target_host) != base_tail:
            continue

        text = anchor.get_text(" ", strip=True).lower()
        combined = f"{text} {absolute_url.lower()}"

        score = 0
        if protein_term and protein_term in combined:
            score += 6
        score += sum(2 for keyword in keywords if keyword in combined)

        if "search" in absolute_url.lower() or "query=" in absolute_url.lower():
            score -= 1

        if score <= 0:
            continue

        previous = scored.get(absolute_url, -1)
        if score > previous:
            scored[absolute_url] = score

    ranked_urls = sorted(scored.items(), key=lambda item: item[1], reverse=True)
    return [url for url, _ in ranked_urls[: max(1, max_links)]]
