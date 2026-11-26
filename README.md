# gte-ielts-stt

Transkrip rekaman Speaking GTE IELTS Centre memakai [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) di GitHub Actions. Gratis, tanpa API key.

- Dipicu oleh tugas terjadwal Claude (penilai AI GTE) lewat `workflow_dispatch`.
- Rekaman diambil dari signed URL Supabase (berlaku 2 jam) dan tidak disimpan di repo.
- Hasil (`transcripts.json`) dikirim ke storage Supabase lewat signed upload URL, lalu dihapus setelah dibaca penilai AI. Tidak ada transkrip yang tersimpan di GitHub.
- Repo ini harus **private**: artifact berisi transkrip jawaban student.
