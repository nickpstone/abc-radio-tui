#!/usr/bin/env python3
"""Read the on-air programme from the selected station's official live page."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import urllib.request

from radio import STATIONS, STATE


def parse_programme(html, now):
    match = re.search(r'<script\b[^>]*\bid="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not match:
        raise ValueError('ABC programme data unavailable')
    data = json.loads(match.group(1))
    components = data['props']['pageProps']['data']['componentsContent']
    for component in components:
        props = component.get('componentProps', {})
        if not props.get('papiServiceId') or not props.get('title'):
            continue
        try:
            start = datetime.fromisoformat(props['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(props['end'].replace('Z', '+00:00'))
        except (KeyError, ValueError):
            continue
        if start <= now < end:
            presenters = ', '.join(p.get('names', {}).get('full', '') for p in props.get('preparedPresenters', []))
            return {'title': props['title'], 'presenter': presenters,
                    'start': start.isoformat(), 'end': end.isoformat(),
                    'link': props.get('programLink', ''), 'available': True}
    return {'available': False, 'title': '', 'presenter': ''}


def programme(station_id):
    station = next(s for s in STATIONS if s['id'] == station_id)
    cache = STATE / ('programme-' + station_id + '.json')
    now = datetime.now(timezone.utc)
    try:
        cached = json.loads(cache.read_text())
        age = now.timestamp() - cached['fetched']
        end = datetime.fromisoformat(cached['end']) if cached.get('end') else None
        if 0 <= age < 60 and (end is None or now < end):
            return cached
    except (OSError, ValueError, KeyError):
        pass
    request = urllib.request.Request(station['page'], headers={'User-Agent': 'Omarchy-ABC-Radio/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result = parse_programme(response.read().decode(), now)
    except Exception:
        result = {'available': False, 'title': '', 'presenter': ''}
    result.update({'station': station_id, 'fetched': now.timestamp()})
    temp = cache.with_suffix('.tmp')
    temp.write_text(json.dumps(result))
    temp.replace(cache)
    return result


if __name__ == '__main__':
    print(json.dumps(programme(sys.argv[1])))
