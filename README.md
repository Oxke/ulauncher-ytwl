[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# ulauncher-ytwl
Simple ulauncher extension for having a youtube watchlist that updates at each new video from subscribed channels

![2023-12-01\_01-29](https://github.com/Oxke/ulauncher-ytwl/assets/40807290/68f126bf-f83e-4893-b2a1-b67d8fca4157)

## Features
- Lets you add to watchlist all videos in a playlist (even from search results)
- Lets you search on youtube for videos
- Stores a watchlist of youtube videos
- Subscribes to channels and automatically adds new videos to the watchlist
- Subscribes to playlists and automatically adds new videos to the watchlist
- Lets you fetch for new videos immediately and know time of last fetch


## Setup
- Get an API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Activate the YouTube Data API v3
- _(systemd)_ run the following command:
    ```bash
    bash ~/.local/share/ulauncher/extensions/com.github.oxke.ulauncher-ytwl/setup
    ```
- Add the Youtube Data API key in the settings of the extension

## Instructions (keys can be modified)
- `y s {search}` to search for YouTube videos or channels
- `y a {video / channel}` to subscribe to a new channel or append a new video the the watchlist (insert a link)
- `y a {playlist ID}` to subscribe or add all videos from a playlist (insert the playlist ID)
- `y w` to watch the next video
- `y q` to get the whole list
