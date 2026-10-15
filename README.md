# ABC Radio TUI

A terminal app for listening to 19 ABC live radio stations: Brisbane and the other capital-city stations, Radio National, ABC NEWS, Classic, Jazz, Country, triple j, Double J, Unearthed, SPORT, Kids listen and Radio Australia.

It plays through its own private mpv instance and never touches other media players. On Omarchy it shares that player with the ABC Radio bar widget (`nick.abc-radio`), if you have it, so either one can control what's playing.

## Use

Run `abc-radio`, or open **ABC Radio** from the Omarchy app launcher (Super + Space).

| Key | Action |
| --- | --- |
| ↑ ↓ / j k, PgUp PgDn, g G | Move through stations |
| Enter / l, or click | Play the selected station |
| Space / p | Play or pause |
| s | Stop |
| + / - or → / ← | Volume up or down by 5% |
| o | Open the station's ABC listen page |
| q / Esc | Quit and keep playing |
| Q | Stop playback and quit |

The **On air now** panel shows the current programme, presenter and times in your local timezone. It refreshes every 30 seconds. In narrow terminals the layout stacks.

The last station and volume are remembered. Playback keeps going after you quit with `q`.

It also works as a plain command:

```bash
abc-radio play classic    # station ids are in stations.json
abc-radio toggle
abc-radio volume 40
abc-radio stop
abc-radio status          # JSON
```

## Install

Works on any Linux with **Python 3.8+** and **mpv** (curses is part of Python on Linux). `xdg-open` is optional, for the open-page key.

```bash
# Debian/Ubuntu: sudo apt install python3 mpv
# Fedora:        sudo dnf install python3 mpv
# Arch:          sudo pacman -S python mpv

git clone https://github.com/nickpstone/abc-radio-tui.git
cd abc-radio-tui
mkdir -p ~/.local/bin
ln -s "$PWD/abc-radio" ~/.local/bin/abc-radio   # ~/.local/bin must be on your PATH
abc-radio
```

On [Omarchy](https://omarchy.org), add it to the app launcher as a floating window:

```bash
omarchy tui install "ABC Radio" "$HOME/.local/bin/abc-radio" float "$PWD/abc-logo.svg"
```

Remove the launcher with `omarchy tui remove "ABC Radio"`.

## Notes

Player log: `~/.local/state/abc-radio/player.log` (respects `XDG_STATE_HOME`). If a stream drops, select the station again. Stream URLs come from the official ABC listen live pages and can be updated in `stations.json`. Some streams, especially sport, are geo-restricted to Australia.

Unofficial; no ABC affiliation. ABC owns its logo; the MIT license covers the code.
