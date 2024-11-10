"""Generate status page"""

from enum import Enum
from logging import Logger

from cachelib import BaseCache

from .changelog import (
    get_android_changelog,
    get_desktop_changelog,
    get_ios_changelog,
    get_latest_core,
)
from .constants import UNKNOWN
from .stores import (
    ANDROID_LINKS,
    DESKTOP_LINKS,
    IOS_LINKS,
    get_android_stores,
    get_desktop_stores,
    get_ios_stores,
)
from .web import session

DEBUG = "🐞"
STYLES = """
body {
    font-family: sans-serif;
    padding: 0.5em;
    text-align: center;
}

:target {
   background-color: #ffa;
}

hr {
    border: 0;
    height: 1px;
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));
}

a {
    color: inherit;
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
}

table th:last-of-type, table td:last-of-type {
    text-align: right;
}

table th,
table td {
    padding: 0.5em;
    text-align: right;
}

table tr {
    border-bottom: 1px solid #dddddd;
}

table tr:nth-of-type(even) {
    background-color: #f3f3f3;
}

table tr:nth-of-type(odd) {
    background-color: #ffffff;
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

.gray {
    color: #ffffff;
    text-shadow: 1px 1px 2px black;
    background-color: #9f9f9f;
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
        changelog = func(15)
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


def _get_latest_core(cache: BaseCache) -> str:
    cache_key = "core.latest"
    version = cache.get(cache_key)
    if not version:
        version = get_latest_core()
        if version != UNKNOWN:
            cache.set(cache_key, version)
    return version


def draw_changelog_table(
    header: str, versions: list[tuple[str, str]], latest_core: str
) -> str:
    table = f"<h2>{header}</h2>"
    table += f'<div class="{header.lower()}-bg">'
    table += "<table><tr><th>Release</th><th>Core</th></tr>"
    for index, (app, core) in enumerate(versions):
        if core == latest_core:
            cls = "green"
        elif index == 0:
            cls = "red"
        else:
            cls = "red" if core == UNKNOWN else "gray"
        table += f'<tr><td id="{header.lower()}-{app}">{app}</td><td class="{cls}">{core}</td>'
    table += "</table></div>"
    return table


def get_color(version, latest):
    if version == latest:
        return "green"
    return "yellow" if DEBUG in latest else "red"


def get_status(cache: BaseCache, logger: Logger) -> str:  # noqa
    status = '<!doctype html><html><body><head><meta charset="UTF-8"/>'
    status += '<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'

    status += f"<style>{STYLES}\n"
    plt = [Platform.ANDROID, Platform.IOS, Platform.DESKTOP]
    for platform, emoji in zip(plt, ["🤖", "🍏", "🖥️"]):
        status += f"""
        .{platform.value}-bg {{
            width: 100%;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><text y="40" font-size="40" fill="rgba(255, 255, 0, 0.2)" transform="rotate(-45 25 25)">{emoji}</text></svg>');
            background-repeat: repeat;
            background-size: 60px 60px;
        }}
        """
    status += "</style></head>"

    android_changelog = []
    for app, core in _get_changelog(cache, Platform.ANDROID):
        app = app.replace("-", " ")
        if app.split()[-1].lower() == "testrun":
            app = f"{DEBUG}{app.split()[0]}"
        android_changelog.append((app, core))
    latest_android = android_changelog[0][0]

    android_stores = get_android_stores(cache, logger)
    android_github_release = ""
    for store, version in android_stores:
        if store == "GitHub Releases":
            android_github_release = version

    ios_changelog = []
    for app, core in _get_changelog(cache, Platform.IOS):
        app = app.replace("-", " ")
        if app.split()[-1].lower() == "testflight":
            app = f"{DEBUG}{app.split()[0]}"
        ios_changelog.append((app, core))
    latest_ios = ios_changelog[0][0]

    desktop_changelog = []
    for app, core in _get_changelog(cache, Platform.DESKTOP):
        if "." in app and int(app.split(".")[1]) % 2 != 0:
            app = f"{DEBUG}{app}"
        desktop_changelog.append((app, core))
    latest_desktop = desktop_changelog[0][0]

    status += "<h1>Delta Chat Releases</h1>"

    icon = "" if DEBUG in latest_android else "🚀"
    status += f"<h2>Android {icon}{latest_android}</h2>"
    status += '<div class="android-bg"><table><tr><th></th><th>Version</th></tr>'
    for store, version in android_stores:
        cls = get_color(version, latest_android)
        icon = ""
        if store == "F-Droid" and cls == "red":
            if android_github_release == latest_android:
                cls = "yellow"
                icon = "⏳"
        store = f'<a href="{ANDROID_LINKS[store]}">{store}</a>'
        if version in [data[0] for data in android_changelog]:
            version = f'<a href="#android-{version}">{version}</a>'
        status += f'<tr><td>{store}</td><td class="{cls}">{icon}{version}</td>'
    status += "</table></div>"

    icon = "" if DEBUG in latest_ios else "🚀"
    status += f"<h2>iOS {icon}{latest_ios}</h2>"
    status += '<div class="ios-bg"><table><tr><th></th><th>Version</th></tr>'
    for store, version in get_ios_stores(cache, logger):
        cls = get_color(version, latest_ios)
        store = f'<a href="{IOS_LINKS[store]}">{store}</a>'
        if version in [data[0] for data in ios_changelog]:
            version = f'<a href="#ios-{version}">{version}</a>'
        status += f'<tr><td>{store}</td><td class="{cls}">{version}</td>'
    status += "</table></div>"

    latest_desk_ver = _get_changelog(cache, Platform.DESKTOP)[0][0]
    url = (
        "https://github.com/deltachat/deltachat-desktop/issues"
        f"?q=is%3Aissue+release+progress+{latest_desk_ver}"
    )
    icon = "" if DEBUG in latest_desktop else "🚀"
    status += f'<h2>Desktop {icon}<a href="{url}">{latest_desktop}</a></h2>'
    status += '<div class="desktop-bg"><table><tr><th></th><th>Version</th></tr>'
    for store, version in get_desktop_stores(cache, logger):
        cls = get_color(version, latest_desktop)
        store = f'<a href="{DESKTOP_LINKS[store]}">{store}</a>'
        if version in [data[0] for data in desktop_changelog]:
            version = f'<a href="#desktop-{version}">{version}</a>'
        status += f'<tr><td>{store}</td><td class="{cls}">{version}</td>'
    status += "</table>"

    status += "<br/>" + _get_desktop_3rdparty(cache)
    status += "</div>"

    status += "<hr/><h1>🦀 Core Versions</h1>"

    latest_core = _get_latest_core(cache)
    status += "<table><tr><td>latest</td>"
    status += f'<td class="green">{latest_core}</td></tr></table>'

    status += draw_changelog_table("Android", android_changelog, latest_core)
    status += draw_changelog_table("iOS", ios_changelog, latest_core)
    status += draw_changelog_table("Desktop", desktop_changelog, latest_core)

    status += "</body></html>"

    return status
