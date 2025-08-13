cat > /home/dasha/ant_colony/start_ant_colony.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/dasha/ant_colony"
PIDFILE="$APP_DIR/ant_colony.pid"
LOGFILE="$APP_DIR/run.log"

# If already running, exit quietly
if [ -f "$PIDFILE" ] && ps -p "$(cat "$PIDFILE")" > /dev/null 2>&1; then
  exit 0
fi

cd "$APP_DIR"

# Headless SDL for the LCD path; unbuffered logging
export SDL_VIDEODRIVER=dummy
export PYTHONUNBUFFERED=1

# Wait for SPI device to appear
for i in {1..15}; do
  [ -e /dev/spidev0.0 ] && break
  sleep 1
done
sleep 2

# Write our PID and run the app (exec keeps same PID)
echo $$ > "$PIDFILE"
exec /usr/bin/python3 main.py >> "$LOGFILE" 2>&1
EOF

chmod +x /home/dasha/ant_colony/start_ant_colony.sh
