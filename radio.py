#!/usr/bin/env python3
"""Control a private mpv instance; never touches other media players.

Shares its socket and state with the ABC Radio Omarchy bar widget, so both
control the same player.
"""
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
STATIONS = json.loads((BASE / 'stations.json').read_text())
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', f'/tmp/abc-radio-{os.getuid()}')) / 'abc-radio'
STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'abc-radio'
RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
SOCKET = RUNTIME / 'mpv.sock'
PREFS = STATE / 'settings.json'

def ipc(command):
    with socket.socket(socket.AF_UNIX) as conn:
        conn.settimeout(2)
        conn.connect(str(SOCKET))
        conn.sendall((json.dumps({'command': command, 'request_id': 1}) + '\n').encode())
        with conn.makefile() as stream:
            for line in stream:
                reply = json.loads(line)
                if reply.get('request_id') == 1:
                    if reply.get('error') != 'success':
                        raise RuntimeError(reply.get('error'))
                    return reply.get('data')
        raise RuntimeError('Player disconnected')

def get(prop, fallback=None):
    try:
        return ipc(['get_property', prop])
    except (OSError, RuntimeError):
        return fallback

def preferences():
    try:
        return json.loads(PREFS.read_text())
    except (OSError, ValueError):
        return {'station': 'brisbane', 'volume': 60}

def save(prefs):
    tmp = PREFS.with_suffix('.tmp')
    tmp.write_text(json.dumps(prefs))
    tmp.replace(PREFS)

def station_by_id(station_id):
    station = next((s for s in STATIONS if s['id'] == station_id), None)
    if station is None:
        raise ValueError('Unknown station: ' + station_id)
    return station

def ensure_player(prefs):
    if get('idle-active') is not None:
        return
    SOCKET.unlink(missing_ok=True)
    with (STATE / 'player.log').open('w') as log:
        subprocess.Popen(['mpv', '--no-config', '--no-video', '--idle=yes', '--terminal=no',
                          '--audio-display=no', '--keep-open=no', '--cache=yes',
                          '--demuxer-max-bytes=8MiB', '--network-timeout=15',
                          '--volume=' + str(prefs['volume']), '--input-ipc-server=' + str(SOCKET)],
                         stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    for _ in range(50):
        if get('idle-active') is not None:
            return
        time.sleep(.1)
    raise RuntimeError('mpv did not start. Check ' + str(STATE / 'player.log'))

def control(action='status', arg=None):
    """Run one player action under the shared lock and return the status."""
    with (RUNTIME / 'control.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prefs = preferences()
        if action == 'play':
            station = station_by_id(arg or prefs['station'])
            ensure_player(prefs)
            ipc(['loadfile', station['url'], 'replace'])
            ipc(['set_property', 'pause', False])
            prefs['station'] = station['id']
            save(prefs)
        elif action == 'toggle':
            if get('idle-active', True):
                ensure_player(prefs)
                ipc(['loadfile', station_by_id(prefs['station'])['url'], 'replace'])
                ipc(['set_property', 'pause', False])
            else:
                ipc(['cycle', 'pause'])
        elif action == 'stop':
            if get('idle-active') is not None:
                ipc(['stop'])
        elif action == 'volume':
            prefs['volume'] = max(0, min(100, int(float(arg))))
            if get('idle-active') is not None:
                ipc(['set_property', 'volume', prefs['volume']])
            save(prefs)
        elif action != 'status':
            raise ValueError('Usage: radio.py status|play [station]|toggle|stop|volume 0..100')
        idle = get('idle-active', True)
        paused = get('pause', False)
        station = next((s for s in STATIONS if s['id'] == prefs['station']), STATIONS[0])
        return {'station': station['id'], 'name': station['name'], 'page': station['page'],
                'playing': not idle and not paused, 'paused': not idle and paused,
                'active': not idle, 'buffering': bool(get('paused-for-cache', False)),
                'volume': round(get('volume', prefs['volume'])), 'error': '', 'stations': STATIONS}

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'
    print(json.dumps(control(action, sys.argv[2] if len(sys.argv) > 2 else None)))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(1)
