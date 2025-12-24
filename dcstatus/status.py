"""Generate status page"""

from logging import Logger

from cachelib import BaseCache

from .changelog import Platform, get_latest_version
from .stores import (
    ANDROID_LINKS,
    DESKTOP_LINKS,
    IOS_LINKS,
    get_android_stores,
    get_desktop_stores,
    get_ios_stores,
)

STYLES = """
body {
    font-family: sans-serif;
    padding: 0.5em;
    text-align: center;
}

a {
    color: inherit;
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

table th:nth-of-type(odd) {
    text-align: left;
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

.row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.2em;
}
.cell {
    flex-grow: 1;
}
"""
PLATFORM_EMOJI = {
    Platform.ANDROID: "🤖",
    Platform.IOS: "🍏",
    Platform.DESKTOP: "🖥️",
    Platform.CORE: "🦀",
}


def get_color(version, latest):
    return "green" if version == latest else "red"


def get_status(cache: BaseCache, logger: Logger) -> str:  # noqa
    status = (
        '<!doctype html><html><head><meta charset="UTF-8"/>'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
        f"<style>{STYLES}</style></head><body>"
        "<h1>Delta Chat Releases</h1>"
    )

    latest_core = get_latest_version(cache, Platform.CORE)
    latest_desktop = get_latest_version(cache, Platform.DESKTOP)
    latest_ios = get_latest_version(cache, Platform.IOS)
    latest_android = get_latest_version(cache, Platform.ANDROID)

    android_stores = get_android_stores(cache, logger)
    android_github = ""
    for store, version in android_stores:
        if store == "GitHub":
            android_github = version

    status += '<div class="row">'

    icon = PLATFORM_EMOJI[Platform.ANDROID]
    status += f'<div class="cell"><h3>Android {latest_android}</h3>'
    status += f"<table><tr><th>{icon}</th><th>Version</th></tr>"
    for store, version in android_stores:
        cls = get_color(version, latest_android)
        icon = ""
        if store == "F-Droid" and cls == "red":
            if android_github == latest_android:
                cls = "yellow"
                icon = "⏳"
        store = f'<a href="{ANDROID_LINKS[store]}">{store}</a>'
        status += f'<tr><td>{store}</td><td class="{cls}">{icon}{version}</td>'
    status += "</table></div>"

    icon = PLATFORM_EMOJI[Platform.DESKTOP]
    status += f'<div class="cell"><h3>Desktop {latest_desktop}</h3>'
    status += f"<table><tr><th>{icon}</th><th>Version</th></tr>"
    for store, version in get_desktop_stores(cache, logger):
        cls = get_color(version, latest_desktop)
        store = f'<a href="{DESKTOP_LINKS[store]}">{store}</a>'
        status += f'<tr><td>{store}</td><td class="{cls}">{version}</td>'
    status += "</table></div>"

    status += "</div>"
    status += '<div class="row">'

    icon = PLATFORM_EMOJI[Platform.IOS]
    status += f'<div class="cell"><h3>iOS {latest_ios}</h3>'
    status += f"<table><tr><th>{icon}</th><th>Version</th></tr>"
    for store, version in get_ios_stores(cache, logger):
        cls = get_color(version, latest_ios)
        store = f'<a href="{IOS_LINKS[store]}">{store}</a>'
        status += f'<tr><td>{store}</td><td class="{cls}">{version}</td>'
    status += "</table></div>"

    icon = PLATFORM_EMOJI[Platform.CORE]
    status += '<div class="cell"><h3>Chatmail Core</h3>'
    status += f"<table><tr><th>{icon}</th><th>Version</th></tr>"
    status += "<tr><td>latest</td>"
    status += f'<td class="green">{latest_core}</td></tr>'
    status += "</table></div>"

    status += "</div>"
    status += "</body></html>"

    return status
