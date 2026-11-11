"""Edit This Video: speech-to-text worker. Runs inside the private tools folder (faster-whisper + numpy).

Reads a jobs file: {"model": "small.en", "prompt": "names", "jobs": [{"path": clip, "out": json}]}
Writes, for each clip, a list of words: [{"start": s, "end": e, "word": w, "p": prob}, ...] in clip seconds.
Audio is decoded with ffmpeg (not PyAV) so it works with any ffmpeg the person has.
"""
import json
import os
import subprocess
import sys
import time

import numpy as np
from faster_whisper import WhisperModel


def load_audio(path):
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
           "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def silences(audio, sr=16000):
    """Where the room is quiet: 20 ms windows quieter than the noise floor + 9 dB, at least 80 ms long."""
    win, hop = 320, 160
    n = max(0, (len(audio) - win) // hop)
    if n < 10:
        return {"floor": None, "threshold": None, "silences": []}
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    rms = np.sqrt((audio[idx] ** 2).mean(axis=1)) + 1e-9
    db = 20 * np.log10(rms)
    floor = float(np.percentile(db, 10))
    thr = min(floor + 9.0, -24.0)
    quiet = db < thr
    out, start = [], None
    for i, q in enumerate(quiet):
        t = (i * hop + win / 2) / sr
        if q and start is None:
            start = t
        elif not q and start is not None:
            if t - start >= 0.08:
                out.append([round(start, 3), round(t, 3)])
            start = None
    if start is not None:
        out.append([round(start, 3), round(len(audio) / sr, 3)])
    return {"floor": round(floor, 1), "threshold": round(thr, 1), "silences": out}


def main(jobs_file):
    cfg = json.load(open(jobs_file, encoding="utf-8"))
    print(f"Loading the speech model ({cfg['model']}; the first time it downloads, about 500 MB)...", flush=True)
    model = WhisperModel(cfg["model"], device="cpu", compute_type="int8")
    for job in cfg["jobs"]:
        t0 = time.time()
        audio = load_audio(job["path"])
        segs, _ = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=False,
                                   initial_prompt=cfg.get("prompt") or None, condition_on_previous_text=False)
        words = []
        for s in segs:
            for w in s.words or []:
                text = w.word.strip()
                if text:
                    words.append({"start": round(w.start, 3), "end": round(w.end, 3), "word": text,
                                  "p": round(w.probability, 2)})
        os.makedirs(os.path.dirname(job["out"]), exist_ok=True)
        with open(job["out"], "w", encoding="utf-8") as fh:
            json.dump(words, fh, ensure_ascii=False)
        with open(job["out"][:-5] + ".silence.json", "w", encoding="utf-8") as fh:
            json.dump(silences(audio), fh)
        print(f"  {os.path.basename(job['path'])}: {len(words)} words ({time.time() - t0:.0f} s)", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
