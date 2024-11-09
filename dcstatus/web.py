"""Utilities for website fetching."""

import functools
import time
from logging import Logger
from typing import Optional

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


def get_html(
    logger: Logger, url: str, sleep: float = 0, cookies: Optional[list[dict]] = None
) -> str:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        if cookies is not None:
            context = browser.new_context()
            context.add_cookies(cookies)
        else:
            context = None
        page = (context or browser).new_page()
        try:
            page.goto(url)
        except Exception as ex:
            logger.exception(ex)
            content = ""
        else:
            time.sleep(sleep)
            content = page.content()
        if context and cookies is not None:
            cookies.clear()
            cookies.extend(context.cookies())
            browser.close()
        browser.close()
    return content
