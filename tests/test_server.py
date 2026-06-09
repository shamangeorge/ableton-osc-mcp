from unittest.mock import patch

from ableton_osc_mcp import server


def test_main_swallows_keyboard_interrupt():
    with patch.object(server.mcp, "run", side_effect=KeyboardInterrupt):
        server.main()
