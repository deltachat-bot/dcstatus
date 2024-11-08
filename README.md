# dcstatus

[![Latest Release](https://img.shields.io/pypi/v/dcstatus.svg)](https://pypi.org/project/dcstatus)
[![CI](https://github.com/deltachat-bot/dcstatus/actions/workflows/python-ci.yml/badge.svg)](https://github.com/deltachat-bot/dcstatus/actions/workflows/python-ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Bot to get Delta Chat releases status information.

## Install

```sh
pip install dcstatus
```

Then, to setup [Playwright](https://playwright.dev/python/docs/intro), run:

```sh
playwright install
```

## Usage

Configure the bot:

```sh
dcstatus init bot@example.com PASSWORD
```

Start the bot:

```sh
dcstatus serve
```

Run `dcstatus --help` to see all available options.
