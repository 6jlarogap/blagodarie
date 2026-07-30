import asyncio
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


try:
    import aiohttp  # noqa: F401
except ModuleNotFoundError:
    class Response:
        def __init__(self, data, status=200):
            self.status = status
            self.body = json.dumps(data).encode()

    sys.modules["aiohttp"] = types.SimpleNamespace(
        web=types.SimpleNamespace(json_response=Response)
    )


MODULE_PATH = Path(__file__).parents[1] / "rental_stt_adapter.py"
SPEC = importlib.util.spec_from_file_location("rental_stt_adapter", MODULE_PATH)
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class SttConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_keeps_slot_until_worker_finishes(self):
        service = adapter.SttService()
        started = asyncio.Event()
        finish = asyncio.Event()
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as handle:
            voice = Path(handle.name)

        async def blocking_to_thread(_function, _path, _language):
            started.set()
            await finish.wait()
            return {"transcript": "done"}

        request = type("Request", (), {"app": {"stt_service": service}})()

        async def parsed(_request):
            return voice, 1, "ru"

        with (
            mock.patch.object(adapter, "REQUEST_TIMEOUT", 0.01),
            mock.patch.object(adapter, "parse_transcribe_request", parsed),
            mock.patch.object(adapter.asyncio, "to_thread", blocking_to_thread),
        ):
            response = await adapter.transcribe(request)
            self.assertEqual(response.status, 504)
            self.assertTrue(started.is_set())
            self.assertTrue(service.busy)

            overloaded = await adapter.transcribe(request)
            self.assertEqual(overloaded.status, 503)

            finish.set()
            for _ in range(100):
                if not service.busy:
                    break
                await asyncio.sleep(0.001)

        self.assertFalse(service.busy)
        self.assertFalse(voice.exists())


if __name__ == "__main__":
    unittest.main()
