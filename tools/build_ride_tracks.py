#!/usr/bin/env python3
"""Build static/data/ride_tracks.json — per-ride paths for the map heat + lines layers.

Pulls every activity's summary_polyline from the Strava API (credentials from
~/.config/strava-mcp/config.json, auto-refreshing the token) and emits a flat,
downsampled [lat, lng] point list. Re-run whenever you want the layer current.
"""
import json, os, time, urllib.request, urllib.parse

CONFIG = os.path.expanduser("~/.config/strava-mcp/config.json")
OUT = os.path.join(os.path.dirname(__file__), "..", "static", "data", "ride_tracks.json")
MAX_PTS_PER_RIDE = 60


def load_token():
    cfg = json.load(open(CONFIG))
    if cfg.get("expiresAt", 0) < time.time() + 300:
        data = urllib.parse.urlencode({
            "client_id": cfg["clientId"], "client_secret": cfg["clientSecret"],
            "grant_type": "refresh_token", "refresh_token": cfg["refreshToken"],
        }).encode()
        with urllib.request.urlopen("https://www.strava.com/oauth/token", data) as r:
            tok = json.load(r)
        cfg.update(accessToken=tok["access_token"], refreshToken=tok["refresh_token"],
                   expiresAt=tok["expires_at"])
        json.dump(cfg, open(CONFIG, "w"), indent=2)
    return cfg["accessToken"]


def decode_polyline(s):
    """Standard Google encoded polyline -> [(lat, lng), ...]."""
    pts, i, lat, lng = [], 0, 0, 0
    while i < len(s):
        for which in (0, 1):
            shift = result = 0
            while True:
                b = ord(s[i]) - 63; i += 1
                result |= (b & 0x1F) << shift; shift += 5
                if b < 0x20: break
            d = ~(result >> 1) if result & 1 else result >> 1
            if which == 0: lat += d
            else: lng += d
        pts.append((lat / 1e5, lng / 1e5))
    return pts


def main():
    token = load_token()
    hdr = {"Authorization": f"Bearer {token}"}
    rides, npts = [], 0
    page = 1
    while True:
        url = f"https://www.strava.com/api/v3/athlete/activities?per_page=200&page={page}"
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req) as r:
            acts = json.load(r)
        if not acts: break
        for a in acts:
            poly = (a.get("map") or {}).get("summary_polyline")
            if not poly: continue
            pts = decode_polyline(poly)
            step = max(1, len(pts) // MAX_PTS_PER_RIDE)
            path = [[round(p[0], 4), round(p[1], 4)] for p in pts[::step]]
            rides.append({"n": a.get("name", "")[:60],
                          "d": (a.get("start_date_local") or "")[:10],
                          "p": path})
            npts += len(path)
        print(f"page {page}: total {len(rides)} rides, {npts} points")
        page += 1
        time.sleep(0.5)
    json.dump(rides, open(OUT, "w"), separators=(",", ":"))
    print(f"wrote {OUT}: {len(rides)} rides, {npts} points, "
          f"{os.path.getsize(OUT)//1024} KB")


if __name__ == "__main__":
    main()
