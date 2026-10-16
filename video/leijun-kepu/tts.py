"""生成旁白 / 人物短句音频，并记录逐词时间戳用于字幕对齐。"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

from script import (CHARACTER_PITCH, CHARACTER_RATE, CHARACTER_VOICE, LINES,
                    NARRATOR_RATE, NARRATOR_VOICE)

OUT = Path(__file__).parent / "build" / "tts"


def probe_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)])
    return float(out)


async def synth(line_id, kind, text):
    mp3 = OUT / f"{line_id}.mp3"
    meta = OUT / f"{line_id}.json"
    if mp3.exists() and meta.exists() and json.loads(meta.read_text())["text"] == text:
        return json.loads(meta.read_text())
    if kind == "n":
        comm = edge_tts.Communicate(text, NARRATOR_VOICE, rate=NARRATOR_RATE,
                                    boundary="WordBoundary")
    else:
        comm = edge_tts.Communicate(text, CHARACTER_VOICE, rate=CHARACTER_RATE,
                                    pitch=CHARACTER_PITCH, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "t": chunk["offset"] / 1e7,
                    "d": chunk["duration"] / 1e7,
                    "text": chunk["text"],
                })
    info = {"id": line_id, "kind": kind, "text": text, "words": words,
            "duration": probe_duration(mp3)}
    meta.write_text(json.dumps(info, ensure_ascii=False, indent=1))
    return info


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for line_id, kind, start, text in LINES:
        info = await synth(line_id, kind, text)
        print(f"{line_id} start={start:6.2f} dur={info['duration']:5.2f} "
              f"end={start + info['duration']:6.2f}  {text}")


if __name__ == "__main__":
    asyncio.run(main())
