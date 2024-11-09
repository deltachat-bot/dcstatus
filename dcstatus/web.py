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
            "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5666.197 Safari/537.36"
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
            context = browser.new_context(user_agent=session.headers["User-Agent"])
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
            context.close()
        browser.close()
    return content


def post(
    logger: Logger,
    base_url: str,
    url: str,
    form: Optional[dict] = None,
    json: Optional[dict] = None,
    headers: Optional[dict] = None,
    cookies: Optional[list[dict]] = None,
) -> str:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            base_url=base_url, user_agent=session.headers["User-Agent"]
        )
        if cookies is not None:
            context.add_cookies(cookies)
        page = context.new_page()
        try:
            page.goto(base_url)
            time.sleep(3)
            response = page.request.post(
                url, headers=headers, form=form, data=json
            ).body()
        except Exception as ex:
            logger.exception(ex)
            response = ""

        if cookies is not None:
            cookies.clear()
            cookies.extend(context.cookies())
        context.close()
        browser.close()
    return response
