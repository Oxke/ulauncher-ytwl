import re
import os
import subprocess
import requests
from random import randint
from datetime import datetime
from isodate import parse_duration
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

CONFIG = os.environ.get("HOME") + "/.config/ulauncher/com.github.oxke.ytlw"
WATCHLIST = CONFIG + "/watchlist"
SUBSCRIPTIONS = CONFIG + "/subscriptions"
IMAGES = CONFIG + "/images"
yt_info = "https://www.googleapis.com/youtube/v3/videos"
pl_info = "https://www.googleapis.com/youtube/v3/playlists"
ch_info = "https://www.googleapis.com/youtube/v3/channels"
yt_search = "https://www.googleapis.com/youtube/v3/search"
yt_watch = "https://www.youtube.com/watch?v="


def WatchVideo(vid=None, stack=False, random=False):
    with open(WATCHLIST, "r+") as f:
        lines = f.readlines()
        if lines:
            if vid:
                url = yt_watch + vid
                lines = [line for line in lines if line[:-1] != vid]
            elif stack:
                url = yt_watch + lines.pop()
            elif random:
                url = yt_watch + lines.pop(randint(0, len(lines) - 1))
            else:
                url = yt_watch + lines.pop(0)
            f.seek(0)
            f.writelines(lines)
            f.truncate()
        else:
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    subprocess.Popen(["mpv", url])
    return HideWindowAction()


def AppendToQueue(url, yt_apikey=None, remove=False):
    ytvideolink = re.compile(
        "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/|shorts\/)?)([\w\-]{11})(\S+)?$"
    )
    ytplaylistlink = re.compile("PL[\w\-]{32}")
    ytchannellink = re.compile(
        "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:channel\/|c\/)?)([\w\-]{24}|\@[\w\-]+)(\S+)?$"
    )
    m_video = ytvideolink.match(url)
    m_playlist = ytplaylistlink.match(url)
    m_channel = ytchannellink.match(url)
    if m_video:
        video_id = m_video.group(6)
        if remove:
            with open(WATCHLIST, "r+") as f:
                lines = f.readlines()
                if lines:
                    lines = [line for line in lines if line[:-1] != video_id]
                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()
            items = [
                ExtensionResultItem(
                    icon="images/remove.png",
                    name="REMOVED: " + video_id,
                    description="enter to watch anyway",
                    on_enter=ExtensionCustomAction("q" + video_id),
                )
            ]
            return RenderResultListAction(items)
        with open(WATCHLIST, "a") as f:
            f.write(video_id + "\n")
        try:
            video_info = requests.get(
                yt_info,
                params={
                    "id": video_id,
                    "part": ["snippet", "contentDetails"],
                    "key": yt_apikey,
                },
                timeout=5,
            )
            assert video_info.status_code == 200, f"Error code {video_info.status_code}"
            video_info = video_info.json()["items"][0]
            video_title = video_info["snippet"]["title"]
            video_channl = video_info["snippet"]["channelTitle"]
            video_duration = str(
                parse_duration(video_info["contentDetails"]["duration"])
            )
            video_published = datetime.fromisoformat(
                video_info["snippet"]["publishedAt"]
            ).strftime("%-d %b, %H:%M")
            video_subtitle = [
                video_channl,
                video_duration,
                video_published,
                "enter to watch immediately",
            ]
            items = [
                ExtensionResultItem(
                    icon="images/append.png",
                    name="ADDED: " + video_title,
                    description=" - ".join(video_subtitle),
                    on_enter=ExtensionCustomAction("q" + video_id),
                )
            ]
        except Exception as e:
            items = [
                ExtensionResultItem(
                    icon="images/error.png",
                    name="Error fetching video",
                    description=str(e),
                    on_enter=HideWindowAction(),
                )
            ]

    elif m_playlist:
        playlist_id = url
        if remove:
            action_done = (
                "Playlist not found in subscriptions"
                if not os.path.isfile(HERE + f"/images/{playlist_id}.png")
                else "REMOVED: " + playlist_id
            )
            if action_done.startswith("R"):
                with open(SUBSCRIPTIONS, "r+") as f:
                    lines = f.readlines()
                    if lines:
                        lines = [
                            line
                            for line in lines
                            if line.split(" | ")[0] != playlist_id
                        ]
                        f.seek(0)
                        f.writelines(lines)
                        f.truncate()
                os.system("rm " + HERE + f"/images/{playlist_id}.png")
            items = [
                ExtensionResultItem(
                    icon="images/remove.png",
                    name=action_done,
                    description="bye",
                    on_enter=HideWindowAction(),
                )
            ]
            return RenderResultListAction(items)
        try:
            playlist_info = requests.get(
                pl_info,
                params={
                    "id": playlist_id,
                    "part": ["snippet", "contentDetails"],
                    "key": yt_apikey,
                },
            )
            assert playlist_info.status_code == 200, "Error fetching playlist"
            playlist_info = playlist_info.json()["items"][0]
            playlist_title = playlist_info["snippet"]["title"]

            with open(SUBSCRIPTIONS, "r+") as f:
                if playlist_id not in f.read():
                    f.write(
                        playlist_id
                        + " | "
                        + playlist_title
                        + " " * (23 - len(playlist_title))
                        + "| \n"
                    )

            playlist_description = playlist_info["snippet"]["description"]
            thumb = playlist_info["snippet"]["thumbnails"]["medium"]["url"]
            os.system(
                f"wget -O {HERE}/images/{playlist_id}.jpg {thumb} && "
                + f"convert {HERE}/images/{playlist_id}.jpg {HERE}/images/{playlist_id}.png && "
                + f"rm {HERE}/images/{playlist_id}.jpg"
            )
            items = [
                ExtensionResultItem(
                    icon=f"images/{playlist_id}.png",
                    name="ADDED PLAYLIST: " + playlist_title,
                    description=playlist_description,
                    on_enter=HideWindowAction(),
                )
            ]
        except Exception as e:
            items = [
                ExtensionResultItem(
                    icon="images/error.png",
                    name="Error fetching playlist",
                    description=str(e),
                    on_enter=HideWindowAction(),
                )
            ]
    elif m_channel:
        channel_id = m_channel.group(6)
        try:
            if channel_id.startswith("@"):
                channel_id = requests.get(
                    yt_search,
                    params={"q": channel_id, "part": "snippet", "key": yt_apikey},
                ).json()["items"][0]["id"]["channelId"]

            assert channel_id.startswith("UC"), f"Invalid channel id: {channel_id}"

            if remove:
                action_done = (
                    "Channel not found in subscriptions"
                    if not os.path.isfile(HERE + f"/images/{channel_id}.png")
                    else "REMOVED: " + channel_id
                )
                if action_done.startswith("R"):
                    with open(SUBSCRIPTIONS, "r+") as f:
                        lines = f.readlines()
                        if lines:
                            lines = [
                                line
                                for line in lines
                                if line.split("|")[0].strip() != channel_id
                            ]
                            f.seek(0)
                            f.writelines(lines)
                            f.truncate()
                    os.system("rm " + HERE + f"/images/{channel_id}.png")
                items = [
                    ExtensionResultItem(
                        icon="images/remove.png",
                        name=action_done,
                        description="bye",
                        on_enter=HideWindowAction(),
                    )
                ]
                return RenderResultListAction(items)

            channel_info = requests.get(
                ch_info,
                params={
                    "id": channel_id,
                    "part": ["snippet", "contentDetails"],
                    "key": yt_apikey,
                },
            )
            assert channel_info.status_code == 200, "Error {channel_info.status_code}"
            channel_info = channel_info.json()["items"][0]
            channel_title = channel_info["snippet"]["title"]

            with open(SUBSCRIPTIONS, "r+") as f:
                if channel_id not in f.read():
                    f.write(
                        channel_id
                        + "           | "
                        + channel_title
                        + " " * (23 - len(channel_title))
                        + "| \n"
                    )

            channel_description = channel_info["snippet"]["description"]
            thumb = channel_info["snippet"]["thumbnails"]["medium"]["url"]
            os.system(
                f"wget -O {HERE}/images/{channel_id}.jpg {thumb} && "
                + f"convert {HERE}/images/{channel_id}.jpg {HERE}/images/{channel_id}.png && "
                + f"rm {HERE}/images/{channel_id}.jpg"
            )

            items = [
                ExtensionResultItem(
                    icon=f"images/{channel_id}.png",
                    name="ADDED CHANNEL: " + channel_title,
                    description=channel_description,
                    on_enter=HideWindowAction(),
                )
            ]
        except Exception as e:
            items = [
                ExtensionResultItem(
                    icon="images/error.png",
                    name="Error fetching channel",
                    description=str(e),
                    on_enter=HideWindowAction(),
                )
            ]

    else:
        items = [
            ExtensionResultItem(
                icon="images/error.png",
                name="Invalid youtube link",
                description="Please try again",
                on_enter=HideWindowAction(),
            )
        ]
    return RenderResultListAction(items)


class YTLWExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        append = extension.preferences["append"]
        remove = extension.preferences["remove"]
        watch = extension.preferences["watch"]
        getqueue = extension.preferences["getqueue"]
        if event.get_data() == watch:
            wm = extension.preferences["watchlist-mode"]
            return (
                WatchVideo(stack=True)
                if wm == "Stack"
                else WatchVideo(random=True)
                if wm == "Random"
                else WatchVideo()
            )
        if event.get_data().startswith(append) or event.get_data().startswith(remove):
            return AppendToQueue(
                event.get_data()[2:],
                extension.preferences["yt_apikey"],
                remove=event.get_data().startswith(remove),
            )
        if event.get_data().startswith(getqueue):
            return WatchVideo(vid=event.get_data()[1:])


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        items = []
        append = extension.preferences["append"]
        remove = extension.preferences["remove"]
        watch = extension.preferences["watch"]
        getqueue = extension.preferences["getqueue"]
        if extension.preferences["yt_apikey"] == "":
            items.append(
                ExtensionResultItem(
                    icon="images/error.png",
                    name="No Youtube API key",
                    description="Please set it in preferences",
                    on_enter=HideWindowAction(),
                )
            )
            return RenderResultListAction(items)
        if event.get_argument() and event.get_argument().startswith(append):
            items.append(
                ExtensionResultItem(
                    icon="images/append.png",
                    name="Append " + event.get_argument()[2:],
                    description="I'll check if it's a valid youtube link",
                    on_enter=ExtensionCustomAction(
                        event.get_argument(), keep_app_open=True
                    ),
                )
            )
        elif event.get_argument() and event.get_argument().startswith(remove):
            items.append(
                ExtensionResultItem(
                    icon="images/remove.png",
                    name="Remove " + event.get_argument()[2:],
                    description="I'll check if it's a valid youtube link",
                    on_enter=ExtensionCustomAction(
                        event.get_argument(), keep_app_open=True
                    ),
                )
            )
        elif event.get_argument() and event.get_argument() == watch:
            items.append(
                ExtensionResultItem(
                    icon="images/watch.png",
                    name="Watch next video in watchlist",
                    description="If there's any that is",
                    on_enter=ExtensionCustomAction(event.get_argument()),
                )
            )
        elif event.get_argument() and event.get_argument().startswith(getqueue):
            yt_apikey = extension.preferences["yt_apikey"]
            with open(WATCHLIST, "r") as f:
                ids = [line[:-1] for line in f.readlines()[:-10:-1]]
            parts = ["snippet", "contentDetails"]
            try:
                videos_info = requests.get(
                    yt_info,
                    params={"id": ids, "part": parts, "key": yt_apikey},
                    timeout=5,
                )
                assert (
                    videos_info.status_code == 200
                ), f"Error code {videos_info.status_code}"
                videos_info = videos_info.json()["items"]
                for video_info in videos_info:
                    video_title = video_info["snippet"]["title"]
                    video_channl = video_info["snippet"]["channelTitle"]
                    video_channl_id = video_info["snippet"]["channelId"]
                    video_id = video_info["id"]
                    video_duration = str(
                        parse_duration(video_info["contentDetails"]["duration"])
                    )
                    video_published = datetime.fromisoformat(
                        video_info["snippet"]["publishedAt"]
                    ).strftime("%H:%M, %b %-d, %y")
                    video_subtitle = [video_channl, video_duration, video_published]
                    items.append(
                        ExtensionResultItem(
                            icon=f"images/{video_channl_id}.png"
                            if os.path.isfile(f"{HERE}/images/{video_channl_id}.png")
                            else "images/icon.png",
                            name=video_title,
                            description=" - ".join(video_subtitle),
                            on_enter=ExtensionCustomAction("q" + video_id),
                        )
                    )
            except Exception as e:
                items.append(
                    ExtensionResultItem(
                        icon="images/error.png",
                        name="Error fetching videos",
                        description=str(e),
                        on_enter=HideWindowAction(),
                    )
                )
        else:
            items.append(
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Loading ...",
                    on_enter=HideWindowAction(),
                )
            )
        return RenderResultListAction(items)


if __name__ == "__main__":
    YTLWExtension().run()
