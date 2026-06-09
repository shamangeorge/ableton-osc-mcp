import os
import importlib
from unittest.mock import patch


def test_osc_client_uses_env_defaults():
    env = {
        "ABLETON_OSC_HOST": "host.docker.internal",
        "ABLETON_OSC_PORT": "12000",
        "ABLETON_OSC_REPLY_PORT": "12001",
    }
    with patch.dict(os.environ, env, clear=False):
        import ableton_osc_mcp.osc_client as osc_client

        osc_client = importlib.reload(osc_client)
        assert osc_client.REMOTE_HOST == "host.docker.internal"
        assert osc_client.REMOTE_PORT == 12000
        assert osc_client.LOCAL_PORT == 12001
