"""Utilities for website fetching."""

import functools
import time

from playwright.sync_api import sync_playwright
from requests import Session

session = Session()
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0"
        )
    }
)
session.request = functools.partial(session.request, timeout=30)  # type: ignore


def get_html(url: str, sleep: float = 0) -> str:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        time.sleep(sleep)
        content = page.content()
        browser.close()
    return content
