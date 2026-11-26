"""GTE IELTS Centre: transkrip rekaman Speaking dengan faster-whisper (MIT).

Input  : env JOB = {"items":[{"id":"<attempt>-p1","url":"<signed url>"}, ...]}
Output : out/transcripts.json = {"<id>": {text, secs, words, wpm, pauses_2s, longest_pause, fillers,
          avg_logprob, low_conf_words, segments:[...]}}
URL dan isi transkrip tidak pernah dicetak ke log.
"""
import json, os, re, subprocess, sys, time, urllib.request

from faster_whisper import WhisperModel

MODEL = os.environ.get("MODEL", "small.en")
FILLERS = re.compile(r"^(um+|uh+|erm*|er|ah+|hmm+|mm+|eh+)$", re.I)
# Prompt yang mendorong Whisper menuliskan filler (um, uh) alih-alih membuangnya
PROMPT = "Umm, let me think, uh... Well, I mean, like, hmm. Okay."

job = json.loads(os.environ["JOB"])
items = job.get("items", [])[:12]
os.makedirs("audio", exist_ok=True); os.makedirs("out", exist_ok=True)
model = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
res = {}
for it in items:
    iid = re.sub(r"[^A-Za-z0-9_-]", "", str(it.get("id", "")))[:80] or "x"
    t0 = time.time()
    try:
        raw = f"audio/{iid}.bin"; wav = f"audio/{iid}.wav"
        urllib.request.urlretrieve(it["url"], raw)
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", raw, "-ac", "1", "-ar", "16000", wav], check=True)
        segs, info = model.transcribe(wav, language="en", beam_size=5, word_timestamps=True,
                                      vad_filter=False, initial_prompt=PROMPT, condition_on_previous_text=False)
        segs = list(segs)
        words = [w for s in segs for w in (s.words or [])]
        text = " ".join(s.text.strip() for s in segs).strip()
        n = len(words); secs = float(info.duration or 0)
        speech = (words[-1].end - words[0].start) if n else 0.0
        gaps = [b.start - a.end for a, b in zip(words, words[1:])]
        fill = sum(1 for w in words if FILLERS.match(re.sub(r"[^\w]", "", w.word.strip())))
        lp = [s.avg_logprob for s in segs]
        res[iid] = {
            "text": text, "secs": round(secs, 1), "speech_secs": round(speech, 1), "words": n,
            "wpm": round(n / speech * 60, 1) if speech > 0 else 0,
            "pauses_2s": sum(1 for g in gaps if g > 2.0), "longest_pause": round(max(gaps), 1) if gaps else 0,
            "fillers": fill,
            "avg_logprob": round(sum(lp) / len(lp), 3) if lp else None,
            "low_conf_words": [w.word.strip() for w in words if w.probability < 0.45][:40],
            "segments": [{"s": round(s.start, 1), "e": round(s.end, 1), "t": s.text.strip()} for s in segs],
            "model": MODEL, "took": round(time.time() - t0, 1),
        }
        print(f"{iid}: ok ({n} words, {secs:.0f}s audio, {time.time()-t0:.0f}s)")
    except Exception as e:  # noqa: BLE001
        res[iid] = {"error": type(e).__name__}
        print(f"{iid}: error {type(e).__name__}", file=sys.stderr)
json.dump(res, open("out/transcripts.json", "w"), ensure_ascii=False)
