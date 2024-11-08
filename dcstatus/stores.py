"""Data about App stores releases"""

import json
import re
import time
from typing import Callable

from bs4 import BeautifulSoup
from cachelib import BaseCache

from .constants import UNKNOWN
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
    "Microsoft Store": (
        "https://www.microsoft.com/en-us/p/deltachat/9pjtxx7hn3pk"
        "?activetab=pivot:overviewtab"
    ),
    "Mac App Store": "https://apps.apple.com/us/app/delta-chat-desktop/id1462750497",
    "Flathub": "https://flathub.org/apps/chat.delta.desktop",
    "get.delta.chat": "https://get.delta.chat",
    "GitHub Releases": "https://github.com/deltachat/deltachat-desktop/releases/latest",
}


def _get_from_cache(cache: BaseCache, key: str, func: Callable) -> tuple[str, str]:
    store = cache.get(key)
    if not store:
        store = func()
        if store[1] != UNKNOWN:
            cache.set(key, store)
    return store


def get_gplay() -> tuple[str, str]:
    url = "https://play.google.com/store/apps/details?id=chat.delta"
    with session.get(url) as resp:
        regex = r'\[\[\["(?P<version>\d+\.\d+\.\d+)"'
        match = re.search(regex, resp.text)
        version = match.group("version") if match else UNKNOWN
    return ("Play Store", version)


def get_fdroid() -> tuple[str, str]:
    url = "https://f-droid.org/packages/com.b44t.messenger/"
    with session.get(url) as resp:
        soup = BeautifulSoup(resp.text)
    tag = soup.find(attrs={"id": "latest"})
    if tag:
        tag = tag.find(attrs={"class": "package-version-header"})
    if tag:
        tag = tag.find("a")
    version = tag["name"] if tag else UNKNOWN
    return ("F-Droid", version)


def get_huawei() -> tuple[str, str]:
    url = "https://url.cloud.huawei.com/pXnbdjuOhW?shareTo=qrcode"
    soup = BeautifulSoup(get_html(url, 5))
    version = UNKNOWN
    for tag in soup(attrs={"class": "appSingleInfo"}):
        key = tag.find(attrs={"class": "info_key"}).get_text().strip().lower()
        if key == "version":
            version = tag.find(attrs={"class": "info_val"}).get_text().strip()
            break
    return ("Huawei App Gallery", version)


def get_amazon() -> tuple[str, str]:
    url = "https://www.amazon.com/dp/B0864PKVW3/"
    html = get_html(url)
    tries = 0
    while tries < 5 and "Delta Chat" not in html:
        time.sleep(3)
        html = get_html(url)
        tries += 1
    soup = BeautifulSoup(html)
    version = UNKNOWN
    for tag in soup.find(attrs={"id": "masTechnicalDetails-btf"})("div"):
        key = tag.find("span").get_text().strip().lower()
        if key == "version:":
            version = tag("span")[1].get_text().strip()
            break
    return ("Amazon", version)


def get_dowloads_android() -> tuple[str, str]:
    url = "https://delta.chat/en/download"
    with session.get(url) as resp:
        soup = BeautifulSoup(resp.text)
    tag = soup.find(attrs={"id": "android"}).find("details").find("a")
    version = tag["href"].split("-")[-1][:-4]
    return ("get.delta.chat", version)


def get_github_android() -> tuple[str, str]:
    url = "https://github.com/deltachat/deltachat-android/releases/latest"
    with session.get(url) as resp:
        version = resp.url.split("/")[-1].lstrip("v")
    return ("GitHub Releases", version)


def get_ios_appstore() -> tuple[str, str]:
    url = "https://apps.apple.com/us/app/delta-chat/id1459523234"
    with session.get(url) as resp:
        soup = BeautifulSoup(resp.text)
    tag = soup.find(attrs={"class": "whats-new__latest__version"})
    version = tag.get_text().strip().split()[-1] if tag else UNKNOWN
    return ("App Store", version)


def get_microsoft() -> tuple[str, str]:
    url = "https://www.microsoft.com/en-us/p/deltachat/9pjtxx7hn3pk?activetab=pivot:overviewtab"
    with session.get(url) as resp:
        soup = BeautifulSoup(resp.text)
    tag = soup.find(attrs={"telemetry-area-id": "WhatsNewVersion"})
    if tag:
        tag = tag.find(attrs={"class": "card__body"})
    if not tag:
        version = UNKNOWN
    else:
        version = tag.get_text().strip().lower()
        regex = r'version (?P<version>\d+\.\d+\.\d+)"'
        match = re.search(regex, version)
        version = match.group("version") if match else UNKNOWN

    return ("Microsoft Store", version)


def get_macos() -> tuple[str, str]:
    url = "https://apps.apple.com/us/app/delta-chat-desktop/id1462750497"
    with session.get(url) as resp:
        soup = BeautifulSoup(resp.text)
    tag = soup.find(attrs={"class": "whats-new__latest__version"})
    version = tag.get_text().strip().split()[-1] if tag else UNKNOWN
    return ("Mac App Store", version)


def get_flathub() -> tuple[str, str]:
    url = "https://flathub.org/apps/chat.delta.desktop"
    with session.get(url) as resp:
        soup = BeautifulSoup(resp.text)
    version = UNKNOWN
    for tag in soup("script", attrs={"type": "application/ld+json"}):
        ver = json.loads(tag.get_text().strip()).get("softwareVersion")
        if ver:
            version = ver.lstrip("v")
            break
    return ("Flathub", version)


def get_downloads_desktop() -> tuple[str, str]:
    url = "https://delta.chat/en/download"
    with session.get(url) as resp:
        soup = BeautifulSoup(resp.text)
    tag = soup.find(attrs={"id": "windows"}).find("details").find("a")
    if match := re.search(r"/v(\d+\.\d+\.\d+)/", tag["href"]):
        version = match.group(1)
    else:
        version = UNKNOWN
    return ("get.delta.chat", version)


def get_github_desktop() -> tuple[str, str]:
    url = "https://github.com/deltachat/deltachat-desktop/releases/latest"
    with session.get(url) as resp:
        version = resp.url.split("/")[-1].lstrip("v")
    return ("GitHub Releases", version)


def get_android_stores(cache: BaseCache) -> list[tuple[str, str]]:
    return [
        _get_from_cache(cache, "android.gplay", get_gplay),
        _get_from_cache(cache, "android.fdroid", get_fdroid),
        _get_from_cache(cache, "android.huawei", get_huawei),
        _get_from_cache(cache, "android.amazon", get_amazon),
        _get_from_cache(cache, "android.dowloads", get_dowloads_android),
        _get_from_cache(cache, "android.github", get_github_android),
    ]


def get_ios_stores(cache: BaseCache) -> list[tuple[str, str]]:
    return [_get_from_cache(cache, "ios.store", get_ios_appstore)]


def get_desktop_stores(cache: BaseCache) -> list[tuple[str, str]]:
    return [
        _get_from_cache(cache, "desktop.microsoft", get_microsoft),
        _get_from_cache(cache, "desktop.macos", get_macos),
        _get_from_cache(cache, "desktop.flathub", get_flathub),
        _get_from_cache(cache, "desktop.downloads", get_downloads_desktop),
        _get_from_cache(cache, "desktop.github", get_github_desktop),
    ]
