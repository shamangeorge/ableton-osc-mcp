# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-09

### Added
- MCP server that drives Ableton Live over OSC through an AbletonOSC control
  surface, running as a standalone streamable-HTTP service.
- Transport and song tools: `get_tempo`, `set_tempo`, `start_playback`,
  `stop_playback`, `get_track_count`, `get_track_names`.
- Track and mixer tools: `create_midi_track`, `create_audio_track`,
  `delete_track`, `set_track_name`, `set_track_property`, `get_track_property`,
  `set_track_send`, `list_devices`.
- Device parameter control: `get_device_parameters`, `set_device_parameter`,
  and `get_device_parameter_value_string` for UI-friendly values (e.g. "745 Hz").
- Clip and note tools: `list_clips`, `create_clip`, `set_clip_name`,
  `fire_clip`, `stop_clip`, `add_clip_notes`, and `get_clip_notes` (paged in
  time windows so large clips do not overflow the OSC UDP datagram).
- Region editing: `remove_clip_notes` (whole clip or a beat range),
  `copy_clip_region`, and `cut_clip_region` to slice a region of notes into a
  new clip on the same track.
- Browser tools: `get_browser_tree`, `get_browser_items_at_path`, and
  `load_browser_item` to browse and load instruments, effects and drum racks.
- Arrangement tools: `duplicate_clip_to_arrangement`, `get_arrangement_clips`,
  `set_arrangement_position`, `stop_all_clips`, and `back_to_arranger` for
  building a linear song from Session clips.
- `src/` package layout, `run-http.sh` launcher, and configurable bind host/port
  via `ABLETON_OSC_MCP_HOST` / `ABLETON_OSC_MCP_PORT`.

[Unreleased]: https://github.com/shamangeorge/ableton-osc-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/shamangeorge/ableton-osc-mcp/releases/tag/v0.1.0
