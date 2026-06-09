"""MCP server wrapping AbletonOSC.

Exposes AbletonOSC's full Live Object Model coverage (device parameters,
note read/write, track mixer, sends, transport) plus the ported browser
handlers (load instruments/effects/drum racks) as MCP tools.
"""

import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .osc_client import AbletonOSCClient

mcp = FastMCP(
    "ableton-osc",
    host=os.environ.get("ABLETON_OSC_MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("ABLETON_OSC_MCP_PORT", "8765")),
)
_client: Optional[AbletonOSCClient] = None


def osc() -> AbletonOSCClient:
    global _client
    if _client is None:
        _client = AbletonOSCClient()
    return _client


# --------------------------------------------------------------------------------
# Transport / song
# --------------------------------------------------------------------------------
@mcp.tool()
def get_tempo() -> float:
    """Get the current song tempo (BPM)."""
    return osc().query("/live/song/get/tempo")[0]


@mcp.tool()
def set_tempo(bpm: float) -> str:
    """Set the song tempo in BPM."""
    osc().send("/live/song/set/tempo", (bpm,))
    return "tempo set to %s" % bpm


@mcp.tool()
def start_playback() -> str:
    """Start song playback."""
    osc().send("/live/song/start_playing")
    return "playing"


@mcp.tool()
def stop_playback() -> str:
    """Stop song playback."""
    osc().send("/live/song/stop_playing")
    return "stopped"


@mcp.tool()
def get_track_count() -> int:
    """Number of tracks in the set."""
    return osc().query("/live/song/get/num_tracks")[0]


@mcp.tool()
def get_track_names() -> list:
    """List all track names."""
    return list(osc().query("/live/song/get/track_names"))


@mcp.tool()
def create_midi_track(index: int = -1) -> str:
    """Create a MIDI track at index (-1 = end)."""
    osc().send("/live/song/create_midi_track", (index,))
    return "created midi track"


@mcp.tool()
def create_audio_track(index: int = -1) -> str:
    """Create an audio track at index (-1 = end)."""
    osc().send("/live/song/create_audio_track", (index,))
    return "created audio track"


@mcp.tool()
def delete_track(track_index: int) -> str:
    """Delete a track by index."""
    osc().send("/live/song/delete_track", (track_index,))
    return "deleted track %d" % track_index


# --------------------------------------------------------------------------------
# Track mixer
# --------------------------------------------------------------------------------
@mcp.tool()
def set_track_name(track_index: int, name: str) -> str:
    """Rename a track."""
    osc().send("/live/track/set/name", (track_index, name))
    return "renamed track %d" % track_index


@mcp.tool()
def set_track_property(track_index: int, prop: str, value: float) -> str:
    """Set a track property.

    Supported: mute, solo, arm (0/1), volume (0-1), panning (-1..1).
    """
    addr = "/live/track/set/%s" % prop
    osc().send(addr, (track_index, value))
    return "%s.%s = %s" % (track_index, prop, value)


@mcp.tool()
def get_track_property(track_index: int, prop: str) -> float:
    """Get a track property: mute, solo, arm, volume, panning."""
    return osc().query("/live/track/get/%s" % prop, (track_index,))[1]


@mcp.tool()
def set_track_send(track_index: int, send_index: int, value: float) -> str:
    """Set a track's send level (0-1) to a return track."""
    osc().send("/live/track/set/send", (track_index, send_index, value))
    return "track %d send %d = %s" % (track_index, send_index, value)


# --------------------------------------------------------------------------------
# Devices & parameters
# --------------------------------------------------------------------------------
@mcp.tool()
def list_devices(track_index: int) -> list:
    """List devices on a track with their names."""
    names = osc().query("/live/track/get/devices/name", (track_index,))
    return [{"index": i, "name": n} for i, n in enumerate(names[1:])]


@mcp.tool()
def get_device_parameters(track_index: int, device_index: int) -> list:
    """List a device's parameters with index, name, value, min and max.

    Use this to discover what you can tweak (e.g. Reverb dry/wet, Compressor
    threshold/ratio, sidechain toggle) before calling set_device_parameter.
    """
    names = osc().query(
        "/live/device/get/parameters/name", (track_index, device_index)
    )[2:]
    values = osc().query(
        "/live/device/get/parameters/value", (track_index, device_index)
    )[2:]
    mins = osc().query("/live/device/get/parameters/min", (track_index, device_index))[
        2:
    ]
    maxes = osc().query("/live/device/get/parameters/max", (track_index, device_index))[
        2:
    ]
    out = []
    for i, name in enumerate(names):
        out.append(
            {
                "index": i,
                "name": name,
                "value": values[i] if i < len(values) else None,
                "min": mins[i] if i < len(mins) else None,
                "max": maxes[i] if i < len(maxes) else None,
            }
        )
    return out


@mcp.tool()
def set_device_parameter(
    track_index: int, device_index: int, parameter_index: int, value: float
) -> str:
    """Set a device parameter by index. Discover indices with get_device_parameters."""
    osc().send(
        "/live/device/set/parameter/value",
        (track_index, device_index, parameter_index, value),
    )
    return "device %d.%d param %d = %s" % (
        track_index,
        device_index,
        parameter_index,
        value,
    )


@mcp.tool()
def get_device_parameter_value_string(
    track_index: int, device_index: int, parameter_index: int
) -> str:
    """Get the UI-friendly string for a parameter value (e.g. '2500 Hz', '-12 dB')."""
    rv = osc().query(
        "/live/device/get/parameter/value_string",
        (track_index, device_index, parameter_index),
    )
    return rv[-1]


# --------------------------------------------------------------------------------
# Clips & notes
# --------------------------------------------------------------------------------
@mcp.tool()
def create_clip(track_index: int, clip_index: int, length: float = 4.0) -> str:
    """Create an empty MIDI clip in a clip slot."""
    osc().send("/live/clip_slot/create_clip", (track_index, clip_index, length))
    return "created clip %d:%d (%s beats)" % (track_index, clip_index, length)


@mcp.tool()
def list_clips(track_index: int) -> list:
    """List all Session clip slots on a track: which have clips, names, lengths.

    Use this to find where clips actually are instead of probing slots blindly.
    """
    names = osc().query("/live/track/get/clips/name", (track_index,))[1:]
    lengths = osc().query("/live/track/get/clips/length", (track_index,))[1:]
    out = []
    for i, name in enumerate(names):
        has = name is not None
        out.append(
            {
                "slot": i,
                "has_clip": has,
                "name": name if has else None,
                "length": lengths[i] if (has and i < len(lengths)) else None,
            }
        )
    return out


def _read_notes(
    track_index: int, clip_index: int, start: float = 0.0, span: float = None
) -> list:
    """Read notes from a clip, paging in time windows to stay under the UDP limit.

    If span is None, reads the whole clip. start/span define an absolute beat range.
    Returned note 'start' values are absolute (clip time).
    """
    if span is None:
        length = osc().query("/live/clip/get/length", (track_index, clip_index))[2]
        read_from, read_to = 0.0, length
    else:
        read_from, read_to = start, start + span
    window = 16.0
    notes = []
    t = read_from
    while t < read_to:
        w = min(window, read_to - t)
        rv = osc().query(
            "/live/clip/get/notes",
            (track_index, clip_index, 0, 127, t, w),
            timeout=8.0,
        )
        data = rv[2:]  # reply: track, clip, then groups of 5
        for i in range(0, len(data) - 4, 5):
            notes.append(
                {
                    "pitch": int(data[i]),
                    "start": data[i + 1],
                    "duration": data[i + 2],
                    "velocity": data[i + 3],
                    "mute": bool(data[i + 4]),
                }
            )
        t += w
    # de-dup (window boundaries can re-report a note) and sort
    seen = set()
    uniq = []
    for n in notes:
        key = (n["pitch"], round(n["start"], 4))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(n)
    uniq.sort(key=lambda n: (n["start"], n["pitch"]))
    return uniq


@mcp.tool()
def get_clip_notes(track_index: int, clip_index: int) -> list:
    """Read MIDI notes from a clip.

    Returns list of {pitch, start, duration, velocity, mute}.
    This is the capability the original ableton-mcp lacked -- you can now SEE
    existing melodies, not just write new ones.
    """
    return _read_notes(track_index, clip_index)


@mcp.tool()
def add_clip_notes(track_index: int, clip_index: int, notes: list) -> str:
    """Add MIDI notes to a clip.

    `notes` = list of {pitch, start, duration, velocity, mute}.
    """
    flat = []
    for n in notes:
        flat += [
            int(n["pitch"]),
            float(n["start"]),
            float(n["duration"]),
            int(n.get("velocity", 100)),
            int(bool(n.get("mute", False))),
        ]
    osc().send("/live/clip/add/notes", tuple([track_index, clip_index] + flat))
    return "added %d notes to %d:%d" % (len(notes), track_index, clip_index)


@mcp.tool()
def remove_clip_notes(
    track_index: int, clip_index: int, start: float = None, length: float = None
) -> str:
    """Remove notes from a clip.

    With no start/length: clears ALL notes. With start+length: removes only notes
    in that beat range (used for cutting a region).
    """
    if start is None or length is None:
        osc().send("/live/clip/remove/notes", (track_index, clip_index))
        return "cleared all notes in %d:%d" % (track_index, clip_index)
    osc().send(
        "/live/clip/remove/notes", (track_index, clip_index, 0, 127, start, length)
    )
    return "removed notes in %d:%d beats %s-%s" % (
        track_index,
        clip_index,
        start,
        start + length,
    )


@mcp.tool()
def copy_clip_region(
    track_index: int,
    src_clip_index: int,
    start: float,
    length: float,
    dest_clip_index: int,
    dest_offset: float = 0.0,
    dest_length: float = None,
) -> str:
    """Copy a beat-range of notes from one clip into a NEW clip on the same track.

    - start/length: the region (in beats) to copy from the source clip
    - dest_clip_index: an empty slot on the same track to create the new clip in
    - dest_offset: where in the new clip the region starts (default 0)
    - dest_length: new clip length (defaults to length + dest_offset)
    """
    region = _read_notes(track_index, src_clip_index, start, length)
    if dest_length is None:
        dest_length = length + dest_offset
    osc().send(
        "/live/clip_slot/create_clip", (track_index, dest_clip_index, dest_length)
    )
    import time as _t

    _t.sleep(0.2)
    flat = []
    for n in region:
        new_start = n["start"] - start + dest_offset
        flat += [
            int(n["pitch"]),
            float(new_start),
            float(n["duration"]),
            int(n["velocity"]),
            int(bool(n["mute"])),
        ]
    if flat:
        osc().send("/live/clip/add/notes", tuple([track_index, dest_clip_index] + flat))
    return "copied %d notes (beats %s-%s) -> clip %d:%d" % (
        len(region),
        start,
        start + length,
        track_index,
        dest_clip_index,
    )


@mcp.tool()
def cut_clip_region(
    track_index: int,
    src_clip_index: int,
    start: float,
    length: float,
    dest_clip_index: int,
) -> str:
    """Cut a beat-range: copy it into a new clip on the same track, then delete it
    from the source clip.
    """
    copy_clip_region(track_index, src_clip_index, start, length, dest_clip_index)
    osc().send(
        "/live/clip/remove/notes", (track_index, src_clip_index, 0, 127, start, length)
    )
    return "cut %s-%s from %d:%d into clip %d:%d" % (
        start,
        start + length,
        track_index,
        src_clip_index,
        track_index,
        dest_clip_index,
    )


@mcp.tool()
def set_clip_name(track_index: int, clip_index: int, name: str) -> str:
    """Rename a clip."""
    osc().send("/live/clip/set/name", (track_index, clip_index, name))
    return "renamed clip %d:%d" % (track_index, clip_index)


@mcp.tool()
def fire_clip(track_index: int, clip_index: int) -> str:
    """Start playing a clip."""
    osc().send("/live/clip/fire", (track_index, clip_index))
    return "fired %d:%d" % (track_index, clip_index)


@mcp.tool()
def stop_clip(track_index: int, clip_index: int) -> str:
    """Stop a clip."""
    osc().send("/live/clip/stop", (track_index, clip_index))
    return "stopped %d:%d" % (track_index, clip_index)


# --------------------------------------------------------------------------------
# Arrangement (build a linear song instead of launching session clips)
# --------------------------------------------------------------------------------
@mcp.tool()
def duplicate_clip_to_arrangement(
    track_index: int, session_clip_index: int, time: float
) -> str:
    """Copy a Session-view clip onto the Arrangement timeline at `time` (in beats).

    Lay your session clips along the arrangement to build a full song
    structure (intro/verse/chorus/drop), then play the arrangement linearly.
    """
    osc().query(
        "/live/track/duplicate_clip_to_arrangement",
        (track_index, session_clip_index, time),
    )
    return "placed track %d session clip %d at beat %s" % (
        track_index,
        session_clip_index,
        time,
    )


@mcp.tool()
def get_arrangement_clips(track_index: int) -> list:
    """List clips placed in the Arrangement for a track (name, length, start_time)."""
    names = osc().query("/live/track/get/arrangement_clips/name", (track_index,))[1:]
    lengths = osc().query("/live/track/get/arrangement_clips/length", (track_index,))[
        1:
    ]
    starts = osc().query(
        "/live/track/get/arrangement_clips/start_time", (track_index,)
    )[1:]
    return [
        {"name": n, "length": l, "start_time": s}
        for n, l, s in zip(names, lengths, starts)
    ]


@mcp.tool()
def set_arrangement_position(time: float) -> str:
    """Move the arrangement playhead to `time` (in beats)."""
    osc().send("/live/song/set/current_song_time", (time,))
    return "playhead at beat %s" % time


@mcp.tool()
def stop_all_clips() -> str:
    """Stop all launched Session clips (so the Arrangement plays without override)."""
    osc().send("/live/song/stop_all_clips")
    return "stopped all session clips"


@mcp.tool()
def back_to_arranger() -> str:
    """Clear the 'session overrides arrangement' state so the Arrangement plays back."""
    osc().send("/live/song/set/back_to_arranger", (0,))
    return "back to arranger"


# --------------------------------------------------------------------------------
# Browser (ported into AbletonOSC)
# --------------------------------------------------------------------------------
@mcp.tool()
def get_browser_tree(category_type: str = "all") -> dict:
    """Get browser categories. category_type: all, instruments, sounds, drums,
    audio_effects, midi_effects."""
    rv = osc().query("/live/browser/get/tree", (category_type,))
    return json.loads(rv[0])


@mcp.tool()
def get_browser_items_at_path(path: str) -> dict:
    """List browser items at a path, e.g. 'instruments' or 'audio_effects/Reverb'."""
    rv = osc().query("/live/browser/get/items_at_path", (path,))
    return json.loads(rv[0])


@mcp.tool()
def load_browser_item(track_index: int, uri: str) -> dict:
    """Load a browser item (instrument/effect/drum rack) onto a track by URI.

    Get URIs from get_browser_items_at_path.
    """
    rv = osc().query("/live/browser/load_item", (track_index, uri))
    return json.loads(rv[0])


def main():
    # HTTP-only: this server is always run as a standalone streamable-http
    # service so it can be restarted independently of any MCP client.
    # pi connects to http://127.0.0.1:8765/mcp (type: http). No stdio transport.
    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        return None


if __name__ == "__main__":
    main()
