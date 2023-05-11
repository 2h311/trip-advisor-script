import logging
from pathlib import Path
from typing import Optional
from typing import Generator

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api._generated import Page
from playwright.sync_api._generated import BrowserType
from playwright.sync_api._generated import ElementHandle


logging.basicConfig(format="... %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


BROWSER_TIMEOUT = 45 * 1000
TRIP_ADVISOR_HOMEPAGE = "https://www.tripadvisor.com"


def get_page_object(browser: BrowserType, proxies_pool: Optional[Generator] = None):
    if proxies_pool:
        proxy = next(proxies_pool)
        proxy_dict = {
            "server": f"http://{proxy.get('host').strip()}:{proxy.get('port').strip()}"
        }

        if len(proxy) == 4:
            proxy_dict["username"] = proxy.get("username").strip()
            proxy_dict["password"] = proxy.get("password").strip()
        context = browser.new_context(proxy=proxy_dict)
    else:
        context = browser.new_context()

    page = context.new_page()
    page.set_default_timeout(BROWSER_TIMEOUT)
    page.set_default_navigation_timeout(BROWSER_TIMEOUT)
    return page


# @retry_wraps()
def goto_url(url: str, page: Page, page_load_state: str = "load") -> None:
    logger.info(f"Visiting the url -> {url}")
    page.wait_for_load_state(page_load_state)
    response = page.goto(url)
    if response.ok:
        logger.debug("Page Done Loading...")


def get_file_content(filename: str):
    # check if file exists
    if not Path(filename).exists():
        # prompt for a filename if the filename given cant be foun
        filename = Path(input("\aEnter a valid filename: "))
        # if user inputs a non existing filename, raise an exception
        if not Path(filename).exists():
            raise Exception("\aYou might have to check the file name.")

    with open(filename, "r") as fp:
        content = [text.strip() for text in fp]
    return content


places = get_file_content("places.txt")
logger.info(f"Found {len(places)} places in file provided.")
# TODO: only open browser if we have places to work with

playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False, slow_mo=250)
page = get_page_object(browser)

goto_url(TRIP_ADVISOR_HOMEPAGE, page)
form_role_search = page.query_selector("form[role='search']")
form_role_search.
# form_role_search.query_selector("input[type='search']").type("hello")
