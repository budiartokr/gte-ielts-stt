# gte-ielts-stt

Transkrip rekaman Speaking GTE IELTS Centre memakai [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) di GitHub Actions. Gratis, tanpa API key.

- Dipicu oleh tugas terjadwal Claude (penilai AI GTE) lewat `workflow_dispatch`.
- Rekaman diambil dari signed URL Supabase (berlaku 2 jam) dan tidak disimpan di repo.
- Hasil (`transcripts.json`) dikirim ke storage Supabase lewat signed upload URL, lalu dihapus setelah dibaca penilai AI. Tidak ada transkrip yang tersimpan di GitHub.
- Repo ini harus **private**: artifact berisi transkrip jawaban student.

## tts (Listening latihan GTE)
Workflow `tts` membuat audio Listening dari naskah `tts/set<N>-script.json` memakai [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0, suara British), lalu mentranskrip ulang hasilnya dengan faster-whisper untuk verifikasi kunci jawaban. File (mp3, grafik Writing, data tes) dikirim ke storage Supabase lewat signed upload URL. Tanpa ElevenLabs, tanpa biaya.
