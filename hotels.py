import time
import base64
import logging
from pathlib import Path
from typing import Optional
from typing import Generator

import requests
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


def get_text_from_page_element(page_element: ElementHandle) -> str:
    response = ""
    if page_element:
        response = page_element.text_content().strip()
    return response


places = get_file_content("places.txt")
logger.info(f"Found {len(places)} places in file provided.")
# TODO: only open browser if we have places to work with

playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False, slow_mo=250)
page = get_page_object(browser)

goto_url(TRIP_ADVISOR_HOMEPAGE, page)

page.query_selector("footer").scroll_into_view_if_needed()

form_role_search = page.query_selector("form[role='search']")
search = form_role_search.query_selector("input[type='search']")
search.fill("ohio hotels")

time.sleep(2.5)
typeahead_results = page.query_selector("div#typeahead_results")
href = typeahead_results.query_selector("a").get_attribute("href")
goto_url(f"{TRIP_ADVISOR_HOMEPAGE}{href}", page)

listing_hrefs = list()
listings = page.query_selector_all("[class*='listItem']")
while listings:
    listing = listings.pop()
    listing_href = listing.query_selector("a").get_attribute("href")
    logger.debug(listing_href)
    listing_hrefs.append(listing_href)


listing_uri = listing_hrefs.pop()
goto_url(f"{TRIP_ADVISOR_HOMEPAGE}{listing_uri}", page, "networkidle")

h1_heading = page.query_selector("h1#HEADING")
hotel_name = get_text_from_page_element(h1_heading)

anchor_reviews = page.query_selector("a[href='#REVIEWS']")
hotel_number_of_reviews = get_text_from_page_element(anchor_reviews)

span_location = page.query_selector(
    "span.map-pin-fill + span"
)  # before uploading to cloud

hotel_address = get_text_from_page_element(span_location)

url_hotel = page.query_selector('div[data-blcontact*="URL_HOTEL"]')
hotel_website = url_hotel.query_selector("a").get_attribute("href")

url_number = page.query_selector('div[data-blcontact*="PHONE"]')
hotel_phone = get_text_from_page_element(url_number)

photo_viewer = page.query_selector('div[data-section-signature="photo_viewer"]')
images = photo_viewer.query_selector_all("img")

# src = images[0].get_attribute("src")


def get_image_base64_string(src: str) -> bytes:
    # convert jpeg image to base64 string we can upload to cloud database
    response = requests.get(src)
    if not response.ok:
        response.raise_for_status()
    return base64.b64encode(response.content)
