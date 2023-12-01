pip install ~/.local/share/ulauncher/extensions/com.github.oxke.ulauncher-ytwl/requirements.txt
sudo cp ~/.local/share/ulauncher/extensions/com.github.oxke.ulauncher-ytwl/ytfp.* /etc/systemd/system/
systemctl enable ytfp.timer
