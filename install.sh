here=~/.local/share/ulauncher/extensions/com.github.oxke.ulauncher-ytwl
pip install $here/requirements.txt
sudo cp $here/ytfp.* /etc/systemd/system/
systemctl enable ytfp.timer
touch $here/subscriptions2
touch $here/watchlist2
