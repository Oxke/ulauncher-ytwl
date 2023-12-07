#!/usr/bin/env python
from datetime import datetime
import pytz
import feedparser
import os

CHANNEL_URL = "https://www.youtube.com/feeds/videos.xml?channel_id="
PLAYLIST_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id="
CONFIG = os.environ.get("HOME") + "/.config/ulauncher/com.github.oxke.ulauncher-ytwl/"

# function 'function' takes int as argument and returns int

def get_last_fetched(tz: str = None):
    with open(CONFIG + "lastfetched_ytfp", "r+") as f:
        last_fetched = f.read()
    if tz is None:
        return datetime.fromisoformat(last_fetched)
    else:
        return datetime.fromisoformat(last_fetched).astimezone(pytz.timezone(tz))


def write_last_fetched():
    with open(CONFIG + "lastfetched_ytfp", "w") as f:
        f.write(datetime.now(tz=pytz.UTC).isoformat())


def fetch_feed(url, channel, last_fetched):
    if url.startswith("PL"):
        feed = feedparser.parse(PLAYLIST_URL + url)
    elif url.startswith("UC"):
        feed = feedparser.parse(CHANNEL_URL + url)
    if feed.status != 200:
        print(f"ERROR: {feed.status}")
        return 1
    for entry in feed.entries:
        date_published = datetime.fromisoformat(entry["published"])
        print(
            date_published.astimezone(pytz.timezone("Europe/Paris")).strftime(
                "%b %d %H:%M"
            ),
            end=" ",
        )
        if date_published > last_fetched:
            with open(CONFIG + "watchlist", "a") as f:
                f.write(entry["yt_videoid"] + "\n")
            print("NEW VIDEO!", end=" ")
        else:
            break
    print()
    return 0


def fetch():
    last_fetched = get_last_fetched()
    with open(CONFIG + "subscriptions") as f:
        urls = f.readlines()
    for i, url in enumerate(urls):
        print(f'Fetching {i+1:02}/{len(urls)}: {url.split(" | ")[1].strip()}', end=" ")
        if fetch_feed(*url.split(" | "), last_fetched):
            break
    else:
        write_last_fetched()
        print(
            f'{last_fetched.astimezone(pytz.timezone("Europe/Paris")).strftime("%Y-%m-%d %H:%M")} --> '
            + f'{datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
        )

if __name__ == "__main__":
    fetch()
