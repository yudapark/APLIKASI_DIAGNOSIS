# ThermalDiagnose

**Sistem Pakar Identifikasi Penyebab Laptop Overheating**  
Metode: **Forward Chaining** · Web (Flask) · Katalog multi-merek  

Mata kuliah: Sistem Pakar (UTS)

---

## Fitur

1. Identifikasi perangkat (katalog cascade + input manual)
2. Konsultasi gejala (12 gejala)
3. Diagnosis Forward Chaining + explanation facility
4. Konteks perangkat (GPU/cooling) **tanpa mengubah** logika diagnosis
5. Riwayat konsultasi
6. Katalog + filter (merek, tahun, GPU)
7. Registri sumber & status verifikasi
8. Basis pengetahuan publik + skenario uji live
9. Admin (login) CRUD katalog, GPU, cooling, sumber, verifikasi

---

## Menjalankan aplikasi

```bash
cd thermal_diagnose
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Buka: **http://127.0.0.1:5000**

| Akun | Username | Password |
|------|----------|----------|
| Admin (dev) | `admin` | `admin123` |

Ganti password/hash sebelum production.

---

## Struktur project

```
thermal_diagnose/
├── app.py                 # Flask routes
├── database.py            # SQLite layer, auth, history, GPU, cooling, sources
├── knowledge_base.py      # Gejala, kesimpulan, aturan IF-THEN
├── inference_engine.py    # Forward Chaining
├── catalog_seed.py        # Seed/perluasan katalog (idempotent)
├── test_scenarios.py      # 8 skenario uji formal
├── catalog.db             # Database (auto-init)
├── requirements.txt
├── README.md
├── TESTING.md             # Laporan pengujian
├── templates/             # HTML
└── static/                # style.css, app.js
```

---

## Alur pengguna

1. **Identifikasi** (`/`) — pilih merek → keluarga → model → prosesor, atau input manual
2. **Konsultasi** (`/konsultasi`) — centang gejala
3. **Diagnosis** — hasil + aturan terpicu + konteks perangkat
4. **Riwayat** — tersimpan otomatis

Menu pendukung: Katalog, Sumber, Basis Pengetahuan, Skenario Uji, Validasi, Admin.

---

## Basis pengetahuan (UTS)

| Komponen | Jumlah |
|----------|--------|
| Gejala | 12 (G01–G12) |
| Kesimpulan antara | 3 (I01–I03) |
| Diagnosis akhir | 6 (D01–D06) |
| Aturan | 17 (R01–R17) |
| Operator | AND + OR (R17) |
| Metode | Forward Chaining |
| Explanation | Ya |
| Skenario uji | 8 (semua PASS) |

Sumber aturan: Dell Support, ASUS Support, HP Support, Intel Support.

---

## Katalog (Tahap 2–5)

- **31 merek** · **107 keluarga** · **94 model** · **162 varian prosesor**
- GPU terstruktur + migrasi dari teks model
- Template cooling (tidak dikarang per-model)
- 15 sumber referensi kanonik
- Status verifikasi eksplisit; data seed ditandai perlu verifikasi

---

## Pengujian

```bash
python test_scenarios.py
```

Detail: lihat **TESTING.md**.  
UI live: `/skenario-uji`

---

## Panduan update database laptop

1. Login admin → tambah merek / keluarga / model / prosesor
2. Tambah GPU dan tautkan ke Model ID bila perlu
3. Profil pendinginan: hanya tautkan jika ada service manual / spek resmi; isi catatan sumber
4. Daftarkan sumber di Registri Sumber, lalu **Update Status Verifikasi Model**
5. Seed programatik: edit `catalog_seed.py` (helper idempotent), lalu restart app (`expand_catalog` dipanggil di `init_db`)

**Jangan** mengisi jumlah kipas/heatpipe tanpa dokumen resmi.

---

## Keamanan (catatan production)

- Ganti `SECRET_KEY` (env) dan password admin
- Pertimbangkan Flask-WTF (CSRF), HTTPS, rate limiting
- Admin hash saat ini SHA-256 sederhana (demo)

---

## Roadmap yang sudah selesai

| Tahap | Isi |
|-------|-----|
| 1 | Struktur Flask, admin login, riwayat, perbaikan aturan |
| 2 | Perluasan merek & keluarga |
| 3 | Tabel GPU + filter katalog |
| 4 | Template cooling + admin tautan |
| 5 | Registri sumber + verifikasi |
| 6 | Integrasi pakar, basis pengetahuan, skenario uji |
| 7 | Pengujian formal + dokumentasi akhir |

---

© 2026 ThermalDiagnose — Hasil diagnosis bersifat **identifikasi awal**, bukan pengganti pemeriksaan teknisi.


## Tahap 8 — CSV & Cetak

- Admin: **Ekspor katalog CSV**, **Unduh template**, **Impor CSV** (kolom: brand, family, model, …)
- Hasil diagnosis: tombol **Cetak / PDF** (layout print-friendly)
- Impor idempotent untuk brand/family; model dengan nama sama di keluarga yang sama tidak digandakan
