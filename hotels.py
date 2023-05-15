import time
import base64
import logging
import functools
from pathlib import Path
from typing import Optional
from typing import Generator
from typing import Callable

import requests
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api._generated import Page
from playwright.sync_api._generated import BrowserType
from playwright.sync_api._generated import ElementHandle

from models import Hotel
from models import HotelFields
from database import database


logging.basicConfig(format="... %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


BROWSER_TIMEOUT = 45 * 1000
TRIP_ADVISOR_HOMEPAGE = "https://www.tripadvisor.com"


def retry_wraps(times: int = 3) -> Callable:
    def retry(function) -> Callable:
        """tries to run a function after an unsuccessful attempt."""

        @functools.wraps(function)
        def inner(*args, **kwargs):
            for _ in range(times):
                try:
                    return function(*args, **kwargs)
                except Exception as err:
                    logger.error(err)

        return inner

    return retry


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


@retry_wraps()
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


@retry_wraps()
def get_image_base64_string(src: str) -> bytes:
    # convert jpeg image to base64 string we can upload to cloud database
    logger.info(f"Downloading {src}")
    response = requests.get(src, timeout=45, stream=True)
    if not response.ok:
        response.raise_for_status()
    logger.debug("Image Download Successful")
    logger.debug(f"Preparing a base64 string representation of {src}")
    return base64.b64encode(response.content)


def get_hotel_name(page: Page, hotel_dict: dict) -> None:
    h1_heading = page.query_selector("h1#HEADING")
    hotel_name = get_text_from_page_element(h1_heading)
    hotel_dict[hotel_fields.name] = hotel_name


def get_hotel_reviews(page: Page, hotel_dict: dict) -> None:
    anchor_reviews = page.query_selector("a[href='#REVIEWS']")
    hotel_number_of_reviews = get_text_from_page_element(anchor_reviews)
    hotel_dict[hotel_fields.reviews] = hotel_number_of_reviews


def get_hotel_location(page: Page, hotel_dict: dict) -> None:
    span_location = page.query_selector("span.map-pin-fill + span")
    hotel_address = get_text_from_page_element(span_location)
    hotel_dict[hotel_fields.location] = hotel_address


def get_hotel_website(page: Page, hotel_dict: dict) -> None:
    url_hotel = page.query_selector('div[data-blcontact*="URL_HOTEL"]')
    hotel_website = None
    if url_hotel:
        hotel_website = url_hotel.query_selector("a").get_attribute("href")
    hotel_dict[hotel_fields.website] = hotel_website


def get_hotel_phone(page: Page, hotel_dict: dict) -> None:
    url_number = page.query_selector('div[data-blcontact*="PHONE"]')
    hotel_phone = get_text_from_page_element(url_number)
    hotel_dict[hotel_fields.phone] = hotel_phone


def get_hotel_images(page: Page, hotel_dict: dict) -> None:
    """TO FIX: Invalid URL 'None': No scheme supplied. Perhaps you meant http://None?"""
    images = list()
    photo_viewer = page.query_selector('div[data-section-signature="photo_viewer"]')
    image_links = photo_viewer.query_selector_all("img")
    for image_link in image_links[:5]:
        src = image_link.get_attribute("src")
        byte_string = get_image_base64_string(src)
        if byte_string:
            images.append(byte_string)
    hotel_dict[hotel_fields.images] = images


def get_all_listings_from_page(page: Page) -> list[str | None]:
    listing_hrefs = list()
    listings = page.query_selector_all("[class*='listItem']")
    while listings:
        listing = listings.pop()
        listing_href = listing.query_selector("a").get_attribute("href")
        logger.debug(listing_href)
        listing_hrefs.append(listing_href)
    return listing_hrefs


def get_hotel_data(listing_hrefs: list, page: Page) -> None:
    while listing_hrefs:
        hotel_dict = dict()
        listing_uri = listing_hrefs.pop()
        goto_url(f"{TRIP_ADVISOR_HOMEPAGE}{listing_uri}", page, "domcontentloaded")

        get_hotel_name(page, hotel_dict)
        get_hotel_reviews(page, hotel_dict)
        get_hotel_location(page, hotel_dict)
        get_hotel_website(page, hotel_dict)
        get_hotel_phone(page, hotel_dict)
        get_hotel_images(page, hotel_dict)
        # TODO: remove the hardcoded document name; put it in the .env file, like the database name
        database[f"tetsing{place}"].insert_one(hotel_dict)


def fill_place_in_form(place: str, page: Page) -> None:
    goto_url(TRIP_ADVISOR_HOMEPAGE, page, "domcontentloaded")
    time.sleep(1.5)
    page.query_selector("footer").scroll_into_view_if_needed()
    time.sleep(2)

    form_role_search = page.query_selector("form[role='search']")
    search = form_role_search.query_selector("input[type='search']")
    search.fill(f"{place} hotels")
    time.sleep(5)

    typeahead_results = page.query_selector("div#typeahead_results")
    href = typeahead_results.query_selector("a").get_attribute("href")
    goto_url(f"{TRIP_ADVISOR_HOMEPAGE}{href}", page)

    hrefs = get_all_listings_from_page(page)
    get_hotel_data(hrefs, page)


def main() -> None:
    place = get_file_content("places.txt")[3]
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False, slow_mo=250)
    page = get_page_object(browser)
    fill_place_in_form(place, page)


hotel_fields = HotelFields()
main()
