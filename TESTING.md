# Laporan Pengujian — ThermalDiagnose

**Tanggal:** 5 November 2026  
**Versi:** Tahap 1–7  

---

## 1. Pengujian otomatis mesin inferensi

Perintah:

```bash
python test_scenarios.py
```

| ID | Skenario | Diharapkan | Aktual | Status |
|----|----------|------------|--------|--------|
| S01 | Debu + udara panas | D01 | D01 | PASS |
| S02 | Kipas mati + panas + restart | D02 | D02 | PASS |
| S03 | CPU tinggi + kipas cepat + lag | D04 | D04 | PASS |
| S04 | Sofa + suhu ruangan tinggi | D05 | D05 | PASS |
| S05 | Lama tidak dibersihkan + panas ringan | D03 | D03 | PASS |
| S06 | Gejala minimal (G08 saja) | D06 | D06 | PASS |
| S07 | G01+G04+G12 (R16 AND) | D01 | D01 | PASS |
| S08 | Independensi merek G02+G04 | D01,D05 | D01,D05 | PASS |

**Hasil: 8/8 PASS**

Halaman live: `/skenario-uji`

---

## 2. Pemenuhan syarat UTS

| Syarat | Target | Aktual | Status |
|--------|--------|--------|--------|
| Gejala | ≥ 10 | 12 | OK |
| Kesimpulan antara | ≥ 3 | 3 | OK |
| Diagnosis akhir | ≥ 5 | 6 | OK |
| Aturan produksi | ≥ 15 | 17 | OK |
| Operator AND | Ada | Ada | OK |
| Operator OR | Ada | Ada (R17) | OK |
| Forward Chaining | Ya | Ya | OK |
| Explanation facility | Ya | Aturan + sumber di hasil | OK |
| Skenario uji | ≥ 5 | 8 | OK |

---

## 3. Pengujian fungsional (checklist manual)

| No | Skenario | Diharapkan | Cara verifikasi | Status |
|----|----------|------------|-----------------|--------|
| 1 | Pilih merek → keluarga → model → prosesor | Dropdown berjenjang terisi | Halaman Identifikasi | Manual |
| 2 | Simpan perangkat katalog | Redirect ke konsultasi + profil | Setelah submit katalog | Manual |
| 3 | Input manual merek+model | Profil mode=manual | Form manual | Manual |
| 4 | Model tidak di katalog | Gunakan input manual | Toggle "Tidak menemukan model" | Manual |
| 5 | Konsultasi tanpa gejala | Error / tidak submit | Form gejala kosong | Manual |
| 6 | Diagnosis + penjelasan aturan | Hasil + rule list | Setelah diagnosis | Manual |
| 7 | Konteks GPU dedicated | Catatan konteks, FC tidak berubah | Model dengan RTX | Manual |
| 8 | Riwayat tersimpan | Entri baru di /riwayat | Setelah diagnosis | Manual |
| 9 | Login admin | admin / admin123 | /admin/login | Manual |
| 10 | Admin tanpa login | Redirect login | /admin langsung | Manual |
| 11 | Filter katalog NVIDIA dedicated | Hanya model relevan | /katalog | Manual |
| 12 | Halaman sumber & basis pengetahuan | Konten tampil | /sumber, /basis-pengetahuan | Manual |
| 13 | Responsive mobile | Layout tidak rusak | DevTools mobile | Manual |
| 14 | Ganti perangkat | Session profil dihapus | Tombol ganti | Manual |
| 15 | 404 | Halaman error | URL sembarang | Manual |

---

## 4. Pengujian database

| Cek | Hasil (saat pengujian otomatis) |
|-----|----------------------------------|
| Merek | ≥ 30 (31) |
| Keluarga | ≥ 100 (107) |
| Model | ≥ 90 (94) |
| Prosesor | ≥ 150 (162) |
| GPU terstruktur | 9+ |
| Cooling templates | 6 |
| Sumber terdaftar | 15 |
| Seed idempotent | Ya (expand_catalog) |

---

## 5. Keamanan (tingkat development)

| Item | Status |
|------|--------|
| Admin session gate | Ada (`@admin_required`) |
| Password hash SHA-256 | Ada (ganti di production) |
| SQL parameterized | Ya |
| CSRF | Belum (catatan production) |
| Secret key env | `SECRET_KEY` env didukung |

---

## 6. Integritas diagnosis vs katalog

- Forward Chaining **hanya** memakai gejala + RULES.
- Profil merek/model/GPU/cooling ditampilkan sebagai **konteks**, tidak mengubah kode diagnosis.
- Dibuktikan S08: gejala sama → diagnosis sama (deterministik).

---

## 7. Cara menjalankan ulang pengujian

```bash
cd thermal_diagnose
python test_scenarios.py          # mesin inferensi
python -c "import database as d; d.init_db(); print(d.get_stats())"
python app.py                     # lalu buka /skenario-uji
```
