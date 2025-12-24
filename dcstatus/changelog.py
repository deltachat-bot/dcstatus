"""Extraction of release versions from CHANGELOG"""

import re
from cachelib import BaseCache
from enum import Enum

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

    PRE_URL = "https://raw.githubusercontent.com/"
    SUF_URL = "refs/heads/main/CHANGELOG.md"
    if platform == Platform.ANDROID:
        url = f"{PRE_URL}/deltachat/deltachat-android/{SUF_URL}"
        regex = re.compile(r"## v(?P<version>\d+\.\d+\.\d+).*")
    elif platform == Platform.IOS:
        url = f"{PRE_URL}/deltachat/deltachat-ios/{SUF_URL}"
        regex = re.compile(r"## v(?P<version>\d+\.\d+\.\d+).*")
    elif platform == Platform.DESKTOP:
        url = f"{PRE_URL}/deltachat/deltachat-desktop/{SUF_URL}"
        regex = re.compile(r"## \[(?P<version>\d+\.\d+\.\d+)\].*")
    else:
        url = f"{PRE_URL}/chatmail/core/{SUF_URL}"
        regex = re.compile(r"## \[(?P<version>\d+\.\d+\.\d+)\].*")

    with session.get(url) as resp:
        for line in resp.text.splitlines():
            line = line.strip()
            if match := regex.match(line):
                version = match.group("version").strip()
                cache.set(cache_key, version)
                return version
    return UNKNOWN
