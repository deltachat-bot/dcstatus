"""Extraction of release versions and DC core versions from apps CHANGELOG"""

import re
from re import Pattern

from .constants import UNKNOWN
from .web import session

ORG_URL = "https://raw.githubusercontent.com/deltachat"


def fetch_changelog(
    url: str, app_regex: Pattern, core_regex: Pattern, count: int
) -> list[tuple[str, str]]:
    with session.get(url) as resp:
        lines = resp.text.splitlines()
    versions: list[tuple[str, str]] = []
    core = UNKNOWN
    for line in reversed(lines):
        line = line.strip()
        if match := app_regex.match(line):
            versions.insert(0, (match.group("app").strip(), core))
        if match := core_regex.match(line):
            core = match.group("core").strip()
    return versions[:count]


def get_android_changelog(count: int) -> list[tuple[str, str]]:
    url = f"{ORG_URL}/deltachat-android/refs/heads/main/CHANGELOG.md"
    app_regex = re.compile(r"## v(?P<app>\d+\.\d+\.\d+.*)")
    core_regex = re.compile(
        r"(\*|-) (using core|update to core|update core( to)?) ?(?P<core>.+)",
        re.IGNORECASE,
    )
    return fetch_changelog(url, app_regex, core_regex, count)


def get_ios_changelog(count: int) -> list[tuple[str, str]]:
    url = f"{ORG_URL}/deltachat-ios/refs/heads/main/CHANGELOG.md"
    app_regex = re.compile(r"## v(?P<app>\d+\.\d+\.\d+.*)")
    core_regex = re.compile(
        r"(\*|-) (update to core|update core( to)?|using core) ?(?P<core>.+)",
        re.IGNORECASE,
    )
    return fetch_changelog(url, app_regex, core_regex, count)


def get_desktop_changelog(count: int) -> list[tuple[str, str]]:
    url = f"{ORG_URL}/deltachat-desktop/refs/heads/main/CHANGELOG.md"
    app_regex = re.compile(r"## \[(?P<app>\d+\.\d+\.\d+)\].*")
    core_regex = re.compile(
        r"(\*|-) update `@deltachat/stdio-rpc-server`.* to `?(?P<core>.+)`",
        re.IGNORECASE,
    )
    return fetch_changelog(url, app_regex, core_regex, count)


def get_latest_core() -> str:
    url = f"{ORG_URL}/deltachat-core-rust/refs/heads/main/CHANGELOG.md"
    regex = re.compile(r"## \[(?P<version>\d+\.\d+\.\d+)\].*")
    with session.get(url) as resp:
        for line in resp.text.splitlines():
            line = line.strip()
            if match := regex.match(line):
                return match.group("version")
    return UNKNOWN
