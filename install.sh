#!/bin/bash
# One-shot installer for the Plex "Now Showing" poster display.
# Run on a Raspberry Pi running Raspberry Pi OS *with desktop*:
#     sudo bash install.sh
# Put install.sh, poster.py and config.json in the same folder first.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run with sudo:  sudo bash install.sh"
  exit 1
fi

SRC="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${SUDO_USER:-pi}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
DEST="$USER_HOME/poster"

for f in poster.py config.json; do
  if [ ! -f "$SRC/$f" ]; then
    echo "Missing $f next to install.sh, aborting."
    exit 1
  fi
done

echo "==> Installing files to $DEST"
mkdir -p "$DEST"
cp "$SRC/poster.py" "$SRC/config.json" "$DEST/"

echo "==> Creating kiosk launcher"
cat > "$DEST/start_kiosk.sh" <<'EOF'
#!/bin/bash
# Wait for the poster server, then open the display full screen.
until curl -s -o /dev/null http://localhost:8080; do sleep 2; done
BROWSER="$(command -v chromium-browser || command -v chromium)"
exec "$BROWSER" --kiosk --noerrdialogs --disable-infobars --incognito \
  --check-for-update-interval=31536000 --disable-features=Translate \
  http://localhost:8080
EOF
chmod +x "$DEST/start_kiosk.sh"
chown -R "$USER_NAME":"$USER_NAME" "$DEST"

echo "==> Creating poster server service"
cat > /etc/systemd/system/poster.service <<EOF
[Unit]
Description=Plex Now Showing poster server
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 $DEST/poster.py
WorkingDirectory=$DEST
Restart=always
RestartSec=5
User=$USER_NAME

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now poster.service

echo "==> Setting up kiosk autostart (labwc and LXDE both covered)"
LABWC_DIR="$USER_HOME/.config/labwc"
mkdir -p "$LABWC_DIR"
touch "$LABWC_DIR/autostart"
grep -q start_kiosk "$LABWC_DIR/autostart" || echo "$DEST/start_kiosk.sh &" >> "$LABWC_DIR/autostart"

LXDE_DIR="$USER_HOME/.config/lxsession/LXDE-pi"
mkdir -p "$LXDE_DIR"
if [ ! -f "$LXDE_DIR/autostart" ]; then
  cp /etc/xdg/lxsession/LXDE-pi/autostart "$LXDE_DIR/autostart" 2>/dev/null || touch "$LXDE_DIR/autostart"
fi
grep -q start_kiosk "$LXDE_DIR/autostart" || echo "@$DEST/start_kiosk.sh" >> "$LXDE_DIR/autostart"
chown -R "$USER_NAME":"$USER_NAME" "$USER_HOME/.config"

echo "==> Boot straight to the desktop and keep the screen awake"
if command -v raspi-config >/dev/null; then
  raspi-config nonint do_boot_behaviour B4 || true   # desktop, auto-login
  raspi-config nonint do_blanking 1 || true          # disable screen blanking
fi

echo
echo "Done. Reboot to start the display:  sudo reboot"
echo "Server status any time:  systemctl status poster"
