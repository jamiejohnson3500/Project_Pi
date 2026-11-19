#!/usr/bin/env python3
"""
Plex "Now Showing" poster display for Raspberry Pi (single file).

- Shuffles a random poster from your movie library every 30 seconds.
- While a movie is PLAYING on your Shield, shows its poster under a NOW SHOWING banner.
- When it is paused or stopped, goes back to shuffling.
- Restarts itself every 12 hours (change "restart_hours" in config.json).

Needs config.json in the same folder. Uses only the Python standard library.
Run:  python3 poster.py      then open http://localhost:8080 (the kiosk does this on boot).
"""
import json
import os
import random
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "config.json")) as f:
    CFG = json.load(f)

PLEX = CFG["plex_url"].rstrip("/")
TOKEN = CFG["plex_token"]
PLAYER = CFG.get("player_name", "").lower()
PLAYER_ID = CFG.get("player_machine_id", "")
LIBRARIES = [n.lower() for n in CFG.get("libraries", ["Movies"])]
SHUFFLE_SECONDS = int(CFG.get("rotate_seconds", 30))
POLL_SECONDS = float(CFG.get("poll_seconds", 2))
RESTART_HOURS = float(CFG.get("restart_hours", 12))
PORT = int(CFG.get("port", 8080))
BOOT_ID = str(time.time())

lock = threading.Lock()
thumbs = []        # poster paths for the shuffle
now_playing = None  # poster path of the movie playing right now, or None


def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def plex(path, params=None, raw=False):
    q = dict(params or {}, **{"X-Plex-Token": TOKEN})
    req = urllib.request.Request(PLEX + path + "?" + urllib.parse.urlencode(q),
                                 headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        return (data, r.headers.get("Content-Type", "image/jpeg")) if raw else json.loads(data)


def poster_url(thumb):
    return "/poster?path=" + urllib.parse.quote(thumb, safe="")


def load_library():
    global thumbs
    sections = plex("/library/sections")["MediaContainer"].get("Directory", [])
    found, matched = [], False
    for sec in sections:
        if sec["title"].lower() in LIBRARIES and sec.get("type") == "movie":
            matched = True
            items = plex("/library/sections/%s/all" % sec["key"])["MediaContainer"].get("Metadata", [])
            found += [m["thumb"] for m in items if m.get("thumb")]
    if not matched:
        log("No movie library matched %s. Found: %s" % (
            CFG.get("libraries"), ", ".join("%s (%s)" % (s["title"], s.get("type")) for s in sections)))
    with lock:
        thumbs = found
    log("Loaded %d posters" % len(found))


def library_loop():
    while True:
        try:
            load_library()
            time.sleep(6 * 3600)
        except Exception as e:
            log("Library load failed:", e)
            time.sleep(60)


def playing_thumb():
    """Poster of the movie actively playing on the Shield, or None (paused/stopped/other)."""
    for s in plex("/status/sessions")["MediaContainer"].get("Metadata", []):
        p = s.get("Player", {})
        if s.get("type") != "movie":
            continue
        is_shield = (PLAYER_ID and p.get("machineIdentifier") == PLAYER_ID) or \
                    (PLAYER and PLAYER in (p.get("title", "") + " " + p.get("product", "")).lower())
        if is_shield and p.get("state") in ("playing", "buffering") and s.get("thumb"):
            return s["thumb"]
    return None


def session_loop():
    global now_playing
    failures = 0
    while True:
        try:
            t = playing_thumb()
            with lock:
                now_playing = t
            failures = 0
        except Exception as e:
            failures += 1
            log("Session check failed (%d): %s" % (failures, e))
            if failures >= 3:  # Plex unreachable: don't stay stuck on a stale banner
                with lock:
                    now_playing = None
        time.sleep(POLL_SECONDS)


def restart_watchdog():
    """Restart this whole script after RESTART_HOURS so nothing can stay hung."""
    if RESTART_HOURS <= 0:
        return
    time.sleep(RESTART_HOURS * 3600)
    log("Scheduled restart")
    os.execv(sys.executable, [sys.executable] + sys.argv)


PAGE = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Now Showing</title>
<style>
  html, body { margin: 0; height: 100%; background: #000; overflow: hidden; cursor: none; }
  /* Rotate the complete poster page for a portrait-mounted screen.
     Change 90deg to -90deg if the image appears upside down. */
  #wrap {
    position: absolute;
    top: 0;
    left: 100vw;
    width: 100vh;
    height: 100vw;
    transform-origin: top left;
    transform: rotate(90deg);
    display: flex;
    flex-direction: column;
  }
  #banner {
    position: relative;
    flex: 0 0 auto; height: 0; overflow: hidden; text-align: center;
    background: radial-gradient(ellipse at center, #2358e6 0%, #0e2a8f 55%, #050f45 100%);
    color: #ffe27a; font-family: Georgia, "Times New Roman", serif;
    font-weight: bold; letter-spacing: 0.35em; text-transform: uppercase;
    text-shadow: 0 0 1.2vmin rgba(255, 220, 110, 0.85), 0 0.2vmin 0.4vmin rgba(0, 0, 0, 0.6);
    border-bottom: 0 solid #ffd76a;
    transition: height 0.8s ease, border-width 0.8s ease;
    display: flex; align-items: center; justify-content: center;
    font-size: min(5.5vmin, 8vw);
  }
  #banner.on { height: 12%; border-bottom-width: 0.4vmin; }
  #bannerText { position: relative; z-index: 2; }

  /* Marquee bulbs along the top and bottom edges, chasing in alternation */
  #banner::before, #banner::after {
    content: ""; position: absolute; left: 0; right: 0; height: 1.4vmin; z-index: 1;
    background: radial-gradient(circle, #fff7c9 0 32%, rgba(255, 220, 110, 0.35) 38%, transparent 46%) 0 50% / 3.2vmin 100% repeat-x;
    animation: bulbs 1.1s steps(1) infinite;
  }
  #banner::before { top: 0.5vmin; }
  #banner::after { bottom: 0.5vmin; animation-delay: -0.55s; }
  @keyframes bulbs { 0% { opacity: 1; } 50% { opacity: 0.35; } }

  /* Twinkling stars */
  .star {
    position: absolute; z-index: 0; background: #fff;
    clip-path: polygon(50% 0, 61% 39%, 100% 50%, 61% 61%, 50% 100%, 39% 61%, 0 50%, 39% 39%);
    opacity: 0; animation: twinkle ease-in-out infinite;
    filter: drop-shadow(0 0 0.6vmin #fff);
  }
  @keyframes twinkle {
    0%, 100% { opacity: 0; transform: scale(0.3) rotate(0deg); }
    50% { opacity: 1; transform: scale(1) rotate(45deg); }
  }
  #stage { position: relative; flex: 1 1 auto; min-height: 0; }
  #stage img {
    position: absolute; inset: 0; width: 100%; height: 100%;
    object-fit: contain; opacity: 0; transition: opacity 1.2s ease;
  }
  #stage img.show { opacity: 1; }
</style>
</head>
<body>
<div id="wrap">
  <div id="banner"><span id="bannerText">Now Showing</span></div>
  <div id="stage"><img id="a"><img id="b"></div>
</div>
<script>
const banner = document.getElementById('banner');

// Scatter twinkling stars around the banner
for (let i = 0; i < 34; i++) {
  const st = document.createElement('div');
  st.className = 'star';
  const size = 0.9 + Math.random() * 1.8;               // vmin
  st.style.width = st.style.height = size + 'vmin';
  st.style.left = (Math.random() * 98) + '%';
  st.style.top = (8 + Math.random() * 76) + '%';
  st.style.animationDuration = (1.6 + Math.random() * 2.4) + 's';
  st.style.animationDelay = (-Math.random() * 4) + 's';
  banner.appendChild(st);
}
const layers = [document.getElementById('a'), document.getElementById('b')];
let front = 0, currentPoster = null, lastChange = 0, mode = 'idle', rotate = 30, bootId = null;

function setPoster(url) {
  if (!url || url === currentPoster) return;
  const img = new Image();
  img.onload = () => {
    const next = layers[1 - front];
    next.src = url;
    next.classList.add('show');
    layers[front].classList.remove('show');
    front = 1 - front;
    currentPoster = url;
    lastChange = Date.now();
  };
  img.src = url;
}

async function tick() {
  try {
    const s = await (await fetch('/api/state', {cache: 'no-store'})).json();
    rotate = s.rotate || 30;
    if (bootId && s.boot !== bootId) { location.reload(); return; }
    bootId = s.boot;
    if (s.mode === 'playing') {
      banner.classList.add('on');
      setPoster(s.poster);
      mode = 'playing';
    } else {
      banner.classList.remove('on');
      const due = (Date.now() - lastChange) / 1000 >= rotate;
      if (mode === 'playing' || due || !currentPoster) {
        const r = await (await fetch('/api/random', {cache: 'no-store'})).json();
        if (r.poster) {
          // Make sure a new random poster is shown even if it equals the current one
          setPoster(r.poster);
          lastChange = Date.now();
        }
      }
      mode = 'idle';
    }
  } catch (e) { /* server restarting or network blip; try again */ }
  setTimeout(tick, 2000);
}
tick();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/api/state":
            with lock:
                t = now_playing
            if t:
                self.send_json({"mode": "playing", "poster": poster_url(t),
                                "rotate": SHUFFLE_SECONDS, "boot": BOOT_ID})
            else:
                self.send_json({"mode": "idle", "rotate": SHUFFLE_SECONDS, "boot": BOOT_ID})
        elif u.path == "/api/random":
            with lock:
                t = random.choice(thumbs) if thumbs else None
            self.send_json({"poster": poster_url(t)} if t else {})
        elif u.path == "/poster":
            path = urllib.parse.parse_qs(u.query).get("path", [""])[0]
            if not path.startswith("/library/"):
                self.send_error(400)
                return
            try:
                data, ctype = plex("/photo/:/transcode", {
                    "width": 720, "height": 1080, "minSize": 1, "upscale": 1, "url": path}, raw=True)
            except Exception:
                self.send_error(502)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "max-age=86400")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)


if __name__ == "__main__":
    threading.Thread(target=library_loop, daemon=True).start()
    threading.Thread(target=session_loop, daemon=True).start()
    threading.Thread(target=restart_watchdog, daemon=True).start()
    log("Serving on port %d (auto-restart every %g h)" % (PORT, RESTART_HOURS))
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
