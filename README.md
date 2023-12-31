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
- Add the key in the settings of the extension
- _(systemd)_ run the following command:
    ```bash
    sudo bash ~/.local/share/ulauncher/extensions/com.github.oxke.ulauncher-ytwl/setup
    ```
