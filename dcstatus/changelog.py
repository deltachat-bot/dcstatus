"""Extraction of release versions from CHANGELOG"""

import re
from enum import Enum

from cachelib import BaseCache

from .constants import UNKNOWN
from .web import session


class Platform(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    DESKTOP = "desktop"
    CORE = "core"


def get_latest_version(cache: BaseCache, platform: Platform) -> str:
    cache_key = f"{platform.value}.latest"
    version = cache.get(cache_key)
    if version:
        return version

    pre_url = "https://raw.githubusercontent.com/"
    suf_url = "refs/heads/main/CHANGELOG.md"
    if platform == Platform.ANDROID:
        url = f"{pre_url}/deltachat/deltachat-android/{suf_url}"
        regex = re.compile(r"## v(?P<version>\d+\.\d+\.\d+).*")
    elif platform == Platform.IOS:
        url = f"{pre_url}/deltachat/deltachat-ios/{suf_url}"
        regex = re.compile(r"## v(?P<version>\d+\.\d+\.\d+).*")
    elif platform == Platform.DESKTOP:
        url = f"{pre_url}/deltachat/deltachat-desktop/{suf_url}"
        regex = re.compile(r"## \[(?P<version>\d+\.\d+\.\d+)\].*")
    else:
        url = f"{pre_url}/chatmail/core/{suf_url}"
        regex = re.compile(r"## \[(?P<version>\d+\.\d+\.\d+)\].*")

    with session.get(url) as resp:
        for line in resp.text.splitlines():
            line = line.strip()
            if match := regex.match(line):
                version = match.group("version").strip()
                cache.set(cache_key, version)
                return version
    return UNKNOWN
