#!/usr/bin/env python
from datetime import datetime
from dateutil.tz import tzlocal, UTC

import feedparser
import os

CHANNEL_URL = "https://www.youtube.com/feeds/videos.xml?channel_id="
PLAYLIST_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id="
CONFIG = os.environ.get("HOME") + "/.config/ulauncher/com.github.oxke.ulauncher-ytwl/"

# function 'function' takes int as argument and returns int


def get_last_fetched(local_tz=False):
    with open(CONFIG + "lastfetched_ytfp", "r+") as f:
        last_fetched = f.read()
    if local_tz:
        return datetime.fromisoformat(last_fetched).astimezone(tzlocal())
    else:
        return datetime.fromisoformat(last_fetched)


def write_last_fetched():
    with open(CONFIG + "lastfetched_ytfp", "w") as f:
        f.write(datetime.now(tz=UTC).isoformat())


def fetch_feed(url, channel, last_fetched):
    count = 0
    if url.startswith("PL"):
        feed = feedparser.parse(PLAYLIST_URL + url)
    elif url.startswith("UC"):
        feed = feedparser.parse(CHANNEL_URL + url)
    if feed.status != 200:
        print(f"ERROR: {feed.status}")
        return 1, 0
    for entry in feed.entries:
        date_published = datetime.fromisoformat(entry["published"])
        print(
            date_published.astimezone(tzlocal()).strftime("%b %d %H:%M"),
            end=" ",
        )
        if date_published > last_fetched:
            with open(CONFIG + "watchlist", "a") as f:
                f.write(entry["yt_videoid"] + "\n")
            print("NEW VIDEO!", end=" ")
            count += 1
        else:
            break
    print()
    return 0, count


def fetch():
    last_fetched = get_last_fetched()
    count = 0
    with open(CONFIG + "subscriptions") as f:
        urls = f.readlines()
    for i, url in enumerate(urls):
        print(f'Fetching {i+1:02}/{len(urls)}: {url.split(" | ")[1].strip()}', end=" ")
        ff = fetch_feed(*url.split(" | "), last_fetched)
        if ff[0]:
            break
        count += ff[1]
    else:
        write_last_fetched()
        print(
            f'{last_fetched.astimezone(tzlocal()).strftime("%Y-%m-%d %H:%M")} --> '
            + f'{datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
        )
    return count


if __name__ == "__main__":
    fetch()
