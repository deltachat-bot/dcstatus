"""Data about App stores releases"""

import functools
import json
import re
from logging import Logger
from typing import Callable

from bs4 import BeautifulSoup
from cachelib import BaseCache

from .constants import UNKNOWN
from .microsoft import get_msstore_version
from .web import get_html, session

ANDROID_LINKS = {
    "Play Store": "https://play.google.com/store/apps/details?id=chat.delta",
    "F-Droid": "https://f-droid.org/packages/com.b44t.messenger/",
    "Huawei App Gallery": "https://url.cloud.huawei.com/pXnbdjuOhW?shareTo=qrcode",
    "Amazon": "https://www.amazon.com/dp/B0864PKVW3/",
    "get.delta.chat": "https://get.delta.chat",
    "GitHub Releases": "https://github.com/deltachat/deltachat-android/releases/latest",
}
IOS_LINKS = {"App Store": "https://apps.apple.com/us/app/delta-chat/id1459523234"}
DESKTOP_LINKS = {
    "Microsoft Store": "https://apps.microsoft.com/detail/9pjtxx7hn3pk",
    "Mac App Store": "https://apps.apple.com/us/app/delta-chat-desktop/id1462750497",
    "Flathub": "https://flathub.org/apps/chat.delta.desktop",
    "get.delta.chat": "https://get.delta.chat",
    "GitHub Releases": "https://github.com/deltachat/deltachat-desktop/releases/latest",
}


def _get_from_cache(
    cache: BaseCache, key: str, func: Callable, logger: Logger
) -> tuple[str, str]:
    store = cache.get(key)
    if not store:
        store = func(logger)
        if store[1] != UNKNOWN:
            cache.set(key, store)
    return store


def get_gplay(logger: Logger) -> tuple[str, str]:
    url = "https://play.google.com/store/apps/details?id=chat.delta"
    regex = r'\[\[\["(?P<version>\d+\.\d+\.\d+)"'
    version = UNKNOWN
    try:
        with session.get(url) as resp:
            if match := re.search(regex, resp.text):
                version = match.group("version")
    except Exception as ex:
        logger.exception(ex)
    return ("Play Store", version)


def get_fdroid(logger: Logger) -> tuple[str, str]:
    url = "https://f-droid.org/packages/com.b44t.messenger/"
    try:
        with session.get(url) as resp:
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as ex:
        logger.exception(ex)
        soup = BeautifulSoup("", "html.parser")
    tag = soup.find(attrs={"id": "latest"})
    if tag:
        tag = tag.find(attrs={"class": "package-version-header"})
    if tag:
        tag = tag.find("a")
    version = tag["name"] if tag else UNKNOWN
    return ("F-Droid", version)


def get_huawei(logger: Logger) -> tuple[str, str]:
    url = "https://url.cloud.huawei.com/pXnbdjuOhW?shareTo=qrcode"
    soup = BeautifulSoup(get_html(logger, url, 5), "html.parser")
    version = UNKNOWN
    for tag in soup(attrs={"class": "appSingleInfo"}):
        key = tag.find(attrs={"class": "info_key"}).get_text().strip().lower()
        if key == "version":
            version = tag.find(attrs={"class": "info_val"}).get_text().strip()
            break
    return ("Huawei App Gallery", version)


def get_amazon(logger: Logger, cache: BaseCache) -> tuple[str, str]:
    url = "https://www.amazon.com/dp/B0864PKVW3/"
    cache_key = "amazon.cookies"
    cookies = cache.get(cache_key) or [
        {
            "name": "csm-hit",
            "value": "tb:1B9QN1VKWF143KC8YWYQ+s-1B9QN1VKWF143KC8YWYQ|1731164139081&t:1731164139081&adb:adblk_no",
            "domain": "www.amazon.com",
        },
        {
            "name": "csm-sid",
            "value": "270-2168271-1720160",
            "domain": "www.amazon.com",
        },
        {
            "name": "i18n-prefs",
            "value": "USD",
            "domain": "www.amazon.com",
        },
        {
            "name": "session-id-time",
            "value": "2082787201l",
            "domain": "www.amazon.com",
        },
        {
            "name": "session-id",
            "value": "130-6737246-6226317",
            "domain": "www.amazon.com",
        },
        {
            "name": "session-token",
            "value": "KE1PVeb/FM6TXQ1Cc9P5DRCBOHUrT3pHL7VueXmdNDZu95Sf2Xebgwy5oz/Ob+VqM0iQ2h4QPXbSBMXS2PwR4yjJGWH5wOBSQmY+/GNagCQiWU2XGdpIQC/aHFvwFt0A3zCRiBHRfgVcOfpWgtnoopYdP0nGjWyL2oYmrEe86AGrmqkJAIPEqffWh+BV+MSORR8QzEx0dE8zXxv/tWq6pnr8W90Q4mnqMgTx2aR2VRKxEiXnSE+lloDKy8wi9HPT7ES5kOEWHBhYygbQixVIgIjh63wSHzRnW81MYaXDQGFDMo181zs5D1S7ExICtwB0SufTvEuD2HNii27YU3MuPSTKoU2T0Tut",
            "domain": "www.amazon.com",
        },
        {
            "name": "sp-cdn",
            "value": '"L5Z9:DE"',
            "domain": "www.amazon.com",
        },
        {
            "name": "ubid-main",
            "value": "134-6517992-6175450",
            "domain": "www.amazon.com",
        },
        {
            "name": "x-amz-captcha-1",
            "value": "1731168273651621",
            "domain": "www.amazon.com",
        },
        {
            "name": "x-amz-captcha-2",
            "value": "kUC588sDYrDgqjDcmOX7Bw==",
            "domain": "www.amazon.com",
        },
    ]
    html = get_html(logger, url)
    tries = 0
    while tries < 5 and "Delta Chat" not in html:
        html = get_html(logger, url, 3)
        tries += 1
    version = UNKNOWN
    if "Delta Chat" in html:
        cache.set(cache_key, cookies, timeout=0)
        soup = BeautifulSoup(html, "html.parser")
        details = soup.find(attrs={"id": "masTechnicalDetails-btf"})
        for tag in details("div") if details else []:
            key = tag.find("span").get_text().strip().lower()
            if key == "version:":
                version = tag("span")[1].get_text().strip()
                break
    return ("Amazon", version)


def get_dowloads_android(logger: Logger) -> tuple[str, str]:
    url = "https://delta.chat/en/download"
    try:
        with session.get(url) as resp:
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as ex:
        logger.exception(ex)
        soup = BeautifulSoup("", "html.parser")
    tag = soup.find(attrs={"id": "android"})
    if tag:
        tag = tag.find("details")
        if tag:
            tag = tag.find("a")
    version = tag["href"].split("-")[-1][:-4] if tag else UNKNOWN
    return ("get.delta.chat", version)


def get_github_android(logger: Logger) -> tuple[str, str]:
    url = "https://github.com/deltachat/deltachat-android/releases/latest"
    try:
        with session.get(url) as resp:
            version = resp.url.split("/")[-1].lstrip("v")
    except Exception as ex:
        logger.exception(ex)
        version = UNKNOWN
    else:
        if not re.match(r"\d+\.\d+\.\d+", version):
            version = UNKNOWN
    return ("GitHub Releases", version)


def get_ios_appstore(logger: Logger) -> tuple[str, str]:
    url = "https://apps.apple.com/us/app/delta-chat/id1459523234"
    try:
        with session.get(url) as resp:
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as ex:
        logger.exception(ex)
        soup = BeautifulSoup("", "html.parser")
    tag = soup.find(attrs={"class": "whats-new__latest__version"})
    version = tag.get_text().strip().split()[-1] if tag else UNKNOWN
    return ("App Store", version)


def get_microsoft(logger: Logger) -> tuple[str, str]:
    try:
        version = get_msstore_version("9pjtxx7hn3pk")
    except Exception as ex:
        logger.exception(ex)
        version = UNKNOWN
    return ("Microsoft Store", version)


def get_macos(logger: Logger) -> tuple[str, str]:
    url = "https://apps.apple.com/us/app/delta-chat-desktop/id1462750497"
    try:
        with session.get(url) as resp:
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as ex:
        logger.exception(ex)
        version = UNKNOWN
    else:
        tag = soup.find(attrs={"class": "whats-new__latest__version"})
        version = tag.get_text().strip().split()[-1] if tag else UNKNOWN
    return ("Mac App Store", version)


def get_flathub(logger: Logger) -> tuple[str, str]:
    url = "https://flathub.org/apps/chat.delta.desktop"
    try:
        with session.get(url) as resp:
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as ex:
        logger.exception(ex)
        soup = BeautifulSoup("", "html.parser")
    version = UNKNOWN
    for tag in soup("script", attrs={"type": "application/ld+json"}):
        ver = json.loads(tag.get_text().strip()).get("softwareVersion")
        if ver:
            version = ver.lstrip("v")
            break
    return ("Flathub", version)


def get_downloads_desktop(logger: Logger) -> tuple[str, str]:
    url = "https://delta.chat/en/download"
    try:
        with session.get(url) as resp:
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as ex:
        logger.exception(ex)
        version = UNKNOWN
    else:
        tag = soup.find(attrs={"id": "windows"})
        if tag:
            tag = tag.find("details")
        if tag:
            tag = tag.find("a")
        if match := re.search(r"/v(\d+\.\d+\.\d+)/", tag["href"] if tag else ""):
            version = match.group(1)
        else:
            version = UNKNOWN
    return ("get.delta.chat", version)


def get_github_desktop(logger: Logger) -> tuple[str, str]:
    url = "https://github.com/deltachat/deltachat-desktop/releases/latest"
    try:
        with session.get(url) as resp:
            version = resp.url.split("/")[-1].lstrip("v")
    except Exception as ex:
        logger.exception(ex)
        version = UNKNOWN
    else:
        if not re.match(r"\d+\.\d+\.\d+", version):
            version = UNKNOWN

    return ("GitHub Releases", version)


def get_android_stores(cache: BaseCache, logger: Logger) -> list[tuple[str, str]]:
    _get_amazon = functools.partial(get_amazon, cache=cache)
    return [
        _get_from_cache(cache, "android.gplay", get_gplay, logger),
        _get_from_cache(cache, "android.fdroid", get_fdroid, logger),
        _get_from_cache(cache, "android.huawei", get_huawei, logger),
        _get_from_cache(cache, "android.amazon", _get_amazon, logger),
        _get_from_cache(cache, "android.dowloads", get_dowloads_android, logger),
        _get_from_cache(cache, "android.github", get_github_android, logger),
    ]


def get_ios_stores(cache: BaseCache, logger: Logger) -> list[tuple[str, str]]:
    return [_get_from_cache(cache, "ios.store", get_ios_appstore, logger)]


def get_desktop_stores(cache: BaseCache, logger: Logger) -> list[tuple[str, str]]:
    return [
        _get_from_cache(cache, "desktop.microsoft", get_microsoft, logger),
        _get_from_cache(cache, "desktop.macos", get_macos, logger),
        _get_from_cache(cache, "desktop.flathub", get_flathub, logger),
        _get_from_cache(cache, "desktop.downloads", get_downloads_desktop, logger),
        _get_from_cache(cache, "desktop.github", get_github_desktop, logger),
    ]
