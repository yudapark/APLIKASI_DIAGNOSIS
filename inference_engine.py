from knowledge_base import RULES, KESIMPULAN_AKHIR, KESIMPULAN_ANTARA, GEJALA


def forward_chaining(gejala_dipilih):
    """
    Forward Chaining:
    - Fakta awal = gejala yang dipilih pengguna.
    - Setiap iterasi, periksa semua aturan. Jika kondisi terpenuhi,
      hasil aturan ditambahkan ke fakta (dan loop diulang).
    - Loop berhenti saat tidak ada fakta baru.
    - Jika tidak ada diagnosis akhir yang tercapai → tambahkan D06.
    """
    fakta = set(gejala_dipilih)
    aturan_dijalankan = []
    kesimpulan_akhir = set()

    perubahan = True
    while perubahan:
        perubahan = False

        for aturan in RULES:
            rule_id = aturan["id"]
            if any(r["id"] == rule_id for r in aturan_dijalankan):
                continue

            conditions = aturan["conditions"]
            operator = aturan["operator"]
            result = aturan["result"]

            if operator == "AND":
                terpenuhi = all(k in fakta for k in conditions)
            elif operator == "OR":
                terpenuhi = any(k in fakta for k in conditions)
            else:
                terpenuhi = False

            if terpenuhi:
                fakta.add(result)
                aturan_dijalankan.append(aturan)
                perubahan = True
                if result in KESIMPULAN_AKHIR:
                    kesimpulan_akhir.add(result)

    # Pisahkan fakta gejala (G) dan kesimpulan antara (I)
    fakta_gejala = sorted(k for k in fakta if k in GEJALA)
    fakta_antara = sorted(k for k in fakta if k in KESIMPULAN_ANTARA)

    # Susun hasil diagnosis
    hasil_diagnosis = []
    for kode in sorted(kesimpulan_akhir):
        d = KESIMPULAN_AKHIR[kode]
        hasil_diagnosis.append({
            "kode": kode,
            "nama": d["nama"],
            "penjelasan": d["penjelasan"],
            "solusi": d["solusi"],
            "sumber": d["sumber"],
            "tingkat": d["tingkat"],
        })

    # Jika tidak ada diagnosis akhir yang tercapai → D06
    if not hasil_diagnosis:
        d = KESIMPULAN_AKHIR["D06"]
        hasil_diagnosis.append({
            "kode": "D06",
            "nama": d["nama"],
            "penjelasan": d["penjelasan"],
            "solusi": d["solusi"],
            "sumber": d["sumber"],
            "tingkat": d["tingkat"],
        })

    return {
        "diagnosis": hasil_diagnosis,
        "aturan": aturan_dijalankan,
        "fakta": fakta_gejala,
        "kesimpulan_antara_tercapai": fakta_antara,
        "total_aturan": len(aturan_dijalankan),
    }
