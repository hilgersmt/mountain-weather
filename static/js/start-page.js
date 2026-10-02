/**
 * Start-page preference with localStorage persistence
 *
 * Lets the user choose what the bare home page ("/") opens:
 *   - default : the site default (server-side DEFAULT_LOCATION)
 *   - fixed   : always one chosen location (redirect done early, in <head>)
 *   - nearest : the location closest to the device (Geolocation API),
 *               with NEAREST_ALIASES applied (e.g. any Bend band -> Bend Alpine)
 *
 * Only "/" redirects on load, so the dropdown and direct links keep working.
 * Changing the setting jumps straight to the new start page, from any page.
 * Each page also shows its distance from the user without ever prompting:
 * from a fresh fix if location is granted, else a fix shared in the last
 * 15 minutes (labelled with its age).
 * The position never leaves the browser; distances are computed here.
 */

(function() {
    'use strict';

    const START_STORAGE_KEY = 'mountain-weather-start';
    // Last position this device shared, for the "N miles from you" line. Some
    // browsers (Safari set to "Ask", Chrome "Allow this time") approve location
    // without reporting a lasting "granted", so a recent fix is reused instead
    // of prompting on every page.
    const POSITION_STORAGE_KEY = 'mountain-weather-last-position';
    // Short enough that a driver's distance can't be far off (~15 miles at
    // highway speed); older fixes are shown with their age.
    const POSITION_MAX_AGE_MS = 15 * 60 * 1000;
    const dataEl = document.getElementById('start-page-data');
    if (!dataEl) return;

    const cfg = JSON.parse(dataEl.textContent);
    const byKey = {};
    cfg.locations.forEach(function(loc) { byKey[loc.key] = loc; });

    const currentKey = document.body.dataset.location;
    const isHome = window.location.pathname === '/';

    const startSelect = document.getElementById('start-select');
    const noteEl = document.getElementById('start-note');

    /**
     * Read the saved preference; anything missing or invalid means "default"
     */
    function loadPref() {
        try {
            const pref = JSON.parse(localStorage.getItem(START_STORAGE_KEY) || 'null');
            if (pref && pref.mode === 'nearest') return pref;
            if (pref && pref.mode === 'fixed' && byKey[pref.key]) return pref;
        } catch (e) {
            console.warn('localStorage not available, using site default start page');
        }
        return { mode: 'default' };
    }

    /**
     * Save the preference ("default" is stored as no preference at all)
     */
    function savePref(pref) {
        try {
            if (pref.mode === 'default') {
                localStorage.removeItem(START_STORAGE_KEY);
            } else {
                localStorage.setItem(START_STORAGE_KEY, JSON.stringify(pref));
            }
            return true;
        } catch (e) {
            console.warn('Could not save start page to localStorage');
            return false;
        }
    }

    /**
     * Great-circle distance in km (haversine)
     */
    function distanceKm(lat1, lon1, lat2, lon2) {
        const toRad = Math.PI / 180;
        const dLat = (lat2 - lat1) * toRad;
        const dLon = (lon2 - lon1) * toRad;
        const a = Math.sin(dLat / 2) ** 2 +
                  Math.cos(lat1 * toRad) * Math.cos(lat2 * toRad) * Math.sin(dLon / 2) ** 2;
        return 6371 * 2 * Math.asin(Math.sqrt(a));
    }

    /**
     * Closest location to a position: { key, km }, with the band aliases applied
     * (km is the distance to the location returned, i.e. after the alias)
     */
    function nearest(lat, lon) {
        let best = null;
        let bestKm = Infinity;
        cfg.locations.forEach(function(loc) {
            const km = distanceKm(lat, lon, loc.lat, loc.lon);
            if (km < bestKm) {
                bestKm = km;
                best = loc.key;
            }
        });
        const key = cfg.aliases[best] || best;
        const km = key === best ? bestKm : distanceKm(lat, lon, byKey[key].lat, byKey[key].lon);
        return { key: key, km: km };
    }

    function rememberPosition(coords) {
        try {
            localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify({
                lat: coords.latitude, lon: coords.longitude, t: Date.now()
            }));
        } catch (e) { /* storage blocked: distance just won't persist */ }
    }

    function forgetPosition() {
        try { localStorage.removeItem(POSITION_STORAGE_KEY); } catch (e) { /* ignore */ }
    }

    /**
     * The remembered position if it's recent enough, else null
     */
    function recentPosition() {
        try {
            const p = JSON.parse(localStorage.getItem(POSITION_STORAGE_KEY) || 'null');
            if (p && typeof p.lat === 'number' && typeof p.lon === 'number' &&
                Date.now() - p.t < POSITION_MAX_AGE_MS) {
                return p;
            }
        } catch (e) { /* fall through */ }
        return null;
    }

    /**
     * Ask the browser for a coarse position; callback(errorMessage, match)
     */
    function locate(callback) {
        if (!navigator.geolocation) {
            callback('This browser doesn’t support location.');
            return;
        }
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                rememberPosition(pos.coords);
                callback(null, nearest(pos.coords.latitude, pos.coords.longitude));
            },
            function(err) {
                if (err.code === err.PERMISSION_DENIED) {
                    forgetPosition();
                    callback('Location permission is off for this site. On iPhone: tap aA in the ' +
                             'address bar → Website Settings → Location → Allow.');
                } else if (err.code === err.TIMEOUT) {
                    callback('Getting your location timed out.');
                } else {
                    callback('Your location isn’t available right now.');
                }
            },
            // Coarse is plenty for picking a mountain; reuse a fix up to 10 min old.
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }
        );
    }

    function nameOf(key) {
        return byKey[key] ? byKey[key].name : key;
    }

    /**
     * "under 1 mile" / "6.2 miles" / "612 miles"
     */
    function formatMiles(km) {
        const miles = km * 0.621371;
        if (miles < 1) return 'under 1 mile';
        if (miles < 10) {
            const tenths = Math.round(miles * 10) / 10;
            return tenths === 1 ? '1 mile' : tenths + ' miles';
        }
        return Math.round(miles).toLocaleString() + ' miles';
    }

    function describe(match) {
        return nameOf(match.key) + ' (' + formatMiles(match.km) + ' away)';
    }

    /**
     * Show how far this page's location is from the user, without ever
     * prompting: a fresh fix if location is granted, otherwise a position this
     * device shared within the last 15 minutes; nothing if denied or unknown.
     */
    function showDistanceIfAllowed() {
        const el = document.getElementById('location-distance');
        const here = byKey[currentKey];
        if (!el || !here) return;

        function render(lat, lon, ageMs) {
            let text = '📍 ' + formatMiles(distanceKm(lat, lon, here.lat, here.lon)) + ' from you';
            const minutes = Math.round((ageMs || 0) / 60000);
            if (minutes >= 2) text += ' · as of ' + minutes + ' min ago';
            el.textContent = text;
            el.hidden = false;
        }

        function useRemembered() {
            const p = recentPosition();
            if (p) render(p.lat, p.lon, Date.now() - p.t);
        }

        if (!navigator.geolocation || !navigator.permissions || !navigator.permissions.query) {
            useRemembered();
            return;
        }

        navigator.permissions.query({ name: 'geolocation' }).then(function(status) {
            if (status.state === 'denied') {
                forgetPosition();
                return;
            }
            if (status.state !== 'granted') {
                useRemembered();
                return;
            }
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    rememberPosition(pos.coords);
                    render(pos.coords.latitude, pos.coords.longitude);
                },
                useRemembered,
                { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }
            );
        }).catch(useRemembered);
    }

    function showNote(text) {
        if (!noteEl) return;
        noteEl.textContent = text;
        noteEl.hidden = !text;
    }

    /**
     * Go to a location unless it's already showing; true if navigating
     */
    function goTo(key, replace) {
        if (!key || key === currentKey) return false;
        const url = '/' + encodeURIComponent(key);
        if (replace) {
            window.location.replace(url);
        } else {
            window.location.assign(url);
        }
        return true;
    }

    /**
     * Dropdown value for a preference: "nearest", "default" or a location key
     */
    function valueOf(pref) {
        if (pref.mode !== 'fixed') return pref.mode;
        // The default location isn't listed separately; it *is* "Site default".
        return pref.key === cfg.default ? 'default' : pref.key;
    }

    /**
     * On the home page in "nearest" mode, go to the nearest location
     */
    function applyNearestOnHome() {
        showNote('Finding the location nearest you…');
        locate(function(error, match) {
            if (error) {
                showNote(error + ' Showing the site default.');
                return;
            }
            if (!goTo(match.key, true)) {
                showNote('Nearest to you: ' + describe(match) + '.');
            }
        });
    }

    /**
     * Wire up the Start page dropdown. Each choice is saved, then the new
     * start page is shown right away (from any page).
     */
    function initSelect() {
        if (!startSelect) return;
        let pref = loadPref();
        startSelect.value = valueOf(pref);

        const storageBlocked = 'Couldn’t save (storage is blocked in this browser).';

        startSelect.addEventListener('change', function() {
            const value = startSelect.value;
            showNote('');

            if (value === 'nearest') {
                showNote('Finding the location nearest you…');
                // Asking here (from a user action) is what triggers the permission prompt.
                locate(function(error, match) {
                    if (error) {
                        startSelect.value = valueOf(pref);
                        showNote(error + ' Start page not changed.');
                        return;
                    }
                    pref = { mode: 'nearest' };
                    if (!savePref(pref)) {
                        showNote(storageBlocked);
                    } else if (!goTo(match.key)) {
                        showNote('Saved. The home page opens the nearest location — right now, ' +
                                 describe(match) + '.');
                    }
                });
                return;
            }

            const target = value === 'default' ? cfg.default : value;
            pref = value === 'default' ? { mode: 'default' } : { mode: 'fixed', key: value };
            if (!savePref(pref)) {
                showNote(storageBlocked);
            } else if (!goTo(target)) {
                showNote('Saved. The home page opens ' + nameOf(target) + '.');
            }
        });
    }

    initSelect();
    if (isHome && loadPref().mode === 'nearest') {
        applyNearestOnHome();
    }
    showDistanceIfAllowed();
})();
