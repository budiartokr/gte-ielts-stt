"""GTE IELTS Centre: buat audio Listening dari naskah memakai Kokoro (Apache-2.0), lalu cek ulang dengan faster-whisper (MIT).

Input  : tts/set<N>-script.json  = {"set": N, "segments": [{"v": "<voice>", "t": "<text>"} | {"pause": <detik>}]}
Env    : SETS="3,4"
Output : out/set<N>.mp3 (mono 64 kbps), out/verify.json = {"set<N>": {"secs", "text", "segments":[{s,e,t}]}}
"""
import json, os, subprocess, sys, time

import numpy as np
import soundfile as sf
from kokoro import KPipeline

SR = 24000
NAR = "bm_george"
pipe = KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M")


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def synth(text, voice, speed):
    chunks = []
    for _, _, audio in pipe(text, voice=voice, speed=speed):
        if audio is None:
            continue
        a = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
        chunks.append(a.astype(np.float32))
        chunks.append(silence(0.12))
    return np.concatenate(chunks) if chunks else silence(0.1)


os.makedirs("out", exist_ok=True)
verify = {}
sets = [s.strip() for s in os.environ.get("SETS", "3,4").split(",") if s.strip()]
for n in sets:
    t0 = time.time()
    segs = json.load(open(f"tts/set{n}-script.json"))["segments"]
    out, prev = [silence(1.0)], None
    for s in segs:
        if "pause" in s:
            out.append(silence(float(s["pause"])))
            prev = None
            continue
        v = s["v"]
        nar = v == NAR
        out.append(silence(1.0 if (nar or prev == NAR) else 0.5))
        out.append(synth(s["t"], v, 0.92 if nar else 0.96))
        prev = v
    out.append(silence(1.5))
    wav = np.concatenate(out)
    peak = float(np.max(np.abs(wav))) or 1.0
    wav = (wav / peak * 0.89).astype(np.float32)
    sf.write(f"out/set{n}.wav", wav, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"out/set{n}.wav", "-ac", "1", "-ar", "24000",
                    "-codec:a", "libmp3lame", "-b:a", "64k", f"out/set{n}.mp3"], check=True)
    print(f"set{n}: {len(wav)/SR/60:.1f} min audio, synth {time.time()-t0:.0f}s", flush=True)

# Cek ulang: transkrip audio jadi teks lagi (Whisper) untuk dicocokkan dengan kunci jawaban
from faster_whisper import WhisperModel  # noqa: E402

model = WhisperModel(os.environ.get("MODEL", "small.en"), device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
for n in sets:
    t0 = time.time()
    segs, info = model.transcribe(f"out/set{n}.mp3", language="en", beam_size=5, vad_filter=False, condition_on_previous_text=False)
    segs = list(segs)
    verify[f"set{n}"] = {
        "secs": round(float(info.duration or 0), 1),
        "text": " ".join(s.text.strip() for s in segs),
        "segments": [{"s": round(s.start, 1), "e": round(s.end, 1), "t": s.text.strip()} for s in segs],
    }
    print(f"set{n}: whisper {time.time()-t0:.0f}s", flush=True)
json.dump(verify, open("out/verify.json", "w"), ensure_ascii=False)
print("done", file=sys.stderr)
