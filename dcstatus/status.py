"""Generate status page"""

from enum import Enum

from cachelib import BaseCache

from .changelog import get_android_changelog, get_desktop_changelog, get_ios_changelog
from .stores import UNKNOWN, get_android_stores, get_desktop_stores, get_ios_stores
from .web import session

STYLES = """
body {
    font-family: sans-serif;
    padding: 0.5em;
    text-align: center;
}

h2 {
    padding: 0.2em;
    color: #ffffff;
    text-shadow: 1px 1px 2px black;
    background-color: #364e59;
}

table {
    border-collapse: collapse;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    margin-left: auto;
    margin-right: auto;
}

table th {
    background-color: #364e59;
    color: #ffffff;
    text-align: left;
}

table th:last-of-type, table td:last-of-type {
    text-align: right;
}

table th,
table td {
    padding: 0.5em;
}

table tr {
    border-bottom: 1px solid #dddddd;
}

table tr:nth-of-type(even) {
    background-color: #f3f3f3;
}

table tr:last-of-type {
    border-bottom: 2px solid #364e59;
}

.red {
    color: #ffffff;
    text-shadow: 1px 1px 2px black;
    background-color: #e05d44;
}

.green {
    color: #ffffff;
    text-shadow: 1px 1px 2px black;
    background-color: #4c1;
}

.yellow {
    color: #ffffff;
    text-shadow: 1px 1px 2px black;
    background-color: #e6b135;
}

.blue {
    color: #ffffff;
    text-shadow: 1px 1px 2px black;
    background-color: #44bbe0;
}
"""


class Platform(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    DESKTOP = "desktop"


def _get_changelog(cache: BaseCache, platform: Platform) -> list[tuple[str, str]]:
    cache_key = f"{platform.value}.changelog"
    changelog = cache.get(cache_key)
    if not changelog:
        if platform == "android":
            func = get_android_changelog
        elif platform == "ios":
            func = get_ios_changelog
        else:
            func = get_desktop_changelog
        changelog = func(10)
        cache.set(cache_key, changelog)
    return changelog


def _get_desktop_3rdparty(cache: BaseCache) -> str:
    cache_key = "desktop.3rd-party"
    packages = cache.get(cache_key)
    if not packages:
        url = "https://repology.org/badge/vertical-allrepos/deltachat-desktop.svg"
        with session.get(url) as resp:
            packages = resp.text
        cache.set(cache_key, packages)
    return packages


def get_status(cache: BaseCache) -> str:  # noqa
    status = '<!doctype html><html><body><head><meta charset="UTF-8"/>'
    status += '<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
    status += f"<style>{STYLES}</style></head>"

    android_changelog = _get_changelog(cache, Platform.ANDROID)
    latest_android = android_changelog[0][0]
    android_stores = get_android_stores(cache)
    android_github_release = ""
    for store, version in android_stores:
        if store == "GitHub Releases":
            android_github_release = version

    ios_changelog = _get_changelog(cache, Platform.IOS)
    latest_ios = ios_changelog[0][0]

    desktop_changelog = _get_changelog(cache, Platform.DESKTOP)
    latest_desktop = desktop_changelog[0][0]

    status += "<h1>App Stores Releases</h1>"

    status += f"<h2>Android (🎯{latest_android})</h2>"
    status += "<table><tr><th>Store</th><th>Version</th></tr>"
    for store, version in android_stores:
        cls = "green" if version == latest_android else "red"
        if store == "F-Droid" and cls == "red":
            if android_github_release == latest_android:
                cls = "yellow"
        status += f'<tr><td>{store}</td><td class="{cls}">{version}</td>'
    status += "</table>"

    status += f"<h2>iOS (🎯{latest_ios})</h2>"
    status += "<table><tr><th>Store</th><th>Version</th></tr>"
    for store, version in get_ios_stores(cache):
        cls = "green" if version == latest_ios else "red"
        status += f'<tr><td>{store}</td><td class="{cls}">{version}</td>'
    status += "</table>"

    status += f"<h2>Desktop (🎯{latest_desktop})</h2>"
    status += "<table><tr><th>Store</th><th>Version</th></tr>"
    for store, version in get_desktop_stores(cache):
        cls = "green" if version == latest_desktop else "red"
        status += f'<tr><td>{store}</td><td class="{cls}">{version}</td>'
    status += "</table>"

    status += "<h3>3rd Party Packages</h3>"
    status += _get_desktop_3rdparty(cache)

    status += "<h1>Core Versions</h1>"

    status += "<h2>Android</h2>"
    status += "<table><tr><th>Release</th><th>Core</th></tr>"
    for app, core in android_changelog:
        cls = "red" if core == UNKNOWN else "blue"
        status += f'<tr><td>{app}</td><td class="{cls}">{core}</td>'
    status += "</table>"

    status += "<h2>iOS</h2>"
    status += "<table><tr><th>Release</th><th>Core</th></tr>"
    for app, core in ios_changelog:
        cls = "red" if core == UNKNOWN else "blue"
        status += f'<tr><td>{app}</td><td class="{cls}">{core}</td>'
    status += "</table>"

    status += "<h2>Desktop</h2>"
    status += "<table><tr><th>Release</th><th>Core</th></tr>"
    for app, core in desktop_changelog:
        cls = "red" if core == UNKNOWN else "blue"
        status += f'<tr><td>{app}</td><td class="{cls}">{core}</td>'
    status += "</table>"

    status += "</body></html>"

    return status
