# gte-ielts-stt

Transkrip rekaman Speaking GTE IELTS Centre memakai [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) di GitHub Actions. Gratis, tanpa API key.

- Dipicu oleh tugas terjadwal Claude (penilai AI GTE) lewat `workflow_dispatch`.
- Rekaman diambil dari signed URL Supabase (berlaku 2 jam) dan tidak disimpan di repo.
- Hasil (`transcripts.json`) diunggah sebagai artifact yang terhapus otomatis setelah 1 hari.
- Repo ini harus **private**: artifact berisi transkrip jawaban student.
