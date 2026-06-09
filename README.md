# ableton-osc-mcp

An MCP server that drives [Ableton Live](https://www.ableton.com/) over OSC, via
a [patched AbletonOSC](https://github.com/shamangeorge/AbletonOSC) control
surface (forked from [ideoforms/AbletonOSC](https://github.com/ideoforms/AbletonOSC)).

It exposes Live's full Object Model — reading/writing clip notes, device
parameters, the mixer, transport, the **browser** (load instruments/effects/drum
racks) and **arrangement** placement — as MCP tools, so an LLM agent can compose,
sound‑design and arrange a track end to end.

It runs as a standalone **streamable‑HTTP** service (no stdio), so it can be
restarted independently of the MCP client.

## How it works

```
MCP client (pi)  ──HTTP /mcp──▶  ableton-osc-mcp  ──OSC :11000/:11001──▶  AbletonOSC (in Live)
```

- The server sends OSC messages to AbletonOSC on UDP **11000** and listens for
  replies on **11001**.
- A companion fork of AbletonOSC adds browser access, arrangement clip placement
  and safe empty‑slot handling (see "Requirements").

## Requirements

1. **Ableton Live 11/12.**
2. **AbletonOSC** installed as a Control Surface, with the browser/arrangement
   additions from the fork:
   [github.com/shamangeorge/AbletonOSC](https://github.com/shamangeorge/AbletonOSC).
   - Copy the `AbletonOSC` folder into Live's MIDI Remote Scripts directory.
   - In Live: *Preferences → Link/Tempo/MIDI → Control Surface → AbletonOSC*
     (Input/Output = None). You should see
     `AbletonOSC: Listening for OSC on port 11000`.
3. **[mise](https://mise.jdx.dev/)**.

## Setup

This project uses **mise** for tool management and **uv** for the project
virtualenv/package workflow.

```bash
mise trust
mise install
uv sync
```

That installs the `python` and `uv` versions from `mise.toml`, then creates the
project virtualenv at `.venv/` via `uv`.

## Run

```bash
uv run ableton-osc-mcp
```

The server runs through the uv-managed project environment instead of calling a
hand-built virtualenv Python directly. Tool versions and env defaults both come
from `mise.toml`.

Default environment is defined in `mise.toml`:

| Variable                  | Default     | Meaning                       |
|---------------------------|-------------|-------------------------------|
| `UV_PROJECT_ENVIRONMENT`  | `.venv`     | uv-managed project environment |
| `ABLETON_OSC_MCP_HOST`    | `127.0.0.1` | HTTP bind host                |
| `ABLETON_OSC_MCP_PORT`    | `8765`      | HTTP bind port                |
| `ABLETON_OSC_HOST`        | `127.0.0.1` | AbletonOSC UDP host           |
| `ABLETON_OSC_PORT`        | `11000`     | AbletonOSC UDP port           |
| `ABLETON_OSC_REPLY_PORT`  | `11001`     | local UDP reply port          |

The MCP endpoint is then at `http://127.0.0.1:8765/mcp`.

## Docker

Build:

```bash
docker build -t ableton-osc-mcp .
```

Run:

```bash
docker run --rm \
  -p 8765:8765 \
  -p 11001:11001/udp \
  -e ABLETON_OSC_HOST=host.docker.internal \
  ableton-osc-mcp
```

Or with Docker Compose:

```bash
docker compose up --build
```

`compose.yaml` publishes MCP HTTP on `8765` and the OSC reply UDP port on
`11001`, with `ABLETON_OSC_HOST=host.docker.internal` by default.

On macOS and Docker Desktop, `host.docker.internal` lets container reach
Ableton Live running on host. If you use different network setup, override
`ABLETON_OSC_HOST`/`ABLETON_OSC_PORT`/`ABLETON_OSC_REPLY_PORT`.

## Connect from an MCP client

Add it as an HTTP server. For example, in an `mcp.json`:

```json
{
  "mcpServers": {
    "ableton-osc": {
      "type": "http",
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

## Tools

**Transport / song**
- `get_tempo`, `set_tempo`, `start_playback`, `stop_playback`
- `get_track_count`, `get_track_names`

**Tracks / mixer**
- `create_midi_track`, `create_audio_track`, `delete_track`, `set_track_name`
- `set_track_property` / `get_track_property` (mute, solo, arm, volume, panning)
- `set_track_send`
- `list_devices`

**Devices**
- `get_device_parameters`, `set_device_parameter`
- `get_device_parameter_value_string` (UI‑friendly, e.g. `"745 Hz"`)

**Clips / notes**
- `list_clips`, `create_clip`, `set_clip_name`, `fire_clip`, `stop_clip`
- `get_clip_notes` (paged so large clips don't overflow the UDP datagram)
- `add_clip_notes`, `remove_clip_notes` (whole clip or a beat range)
- `copy_clip_region`, `cut_clip_region` (slice a region into a new clip on the
  same track)

**Browser**
- `get_browser_tree`, `get_browser_items_at_path`, `load_browser_item`

**Arrangement**
- `duplicate_clip_to_arrangement`, `get_arrangement_clips`
- `set_arrangement_position`, `stop_all_clips`, `back_to_arranger`

## Development

Edit `src/ableton_osc_mcp/`, sync deps if needed, then restart the server:

```bash
uv sync
pkill -f ableton_osc_mcp.server
uv run ableton-osc-mcp
```

Live‑side (AbletonOSC) changes can be hot‑reloaded by sending `/live/api/reload`
to port 11000, or by re‑selecting the Control Surface in Live's preferences.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
