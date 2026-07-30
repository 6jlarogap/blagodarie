#!/usr/bin/env python3
"""Local HTTP STT adapter for Doverabot rental voice messages."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from aiohttp import web


HOST = "127.0.0.1"
PORT = 8766
CONTRACT = "organizm_hermes_v1"
MODEL_NAME = "medium"
DEFAULT_LANGUAGE = "ru"
MAX_FILE_SIZE = 25 * 1024 * 1024
REQUEST_TIMEOUT = 300
READ_CHUNK_SIZE = 1024 * 1024

SUPPORTED_FORMATS = {
    ".aac",
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".oga",
    ".ogg",
    ".wav",
    ".webm",
}
CONTENT_TYPE_SUFFIXES = {
    "audio/aac": ".aac",
    "audio/flac": ".flac",
    "audio/m4a": ".m4a",
    "audio/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
}

logger = logging.getLogger("rental_stt_adapter")


class RequestError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class SttService:
    def __init__(self, model_name=MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._busy = False

    @property
    def loaded(self):
        return self._model is not None

    @property
    def busy(self):
        return self._busy

    def try_reserve(self):
        if self._busy:
            return False
        self._busy = True
        return True

    def release(self):
        self._busy = False

    def _load_model(self):
        if self._model is not None:
            return self._model
        from faster_whisper import WhisperModel

        try:
            self._model = WhisperModel(self.model_name, device="auto", compute_type="auto")
        except Exception:
            logger.exception("Falling back to CPU int8 faster-whisper model")
            self._model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio_path, language):
        model = self._load_model()
        kwargs = {
            "beam_size": 5,
            "vad_filter": True,
        }
        if language:
            kwargs["language"] = language
        segments, info = model.transcribe(str(audio_path), **kwargs)
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        return {
            "transcript": transcript,
            "text": transcript,
            "language": getattr(info, "language", language),
            "duration": getattr(info, "duration", None),
            "model": self.model_name,
        }


def json_error(status, message):
    return web.json_response({"error": message}, status=status)


def _suffix_for_part(part):
    filename = part.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix:
        return suffix
    content_type = (part.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_SUFFIXES.get(content_type, ".ogg")


def _safe_language(value):
    value = (value or "").strip() or DEFAULT_LANGUAGE
    if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in value):
        raise RequestError(400, "language contains unsupported characters")
    return value


async def _part_text(part):
    value = await part.text()
    return (value or "").strip()


async def _save_voice_part(part):
    suffix = _suffix_for_part(part)
    if suffix not in SUPPORTED_FORMATS:
        raise RequestError(400, "unsupported audio format")

    tmp_dir = os.getenv("RENTAL_STT_TMP_DIR") or None
    handle = tempfile.NamedTemporaryFile(
        prefix="doverabot-rental-stt-",
        suffix=suffix,
        dir=tmp_dir,
        delete=False,
    )
    path = Path(handle.name)
    size = 0
    try:
        with handle:
            while True:
                chunk = await part.read_chunk(size=READ_CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise RequestError(413, "voice file is too large")
                handle.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if size == 0:
        path.unlink(missing_ok=True)
        raise RequestError(400, "voice file is empty")
    return path, size


async def parse_transcribe_request(request):
    if request.content_length and request.content_length > MAX_FILE_SIZE + READ_CHUNK_SIZE:
        raise RequestError(413, "request is too large")

    try:
        reader = await request.multipart()
    except Exception as exc:
        raise RequestError(400, "multipart form data is required") from exc

    contract = ""
    language = DEFAULT_LANGUAGE
    voice_path = None
    voice_size = 0

    async for part in reader:
        if part.name == "contract":
            contract = await _part_text(part)
        elif part.name == "language":
            language = _safe_language(await _part_text(part))
        elif part.name == "voice":
            if voice_path is not None:
                voice_path.unlink(missing_ok=True)
                raise RequestError(400, "only one voice file is supported")
            voice_path, voice_size = await _save_voice_part(part)
        else:
            await part.release()

    if contract != CONTRACT:
        if voice_path is not None:
            voice_path.unlink(missing_ok=True)
        raise RequestError(400, "unsupported contract")
    if voice_path is None:
        raise RequestError(400, "missing voice file")
    return voice_path, voice_size, language


async def healthz(request):
    service = request.app["stt_service"]
    return web.json_response({
        "ok": True,
        "busy": service.busy,
        "contract": CONTRACT,
        "language": DEFAULT_LANGUAGE,
        "loaded": service.loaded,
        "max_file_size": MAX_FILE_SIZE,
        "model": MODEL_NAME,
    })


async def transcribe(request):
    service = request.app["stt_service"]
    if not service.try_reserve():
        logger.warning("STT request rejected: transcription busy")
        return json_error(503, "transcription busy")

    voice_path = None
    worker = None
    try:
        voice_path, voice_size, language = await asyncio.wait_for(
            parse_transcribe_request(request),
            timeout=REQUEST_TIMEOUT,
        )
        worker = asyncio.create_task(
            asyncio.to_thread(service.transcribe, voice_path, language)
        )

        def finish(task):
            try:
                task.exception()
            except asyncio.CancelledError:
                pass
            finally:
                voice_path.unlink(missing_ok=True)
                service.release()

        worker.add_done_callback(finish)
        result = await asyncio.wait_for(
            asyncio.shield(worker),
            timeout=REQUEST_TIMEOUT,
        )
    except RequestError as exc:
        return json_error(exc.status, exc.message)
    except asyncio.TimeoutError:
        logger.warning("STT request timed out")
        return json_error(504, "transcription timed out")
    except Exception:
        logger.exception("STT request failed")
        return json_error(500, "transcription failed")
    finally:
        if worker is None:
            service.release()
            if voice_path is not None:
                voice_path.unlink(missing_ok=True)

    logger.info(
        "Transcribed rental voice: bytes=%s language=%s chars=%s",
        voice_size,
        result.get("language"),
        len(result.get("transcript") or ""),
    )
    return web.json_response(result)


def create_app():
    app = web.Application(client_max_size=MAX_FILE_SIZE + READ_CHUNK_SIZE)
    app["stt_service"] = SttService()
    app.router.add_get("/healthz", healthz)
    app.router.add_post("/transcribe", transcribe)
    return app


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    web.run_app(create_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
