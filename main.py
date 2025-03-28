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
import fp


copy = lambda text: subprocess.run(
    "xclip -selection clipboard", universal_newlines=True, input=text, shell=True
)

HERE = os.path.dirname(os.path.realpath(__file__))
CONFIG = os.environ.get("HOME") + "/.config/ulauncher/com.github.oxke.ulauncher-ytwl"
WATCHLIST = CONFIG + "/watchlist"
SUBSCRIPTIONS = CONFIG + "/subscriptions"
IMAGES = CONFIG + "/images"

yt_info = "https://www.googleapis.com/youtube/v3/videos"
pl_info = "https://www.googleapis.com/youtube/v3/playlists"
pl_items = "https://www.googleapis.com/youtube/v3/playlistItems"
ch_info = "https://www.googleapis.com/youtube/v3/channels"
yt_search = "https://www.googleapis.com/youtube/v3/search"
yt_watch = "https://www.youtube.com/watch?v="
yt_playlist = "https://www.youtube.com/playlist?list="


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
    subprocess.Popen(["mpv", "--ytdl-raw-options=cookies-from-browser=brave", url])
    os.system(f"rm {IMAGES}/{url[:-11]}.png")
    return HideWindowAction()


def SubscribeToPlaylist(playlist_id, remove, yt_apikey):
    if remove:
        action_done = (
            "Playlist not found in subscriptions"
            if not os.path.isfile(IMAGES + f"/{playlist_id}.png")
            else "REMOVED: " + playlist_id
        )
        if action_done.startswith("R"):
            with open(SUBSCRIPTIONS, "r+") as f:
                lines = f.readlines()
                if lines:
                    lines = [
                        line for line in lines if line.split(" | ")[0] != playlist_id
                    ]
                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()
            os.system("rm " + IMAGES + f"/{playlist_id}.png")
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
            f"wget -q -O {IMAGES}/{playlist_id}.jpg {thumb} && "
            + f"magick {IMAGES}/{playlist_id}.jpg {IMAGES}/{playlist_id}.png && "
            + f"rm {IMAGES}/{playlist_id}.jpg"
        )
        items = [
            ExtensionResultItem(
                icon=f"{IMAGES}/{playlist_id}.png",
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


def AddAllPlaylistVideosToWatchlist(playlist_id, remove, yt_apikey, getqueue="q"):
    try:
        playlist_items = requests.get(
            pl_items,
            params={
                "playlistId": playlist_id,
                "part": "snippet",
                "maxResults": 50,
                "key": yt_apikey,
            },
        )
        assert playlist_items.status_code == 200, "Error fetching playlist"
        playlist_items = playlist_items.json()["items"]
        video_ids = [
            item["snippet"]["resourceId"]["videoId"] for item in playlist_items
        ]
        if remove:
            with open(WATCHLIST, "r+") as f:
                lines = f.readlines()
                if lines:
                    lines = [line for line in lines if line[:-1] not in video_ids]
                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()
            items = [
                ExtensionResultItem(
                    icon="images/remove.png",
                    name="REMOVED all videos from " + playlist_id,
                    description="bye",
                    on_enter=HideWindowAction(),
                )
            ]
            return RenderResultListAction(items)
        with open(WATCHLIST, "a") as f:
            f.writelines([video_id + "\n" for video_id in video_ids])
        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/append.png",
                    name="ADDED all videos from " + playlist_id,
                    description="Enter to start watching them",
                    on_enter=ExtensionCustomAction(getqueue + video_ids[0]),
                )
            ]
        )
    except Exception as e:
        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/error.png",
                    name="Error fetching playlist",
                    description=str(e),
                    on_enter=HideWindowAction(),
                )
            ]
        )


def AppendToQueue(
    url, yt_apikey=None, remove=False, info=False, append="a", getqueue="q"
):
    ytvideolink = re.compile(
        r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/|shorts\/)?)([\w\-]{11})(\S+)?$"
    )
    ytplaylistlink = re.compile(r"PL[A-Za-z0-9_\-]{32}")
    ytchannellink = re.compile(
        r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:channel\/|c\/)?)([\w\-]{24}|\@[\w\-]+)(\S+)?$"
    )
    m_video = ytvideolink.search(url)
    m_playlist = ytplaylistlink.search(url)
    m_channel = ytchannellink.search(url)
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
                    on_enter=ExtensionCustomAction(getqueue + video_id),
                )
            ]
            return RenderResultListAction(items)
        if not info:
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
                "enter to add to watch-list" if info else "enter to watch immediately",
            ]
            if info:
                items = [
                    ExtensionResultItem(
                        icon="images/append.png",
                        name="add " + video_title,
                        description=" - ".join(video_subtitle),
                        on_enter=ExtensionCustomAction(
                            append + " " + url, keep_app_open=True
                        ),
                    ),
                    ExtensionResultItem(
                        icon="images/copy.png",
                        name="Copy link to clipboard",
                        description=yt_watch + video_id,
                        on_enter=ExtensionCustomAction("Y" + yt_watch + video_id),
                    ),
                ]
            else:
                items = [
                    ExtensionResultItem(
                        icon="images/append.png",
                        name="ADDED: " + video_title,
                        description=" - ".join(video_subtitle),
                        on_enter=ExtensionCustomAction(getqueue + video_id),
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
        playlist_id = m_playlist.group(0)
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
            playlist_description = playlist_info["snippet"]["description"]
            playlist_author = playlist_info["snippet"]["channelTitle"]
            if remove:
                items = [
                    ExtensionResultItem(
                        icon="images/remove.png",
                        name="REMOVE ALL VIDEOS FROM: " + playlist_title,
                        description="{playlist_author} - {playlist_description}",
                        on_enter=ExtensionCustomAction(
                            "ADDALLr" + playlist_id, keep_app_open=True
                        ),
                    ),
                    ExtensionResultItem(
                        icon="images/playlist.png",
                        name="UNSUBSCRIBE FROM: " + playlist_title,
                        description="{playlist_author} - {playlist_description}",
                        on_enter=ExtensionCustomAction(
                            "SUBSCRIBEr" + playlist_id, keep_app_open=True
                        ),
                    ),
                ]
            else:
                items = [
                    ExtensionResultItem(
                        icon="images/append.png",
                        name="ADD ALL VIDEOS FROM: " + playlist_title,
                        description=f"{playlist_author} - {playlist_description}",
                        on_enter=ExtensionCustomAction(
                            "ADDALL" + playlist_id, keep_app_open=True
                        ),
                    ),
                    ExtensionResultItem(
                        icon="images/playlist.png",
                        name="SUBSCRIBE TO: " + playlist_title,
                        description=f"{playlist_author} - {playlist_description}",
                        on_enter=ExtensionCustomAction(
                            "SUBSCRIBE" + playlist_id, keep_app_open=True
                        ),
                    ),
                ]

                if info:
                    items.append(
                        ExtensionResultItem(
                            icon="images/copy.png",
                            name="Copy link to clipboard",
                            description=yt_playlist + playlist_id,
                            on_enter=ExtensionCustomAction(
                                "Y" + yt_playlist + playlist_id,
                            ),
                        )
                    )
        except Exception as e:
            items = [
                ExtensionResultItem(
                    icon="images/error.png",
                    name="Error retrieving playlist",
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
                    if not os.path.isfile(IMAGES + f"/{channel_id}.png")
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
                    os.system(f"rm {IMAGES}/{channel_id}.png")
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

            if not info:
                with open(SUBSCRIPTIONS, "r+") as f:
                    if channel_id not in f.read():
                        f.write(
                            channel_id
                            + "           | "
                            + channel_title
                            + " " * (23 - len(channel_title))
                            + "|\n"
                        )

            thumb = channel_info["snippet"]["thumbnails"]["medium"]["url"]
            os.system(
                f"wget -q -O {IMAGES}/{channel_id}.jpg {thumb} && "
                + f"magick {IMAGES}/{channel_id}.jpg {IMAGES}/{channel_id}.png && "
                + f"rm {IMAGES}/{channel_id}.jpg"
            )

            channel_description = channel_info["snippet"]["description"]

            if info:
                items = [
                    ExtensionResultItem(
                        icon="images/append.png",
                        name="subscribe to " + channel_title,
                        description=channel_description,
                        on_enter=ExtensionCustomAction(
                            append + " " + channel_id, keep_app_open=True
                        ),
                    ),
                    ExtensionResultItem(
                        icon="images/copy.png",
                        name="Copy link to cliboard",
                        description=(
                            churl := f"https://www.youtube.com/channel/{channel_id}"
                        ),
                        on_enter=ExtensionCustomAction("Y" + churl),
                    ),
                ]
            else:
                items = [
                    ExtensionResultItem(
                        icon=f"{IMAGES}/{channel_id}.png",
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


def Search(query, /, yt_apikey=None, append="a", thumbnail=True):
    try:
        search_results = requests.get(
            yt_search,
            params={
                "q": query,
                "part": "snippet",
                "key": yt_apikey,
            },
        )
        assert (
            search_results.status_code == 200
        ), f"Error code {search_results.status_code}"
        search_results = search_results.json()["items"]
        items = []
        for result in search_results:
            title = result["snippet"]["title"]
            channl = result["snippet"]["channelTitle"]
            channl_id = result["snippet"]["channelId"]
            kind = result["id"]["kind"].split("#")[1]
            thumb = result["snippet"]["thumbnails"]["medium"]["url"]
            if kind == "channel":
                if thumbnail:
                    os.system(
                        f"wget -q -O {IMAGES}/{channl_id}.jpg {thumb} && "
                        + f"magick {IMAGES}/{channl_id}.jpg {IMAGES}/{channl_id}.png && "
                        + f"rm {IMAGES}/{channl_id}.jpg"
                    )
                items.append(
                    ExtensionResultItem(
                        icon=(
                            f"{IMAGES}/{channl_id}.png"
                            if os.path.isfile(f"{IMAGES}/{channl_id}.png")
                            else "images/channel.png"
                        ),
                        name=title,
                        description="Enter to subscribe to channel",
                        on_enter=ExtensionCustomAction(
                            f"i https://www.youtube.com/channel/{channl_id}",
                            keep_app_open=True,
                        ),
                    )
                )
            elif kind == "playlist":
                playlist_id = result["id"]["playlistId"]
                if thumbnail:
                    os.system(
                        f"wget -q -O {IMAGES}/{playlist_id}.jpg {thumb} && "
                        + f"magick {IMAGES}/{playlist_id}.jpg {IMAGES}/{playlist_id}.png && "
                        + f"rm {IMAGES}/{playlist_id}.jpg"
                    )
                items.append(
                    ExtensionResultItem(
                        icon=(
                            f"{IMAGES}/{playlist_id}.png"
                            if os.path.isfile(f"{IMAGES}/{playlist_id}.png")
                            else "images/playlist.png"
                        ),
                        name=title,
                        description="Playlist: enter to subscribe to subscribe or add all of its videos to watchlist",
                        on_enter=ExtensionCustomAction(
                            f"i {playlist_id}", keep_app_open=True
                        ),
                    )
                )
            elif kind == "video":
                video_id = result["id"]["videoId"]
                video_published = datetime.fromisoformat(
                    result["snippet"]["publishedAt"]
                ).strftime("%H:%M, %b %-d, %y")
                video_subtitle = [channl, video_published]
                if thumbnail:
                    video_thumbnail = result["snippet"]["thumbnails"]["medium"]["url"]
                    os.system(
                        f"wget -q -O {IMAGES}/{video_id}.jpg {video_thumbnail} >/dev/null & "
                        + f'magick {IMAGES}/{video_id}.jpg -gravity center -background "rgba(0, 0, 0, 0)" -extent 256x256 {IMAGES}/{video_id}.png && '
                        + f"rm {IMAGES}/{video_id}.jpg"
                    )
                items.append(
                    ExtensionResultItem(
                        icon=(
                            f"{IMAGES}/{video_id}.png"
                            if os.path.isfile(f"{IMAGES}/{video_id}.png")
                            else (
                                f"{IMAGES}/{channl_id}.png"
                                if os.path.isfile(f"{IMAGES}/{channl_id}.png")
                                else "images/icon.png"
                            )
                        ),
                        name=title,
                        description=" - ".join(video_subtitle),
                        on_enter=ExtensionCustomAction(
                            f"i {yt_watch}{video_id}", keep_app_open=True
                        ),
                    )
                )
            else:
                items.append(
                    ExtensionResultItem(
                        icon="images/error.png",
                        name="Didn't recognize this kind of result",
                        description="Please report this issue, specifying the query",
                        on_enter=HideWindowAction(),
                    )
                )
    except Exception as e:
        items = [
            ExtensionResultItem(
                icon="images/error.png",
                name="Error fetching videos",
                description=str(e),
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
        if event.get_data().startswith("SUBSCRIBE"):
            playlist_id = (
                event.get_data()[9:]
                if event.get_data()[9] == "P"
                else event.get_data()[10:]
            )
            return SubscribeToPlaylist(
                playlist_id,
                remove=event.get_data()[9] == "r",
                yt_apikey=extension.preferences["yt_apikey"],
            )
        if event.get_data().startswith("ADDALL"):
            playlist_id = (
                event.get_data()[6:]
                if event.get_data()[6] == "P"
                else event.get_data()[7:]
            )
            return AddAllPlaylistVideosToWatchlist(
                playlist_id,
                event.get_data()[6] == "r",
                yt_apikey=extension.preferences["yt_apikey"],
                getqueue=extension.preferences["getqueue"],
            )

        if event.get_data() == "FETCH":
            num_new_videos = fp.fetch()
            return RenderResultListAction(
                [
                    ExtensionResultItem(
                        icon="images/fetch_yep.png",
                        name=(
                            "No new videos"
                            if num_new_videos == 0
                            else (
                                "Added one new video"
                                if num_new_videos == 1
                                else f"Added {num_new_videos} new videos"
                            )
                        ),
                        description="Write 'y q' to see the watchlist",
                        on_enter=HideWindowAction(),
                    )
                ]
            )
        if event.get_data() == "DELETE":
            os.system(f"echo > {WATCHLIST}")
            return RenderResultListAction(
                [
                    ExtensionResultItem(
                        icon="images/remove.png",
                        name="Watchlist deleted",
                        description="It's gone forever",
                        on_enter=HideWindowAction(),
                    )
                ]
            )
        search = extension.preferences["search"]
        append = extension.preferences["append"]
        remove = extension.preferences["remove"]
        watch = extension.preferences["watch"]
        getqueue = extension.preferences["getqueue"]
        if event.get_data().startswith(search):
            return Search(
                event.get_data()[2:],
                extension.preferences["yt_apikey"],
                append,
                extension.preferences["thumbnail"] == "Video",
            )
        if event.get_data() == watch:
            wm = extension.preferences["watchlist-mode"]
            return (
                WatchVideo(stack=True)
                if wm == "Stack"
                else WatchVideo(random=True) if wm == "Random" else WatchVideo()
            )
        if event.get_data().startswith(append) or event.get_data().startswith(remove):
            return AppendToQueue(
                event.get_data()[2:],
                extension.preferences["yt_apikey"],
                remove=event.get_data().startswith(remove),
                append=append,
                getqueue=getqueue,
            )
        if event.get_data().startswith(getqueue):
            return WatchVideo(vid=event.get_data()[1:])
        if event.get_data().startswith("i"):
            return AppendToQueue(
                event.get_data()[2:],
                extension.preferences["yt_apikey"],
                remove=False,
                info=True,
                append=append,
                getqueue=getqueue,
            )
        if event.get_data().startswith("Y"):
            copy(event.get_data()[1:])
            return HideWindowAction()


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        items = []
        search = extension.preferences["search"]
        append = extension.preferences["append"]
        remove = extension.preferences["remove"]
        watch = extension.preferences["watch"]
        getqueue = extension.preferences["getqueue"]
        lastfetched = extension.preferences["lastfetched"]
        fetch = extension.preferences["fetch-now"]
        del_list = extension.preferences["delete-list"]
        thumbnail = extension.preferences["thumbnail"] == "Video"
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
        if event.get_argument() and event.get_argument().startswith(search):
            items.append(
                ExtensionResultItem(
                    icon="images/search.png",
                    name="Search " + event.get_argument()[2:],
                    description="Press enter to search for videos",
                    on_enter=ExtensionCustomAction(
                        event.get_argument(), keep_app_open=True
                    ),
                )
            )
        elif event.get_argument() and event.get_argument().startswith(append):
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
                    if thumbnail:
                        video_thumbnail = video_info["snippet"]["thumbnails"]["medium"][
                            "url"
                        ]
                        os.system(
                            f"wget -q -O {IMAGES}/{video_id}.jpg {video_thumbnail} > /dev/null & "
                            + f'magick {IMAGES}/{video_id}.jpg -gravity center -background "rgba(0, 0, 0, 0)" -extent 256x256 {IMAGES}/{video_id}.png && '
                            + f"rm {IMAGES}/{video_id}.jpg"
                        )
                    items.append(
                        ExtensionResultItem(
                            icon=(
                                f"{IMAGES}/{video_id}.png"
                                if os.path.isfile(f"{IMAGES}/{video_id}.png")
                                else (
                                    f"{IMAGES}/{video_channl_id}.png"
                                    if os.path.isfile(f"{IMAGES}/{video_channl_id}.png")
                                    else "images/icon.png"
                                )
                            ),
                            name=video_title,
                            description=" - ".join(video_subtitle),
                            on_enter=ExtensionCustomAction(getqueue + video_id),
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
        elif event.get_argument() and event.get_argument() == lastfetched:
            last_fetched = fp.get_last_fetched(local_tz=True).strftime(
                "%b %-d at %H:%M"
            )
            items.append(
                ExtensionResultItem(
                    icon="images/fetch.png",
                    name="Watchlist was last updated on " + last_fetched,
                    description="Press enter to fetch again",
                    on_enter=ExtensionCustomAction("FETCH", keep_app_open=True),
                )
            )
        elif event.get_argument() and event.get_argument() == fetch:
            items.append(
                ExtensionResultItem(
                    icon="images/fetch.png",
                    name="Fetch for new videos from subscriptions",
                    on_enter=ExtensionCustomAction("FETCH", keep_app_open=True),
                )
            )
        elif event.get_argument() and event.get_argument() == del_list:
            items.append(
                ExtensionResultItem(
                    icon="images/remove.png",
                    name="Delete watchlist",
                    description="This action is irreversible",
                    on_enter=ExtensionCustomAction("DELETE", keep_app_open=True),
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
