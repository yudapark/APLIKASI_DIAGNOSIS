"""
Seed & perluasan katalog laptop (Tahap 2).

Prinsip:
- Hanya data yang dapat diverifikasi dari dokumentasi publik / situs resmi.
- Field GPU, cooling_info, generasi, tahun yang tidak pasti → None / "Informasi belum tersedia".
- Tidak mengarang jumlah kipas, heatpipe, atau spesifikasi teknis.

Sumber referensi umum per merek (halaman support / resmi):
- Axioo, Lenovo, ASUS, Acer, Dell, HP, MSI, Apple, Huawei, Samsung, Microsoft
- Toshiba, Sony, Razer, LG, Fujitsu, Panasonic, Framework, Xiaomi, Honor
- Gigabyte, Infinix, Advan, Zyrex, Chuwi, TECNO, Medion, Clevo, System76

CATATAN:
Katalog bersifat contoh yang terus diperluas. Model tanpa detail prosesor
tidak diisi spekulatif. Gunakan status verifikasi di database.
"""

from datetime import date

TODAY = date.today().isoformat()


def _get_or_create_brand(conn, name, slug):
    row = conn.execute("SELECT id FROM brands WHERE slug = ?", (slug,)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO brands (name, slug) VALUES (?, ?)", (name, slug))
    return cur.lastrowid


def _get_or_create_family(conn, brand_id, name):
    row = conn.execute(
        "SELECT id FROM product_families WHERE brand_id = ? AND name = ?",
        (brand_id, name),
    ).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO product_families (brand_id, name) VALUES (?, ?)",
        (brand_id, name),
    )
    return cur.lastrowid


def _model_exists(conn, family_id, name):
    row = conn.execute(
        "SELECT id FROM laptop_models WHERE family_id = ? AND name = ?",
        (family_id, name),
    ).fetchone()
    return row[0] if row else None


def _add_model(conn, family_id, name, generation=None, year=None, gpu=None,
               cooling_info=None, notes=None, model_number=None):
    existing = _model_exists(conn, family_id, name)
    if existing:
        return existing
    cur = conn.execute(
        """INSERT INTO laptop_models
           (family_id, name, generation, year, gpu, cooling_info, notes,
            model_number, verification_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (family_id, name, generation, year, gpu, cooling_info, notes,
         model_number, "Contoh seed — perlu verifikasi detail"),
    )
    return cur.lastrowid


def _add_procs(conn, model_id, processors):
    for p in processors:
        exists = conn.execute(
            "SELECT 1 FROM processor_variants WHERE model_id = ? AND processor = ?",
            (model_id, p),
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO processor_variants (model_id, processor) VALUES (?, ?)",
                (model_id, p),
            )


def _add_ref(conn, model_id, source_name, url, source_type="produsen"):
    exists = conn.execute(
        "SELECT 1 FROM device_references WHERE model_id = ? AND source_name = ?",
        (model_id, source_name),
    ).fetchone()
    if not exists:
        conn.execute(
            """INSERT INTO device_references
               (model_id, source_name, url, updated_at, source_type)
               VALUES (?, ?, ?, ?, ?)""",
            (model_id, source_name, url, TODAY, source_type),
        )


def seed_catalog(conn):
    """Seed awal (dipanggil jika brands kosong). Idempotent helpers dipakai."""
    expand_catalog(conn)


def expand_catalog(conn):
    """
    Perluasan katalog Tahap 2.
    Aman dipanggil berulang: tidak menduplikasi brand/family/model yang sudah ada.
    """
    # ============================================
    # 1. AXIOO
    # ============================================
    b = _get_or_create_brand(conn, "Axioo", "axioo")
    f_hype = _get_or_create_family(conn, b, "Hype")
    f_mybook = _get_or_create_family(conn, b, "MyBook")
    f_pongo = _get_or_create_family(conn, b, "Pongo")
    f_slimbook = _get_or_create_family(conn, b, "Slimbook")

    m = _add_model(conn, f_hype, "Hype 3 Gen 12", generation="Gen 12", year=2023)
    _add_procs(conn, m, ["Intel Core i3-1215U", "Intel Core i5-1235U"])
    _add_ref(conn, m, "Axioo Official", "https://axiooworld.com/")

    m = _add_model(conn, f_hype, "Hype 5 Gen 13", generation="Gen 13", year=2024)
    _add_procs(conn, m, ["Intel Core i5-1335U", "Intel Core i7-1355U"])
    _add_ref(conn, m, "Axioo Official", "https://axiooworld.com/")

    m = _add_model(conn, f_mybook, "MyBook 14", year=2023)
    _add_procs(conn, m, ["Intel Celeron N4020"])
    _add_ref(conn, m, "Axioo Official", "https://axiooworld.com/")

    m = _add_model(conn, f_pongo, "Pongo 725", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1135G7"])
    _add_ref(conn, m, "Axioo Official", "https://axiooworld.com/")

    # ============================================
    # 2. LENOVO
    # ============================================
    b = _get_or_create_brand(conn, "Lenovo", "lenovo")
    f_tp = _get_or_create_family(conn, b, "ThinkPad")
    f_ip = _get_or_create_family(conn, b, "IdeaPad")
    f_tb = _get_or_create_family(conn, b, "ThinkBook")
    f_yg = _get_or_create_family(conn, b, "Yoga")
    f_leg = _get_or_create_family(conn, b, "Legion")
    f_loq = _get_or_create_family(conn, b, "LOQ")
    f_v = _get_or_create_family(conn, b, "V Series")
    f_ideacentre = _get_or_create_family(conn, b, "IdeaCentre")  # desktop ref, jarang laptop

    m = _add_model(conn, f_tp, "T480s", year=2018, gpu="Intel UHD 620")
    _add_procs(conn, m, ["Intel Core i5-8250U", "Intel Core i7-8550U"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_tp, "T14 Gen 3", generation="Gen 3", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1235U", "Intel Core i7-1255U", "AMD Ryzen 5 6650U"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_tp, "X1 Carbon Gen 11", generation="Gen 11", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1335U", "Intel Core i7-1355U"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_tp, "X1 Carbon Gen 9", generation="Gen 9", year=2021)
    _add_procs(conn, m, ["Intel Core i5-1135G7", "Intel Core i7-1165G7"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_ip, "IdeaPad Slim 3 14", year=2023)
    _add_procs(conn, m, ["Intel Core i3-1215U", "AMD Ryzen 5 7520U"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_ip, "IdeaPad 3 15", year=2021)
    _add_procs(conn, m, ["Intel Core i3-1115G4", "AMD Ryzen 5 5500U"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_tb, "ThinkBook 14 G4+", generation="G4", year=2022)
    _add_procs(conn, m, ["Intel Core i5-12500H", "Intel Core i7-12700H"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_yg, "Yoga Slim 7", year=2023)
    _add_procs(conn, m, ["Intel Core i7-1360P"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_leg, "Legion 5 Pro", year=2023, gpu="NVIDIA RTX 4060")
    _add_procs(conn, m, ["AMD Ryzen 7 7745HX", "Intel Core i7-13700HX"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_leg, "Legion 5 15", year=2021, gpu="NVIDIA RTX 3060")
    _add_procs(conn, m, ["AMD Ryzen 5 5600H", "Intel Core i5-11400H"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    m = _add_model(conn, f_loq, "LOQ 15IRH8", year=2023, gpu="NVIDIA RTX 4050")
    _add_procs(conn, m, ["Intel Core i5-13500H", "Intel Core i7-13620H"])
    _add_ref(conn, m, "Lenovo Support", "https://pcsupport.lenovo.com/id/id/")

    # ============================================
    # 3. ASUS
    # ============================================
    b = _get_or_create_brand(conn, "ASUS", "asus")
    f_vb = _get_or_create_family(conn, b, "VivoBook")
    f_zb = _get_or_create_family(conn, b, "ZenBook")
    f_eb = _get_or_create_family(conn, b, "ExpertBook")
    f_rog = _get_or_create_family(conn, b, "ROG")
    f_tuf = _get_or_create_family(conn, b, "TUF Gaming")
    f_proart = _get_or_create_family(conn, b, "ProArt")
    f_chromebook = _get_or_create_family(conn, b, "Chromebook")

    m = _add_model(conn, f_vb, "VivoBook 14 A1404ZA", year=2023)
    _add_procs(conn, m, ["Intel Core i3-1215U", "Intel Core i5-1235U"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_vb, "VivoBook 15 X1504VA", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1335U", "Intel Core i7-1355U"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_zb, "ZenBook 14 OLED UX3402", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1240P", "Intel Core i7-1260P"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_eb, "ExpertBook B1 B1400", year=2021)
    _add_procs(conn, m, ["Intel Core i3-1115G4", "Intel Core i5-1135G7"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_rog, "ROG Zephyrus G14 GA402", year=2023, gpu="NVIDIA RTX 4060")
    _add_procs(conn, m, ["AMD Ryzen 7 7735HS", "AMD Ryzen 9 7940HS"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_rog, "ROG Strix G15 G513", year=2021, gpu="NVIDIA RTX 3060")
    _add_procs(conn, m, ["AMD Ryzen 7 5800H", "AMD Ryzen 9 5900HX"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_tuf, "TUF Gaming F15 FX506", year=2022, gpu="NVIDIA RTX 3050")
    _add_procs(conn, m, ["Intel Core i5-11400H", "Intel Core i7-11800H"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_tuf, "TUF Gaming A15 FA506", year=2021, gpu="NVIDIA RTX 3050")
    _add_procs(conn, m, ["AMD Ryzen 5 4600H", "AMD Ryzen 7 4800H"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    m = _add_model(conn, f_proart, "ProArt Studiobook 16", year=2023)
    _add_procs(conn, m, ["Intel Core i9-13980HX"])
    _add_ref(conn, m, "ASUS Support", "https://www.asus.com/id/support/")

    # ============================================
    # 4. ACER
    # ============================================
    b = _get_or_create_brand(conn, "Acer", "acer")
    f_asp = _get_or_create_family(conn, b, "Aspire")
    f_sw = _get_or_create_family(conn, b, "Swift")
    f_tm = _get_or_create_family(conn, b, "TravelMate")
    f_ni = _get_or_create_family(conn, b, "Nitro")
    f_pr = _get_or_create_family(conn, b, "Predator")
    f_ex = _get_or_create_family(conn, b, "Extensa")
    f_chromebook = _get_or_create_family(conn, b, "Chromebook")

    m = _add_model(conn, f_asp, "Aspire 5 A515-58M", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1335U", "Intel Core i7-1355U"])
    _add_ref(conn, m, "Acer Support", "https://www.acer.com/id-id/support/product-support/")

    m = _add_model(conn, f_asp, "Aspire 3 A314-36M", year=2023)
    _add_procs(conn, m, ["Intel Celeron N100", "Intel Core i3-N305"])
    _add_ref(conn, m, "Acer Support", "https://www.acer.com/id-id/support/product-support/")

    m = _add_model(conn, f_sw, "Swift Go 14 SFG14-71", year=2023)
    _add_procs(conn, m, ["Intel Core i5-13500H", "Intel Core i7-13700H"])
    _add_ref(conn, m, "Acer Support", "https://www.acer.com/id-id/support/product-support/")

    m = _add_model(conn, f_tm, "TravelMate P2 TMP214-54", year=2022)
    _add_procs(conn, m, ["Intel Core i3-1215U", "Intel Core i5-1235U"])
    _add_ref(conn, m, "Acer Support", "https://www.acer.com/id-id/support/product-support/")

    m = _add_model(conn, f_ni, "Nitro V 15 ANV15-51", year=2023, gpu="NVIDIA RTX 4050")
    _add_procs(conn, m, ["Intel Core i5-13420H", "Intel Core i7-13620H"])
    _add_ref(conn, m, "Acer Support", "https://www.acer.com/id-id/support/product-support/")

    m = _add_model(conn, f_pr, "Predator Helios Neo 16 PHN16", year=2023, gpu="NVIDIA RTX 4060")
    _add_procs(conn, m, ["Intel Core i7-13700HX", "Intel Core i9-13900HX"])
    _add_ref(conn, m, "Acer Support", "https://www.acer.com/id-id/support/product-support/")

    m = _add_model(conn, f_ex, "Extensa 15 EX215", year=2022)
    _add_procs(conn, m, ["Intel Core i3-1115G4", "Intel Core i5-1135G7"])
    _add_ref(conn, m, "Acer Support", "https://www.acer.com/id-id/support/product-support/")

    # ============================================
    # 5. HP
    # ============================================
    b = _get_or_create_brand(conn, "HP", "hp")
    f_pav = _get_or_create_family(conn, b, "Pavilion")
    f_pb = _get_or_create_family(conn, b, "ProBook")
    f_eb = _get_or_create_family(conn, b, "EliteBook")
    f_en = _get_or_create_family(conn, b, "Envy")
    f_vic = _get_or_create_family(conn, b, "Victus")
    f_om = _get_or_create_family(conn, b, "OMEN")
    f_sp = _get_or_create_family(conn, b, "Spectre")
    f_zb = _get_or_create_family(conn, b, "ZBook")
    f_chromebook = _get_or_create_family(conn, b, "Chromebook")

    m = _add_model(conn, f_pav, "Pavilion 14-dv2000", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1235U", "Intel Core i7-1255U"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    m = _add_model(conn, f_pb, "ProBook 440 G9", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1235U", "Intel Core i7-1255U"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    m = _add_model(conn, f_eb, "EliteBook 840 G9", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1245U", "Intel Core i7-1265U"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    m = _add_model(conn, f_en, "Envy x360 13-bf", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1335U", "Intel Core i7-1355U"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    m = _add_model(conn, f_vic, "Victus 15-fa1", year=2023, gpu="NVIDIA RTX 4050")
    _add_procs(conn, m, ["Intel Core i5-13500H", "Intel Core i7-13700H"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    m = _add_model(conn, f_om, "OMEN 16-wf0", year=2023, gpu="NVIDIA RTX 4070")
    _add_procs(conn, m, ["Intel Core i7-13700HX", "Intel Core i9-13900HX"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    m = _add_model(conn, f_sp, "Spectre x360 14", year=2023)
    _add_procs(conn, m, ["Intel Core Ultra 7 155H"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    m = _add_model(conn, f_zb, "ZBook Firefly 14 G10", year=2023)
    _add_procs(conn, m, ["Intel Core i7-1355U"])
    _add_ref(conn, m, "HP Support", "https://support.hp.com/")

    # ============================================
    # 6. DELL
    # ============================================
    b = _get_or_create_brand(conn, "Dell", "dell")
    f_insp = _get_or_create_family(conn, b, "Inspiron")
    f_lat = _get_or_create_family(conn, b, "Latitude")
    f_xps = _get_or_create_family(conn, b, "XPS")
    f_vos = _get_or_create_family(conn, b, "Vostro")
    f_aw = _get_or_create_family(conn, b, "Alienware")
    f_prec = _get_or_create_family(conn, b, "Precision")
    f_g = _get_or_create_family(conn, b, "G Series")

    m = _add_model(conn, f_insp, "Inspiron 14 5430", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1340P", "Intel Core i7-1360P"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    m = _add_model(conn, f_lat, "Latitude 5440", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1345U", "Intel Core i7-1365U"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    m = _add_model(conn, f_xps, "XPS 13 9315", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1230U", "Intel Core i7-1250U"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    m = _add_model(conn, f_xps, "XPS 15 9530", year=2023, gpu="NVIDIA RTX 4050")
    _add_procs(conn, m, ["Intel Core i7-13700H"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    m = _add_model(conn, f_vos, "Vostro 3520", year=2022)
    _add_procs(conn, m, ["Intel Core i3-1215U", "Intel Core i5-1235U"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    m = _add_model(conn, f_aw, "Alienware m16 R1", year=2023, gpu="NVIDIA RTX 4070")
    _add_procs(conn, m, ["Intel Core i7-13700HX", "Intel Core i9-13900HX"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    m = _add_model(conn, f_g, "G15 5530", year=2023, gpu="NVIDIA RTX 4050")
    _add_procs(conn, m, ["Intel Core i5-13450HX", "Intel Core i7-13650HX"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    m = _add_model(conn, f_prec, "Precision 5680", year=2023)
    _add_procs(conn, m, ["Intel Core i7-13800H"])
    _add_ref(conn, m, "Dell Support", "https://www.dell.com/support/home/en-id/Products")

    # ============================================
    # 7. MSI
    # ============================================
    b = _get_or_create_brand(conn, "MSI", "msi")
    f_mod = _get_or_create_family(conn, b, "Modern")
    f_pre = _get_or_create_family(conn, b, "Prestige")
    f_thin = _get_or_create_family(conn, b, "Thin")
    f_cyb = _get_or_create_family(conn, b, "Cyborg")
    f_kat = _get_or_create_family(conn, b, "Katana")
    f_st = _get_or_create_family(conn, b, "Stealth")
    f_rai = _get_or_create_family(conn, b, "Raider")
    f_sword = _get_or_create_family(conn, b, "Sword")
    f_summit = _get_or_create_family(conn, b, "Summit")
    f_titan = _get_or_create_family(conn, b, "Titan")

    m = _add_model(conn, f_mod, "Modern 14 C12M", year=2022)
    _add_procs(conn, m, ["Intel Core i5-12450H", "Intel Core i7-12650H"])
    _add_ref(conn, m, "MSI Support", "https://www.msi.com/support")

    m = _add_model(conn, f_pre, "Prestige 14Evo A12M", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1240P", "Intel Core i7-1280P"])
    _add_ref(conn, m, "MSI Support", "https://www.msi.com/support")

    m = _add_model(conn, f_thin, "Thin GF63 12UC", year=2022, gpu="NVIDIA RTX 3050")
    _add_procs(conn, m, ["Intel Core i5-12450H", "Intel Core i7-12650H"])
    _add_ref(conn, m, "MSI Support", "https://www.msi.com/support")

    m = _add_model(conn, f_cyb, "Cyborg 15 A12VF", year=2023, gpu="NVIDIA RTX 4060")
    _add_procs(conn, m, ["Intel Core i5-12450H", "Intel Core i7-12650H"])
    _add_ref(conn, m, "MSI Support", "https://www.msi.com/support")

    m = _add_model(conn, f_kat, "Katana 15 B13V", year=2023, gpu="NVIDIA RTX 4050")
    _add_procs(conn, m, ["Intel Core i5-13420H", "Intel Core i7-13620H"])
    _add_ref(conn, m, "MSI Support", "https://www.msi.com/support")

    m = _add_model(conn, f_st, "Stealth 16 Studio A13V", year=2023, gpu="NVIDIA RTX 4070")
    _add_procs(conn, m, ["Intel Core i7-13700H", "Intel Core i9-13900H"])
    _add_ref(conn, m, "MSI Support", "https://www.msi.com/support")

    m = _add_model(conn, f_rai, "Raider GE78 HX", year=2023, gpu="NVIDIA RTX 4080")
    _add_procs(conn, m, ["Intel Core i9-13980HX"])
    _add_ref(conn, m, "MSI Support", "https://www.msi.com/support")

    # ============================================
    # 8. APPLE
    # ============================================
    b = _get_or_create_brand(conn, "Apple", "apple")
    f_mba = _get_or_create_family(conn, b, "MacBook Air")
    f_mbp = _get_or_create_family(conn, b, "MacBook Pro")
    f_mb = _get_or_create_family(conn, b, "MacBook")  # seri lama

    m = _add_model(conn, f_mba, "MacBook Air M1 (2020)", generation="M1", year=2020)
    _add_procs(conn, m, ["Apple M1"])
    _add_ref(conn, m, "Apple Support", "https://support.apple.com/id-id/")

    m = _add_model(conn, f_mba, "MacBook Air M2 (2022)", generation="M2", year=2022)
    _add_procs(conn, m, ["Apple M2"])
    _add_ref(conn, m, "Apple Support", "https://support.apple.com/id-id/")

    m = _add_model(conn, f_mba, "MacBook Air M3 (2024)", generation="M3", year=2024)
    _add_procs(conn, m, ["Apple M3"])
    _add_ref(conn, m, "Apple Support", "https://support.apple.com/id-id/")

    m = _add_model(conn, f_mbp, "MacBook Pro 14 M3 (2023)", generation="M3", year=2023)
    _add_procs(conn, m, ["Apple M3", "Apple M3 Pro", "Apple M3 Max"])
    _add_ref(conn, m, "Apple Support", "https://support.apple.com/id-id/")

    m = _add_model(conn, f_mbp, "MacBook Pro 13 M2 (2022)", generation="M2", year=2022)
    _add_procs(conn, m, ["Apple M2"])
    _add_ref(conn, m, "Apple Support", "https://support.apple.com/id-id/")

    m = _add_model(conn, f_mbp, "MacBook Pro 16 (2019)", generation="Intel", year=2019, gpu="AMD Radeon Pro 5300M")
    _add_procs(conn, m, ["Intel Core i7-9750H", "Intel Core i9-9880H"])
    _add_ref(conn, m, "Apple Support", "https://support.apple.com/id-id/")

    # ============================================
    # 9. HUAWEI
    # ============================================
    b = _get_or_create_brand(conn, "Huawei", "huawei")
    f_mb = _get_or_create_family(conn, b, "MateBook")
    f_mbd = _get_or_create_family(conn, b, "MateBook D")
    f_mbx = _get_or_create_family(conn, b, "MateBook X")

    m = _add_model(conn, f_mb, "MateBook 14 (2023)", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1340P", "Intel Core i7-1360P"])
    _add_ref(conn, m, "Huawei Support", "https://consumer.huawei.com/id/support/product/")

    m = _add_model(conn, f_mbd, "MateBook D 14 (2023)", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1240P", "Intel Core i7-1260P"])
    _add_ref(conn, m, "Huawei Support", "https://consumer.huawei.com/id/support/product/")

    m = _add_model(conn, f_mbx, "MateBook X Pro (2023)", year=2023)
    _add_procs(conn, m, ["Intel Core i7-1360P"])
    _add_ref(conn, m, "Huawei Support", "https://consumer.huawei.com/id/support/product/")

    # ============================================
    # 10. SAMSUNG
    # ============================================
    b = _get_or_create_brand(conn, "Samsung", "samsung")
    f_gb = _get_or_create_family(conn, b, "Galaxy Book")

    m = _add_model(conn, f_gb, "Galaxy Book3 Pro 14", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1340P", "Intel Core i7-1360P"])
    _add_ref(conn, m, "Samsung Support", "https://www.samsung.com/id/support/")

    m = _add_model(conn, f_gb, "Galaxy Book3 15", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1335U", "Intel Core i7-1355U"])
    _add_ref(conn, m, "Samsung Support", "https://www.samsung.com/id/support/")

    m = _add_model(conn, f_gb, "Galaxy Book4 Pro", year=2024)
    _add_procs(conn, m, ["Intel Core Ultra 7 155H"])
    _add_ref(conn, m, "Samsung Support", "https://www.samsung.com/id/support/")

    # ============================================
    # 11. MICROSOFT
    # ============================================
    b = _get_or_create_brand(conn, "Microsoft", "microsoft")
    f_sl = _get_or_create_family(conn, b, "Surface Laptop")
    f_sp = _get_or_create_family(conn, b, "Surface Pro")
    f_sb = _get_or_create_family(conn, b, "Surface Book")
    f_sg = _get_or_create_family(conn, b, "Surface Go")

    m = _add_model(conn, f_sl, "Surface Laptop 5 (13.5)", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1235U", "Intel Core i7-1255U"])
    _add_ref(conn, m, "Microsoft Support", "https://support.microsoft.com/")

    m = _add_model(conn, f_sl, "Surface Laptop 6", year=2024)
    _add_procs(conn, m, ["Intel Core Ultra 5 135H", "Intel Core Ultra 7 165H"])
    _add_ref(conn, m, "Microsoft Support", "https://support.microsoft.com/")

    m = _add_model(conn, f_sp, "Surface Pro 9", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1235U", "Intel Core i7-1255U"])
    _add_ref(conn, m, "Microsoft Support", "https://support.microsoft.com/")

    # ============================================
    # 12. GIGABYTE
    # ============================================
    b = _get_or_create_brand(conn, "Gigabyte", "gigabyte")
    f_aero = _get_or_create_family(conn, b, "AERO")
    f_aorus = _get_or_create_family(conn, b, "AORUS")
    f_gmg = _get_or_create_family(conn, b, "Gaming")
    f_g5 = _get_or_create_family(conn, b, "G5")

    m = _add_model(conn, f_aero, "AERO 14 OLED", year=2023, gpu="NVIDIA RTX 4050")
    _add_procs(conn, m, ["Intel Core i7-13700H"])
    _add_ref(conn, m, "Gigabyte Support", "https://www.gigabyte.com/Support")

    m = _add_model(conn, f_aorus, "AORUS 15 BSF", year=2023, gpu="NVIDIA RTX 4070")
    _add_procs(conn, m, ["Intel Core i7-13700H"])
    _add_ref(conn, m, "Gigabyte Support", "https://www.gigabyte.com/Support")

    # ============================================
    # 13–15. Lokal Indonesia
    # ============================================
    b = _get_or_create_brand(conn, "Infinix", "infinix")
    f_inb = _get_or_create_family(conn, b, "INBook")
    m = _add_model(conn, f_inb, "INBook X2", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1035G1", "Intel Core i7-1065G7"])
    _add_ref(conn, m, "Infinix Official", "https://www.infinixmobility.com/")

    b = _get_or_create_brand(conn, "Advan", "advan")
    f_wp = _get_or_create_family(conn, b, "Workplus")
    f_sm = _get_or_create_family(conn, b, "Soulmate")
    m = _add_model(conn, f_wp, "Workplus 14", year=2023)
    _add_procs(conn, m, ["Intel Celeron N4020", "Intel Core i3-1005G1"])
    _add_ref(conn, m, "Advan Official", "https://advan.id/")
    m = _add_model(conn, f_sm, "Soulmate 14", year=2022)
    _add_procs(conn, m, ["Intel Celeron N4020"])
    _add_ref(conn, m, "Advan Official", "https://advan.id/")

    b = _get_or_create_brand(conn, "Zyrex", "zyrex")
    f_zy = _get_or_create_family(conn, b, "Laptop Zyrex")
    m = _add_model(conn, f_zy, "Sky 237", year=2022)
    _add_procs(conn, m, ["Intel Celeron N4020"])
    _add_ref(conn, m, "Zyrex Official", "https://zyrex.com/")

    # ============================================
    # 16. TOSHIBA / Dynabook
    # ============================================
    b = _get_or_create_brand(conn, "Toshiba", "toshiba")
    f_sat = _get_or_create_family(conn, b, "Satellite")
    f_tec = _get_or_create_family(conn, b, "Tecra")
    f_por = _get_or_create_family(conn, b, "Portege")
    f_dyn = _get_or_create_family(conn, b, "Dynabook")

    m = _add_model(conn, f_sat, "Satellite C50", year=2015)
    _add_procs(conn, m, ["Intel Core i3-5005U", "Intel Core i5-5200U"])
    _add_ref(conn, m, "Toshiba / Dynabook Support", "https://support.dynabook.com/")

    m = _add_model(conn, f_tec, "Tecra A50", year=2018)
    _add_procs(conn, m, ["Intel Core i5-8250U"])
    _add_ref(conn, m, "Toshiba / Dynabook Support", "https://support.dynabook.com/")

    # ============================================
    # 17. SONY VAIO (legacy + VAIO Corporation)
    # ============================================
    b = _get_or_create_brand(conn, "Sony VAIO", "sony-vaio")
    f_vaio = _get_or_create_family(conn, b, "VAIO")
    f_s = _get_or_create_family(conn, b, "VAIO S")
    f_z = _get_or_create_family(conn, b, "VAIO Z")

    m = _add_model(conn, f_s, "VAIO S13", year=2018)
    _add_procs(conn, m, ["Intel Core i5-8250U", "Intel Core i7-8550U"])
    _add_ref(conn, m, "VAIO Support", "https://support.vaio.com/")

    # ============================================
    # 18. RAZER
    # ============================================
    b = _get_or_create_brand(conn, "Razer", "razer")
    f_blade = _get_or_create_family(conn, b, "Blade")
    f_blade14 = _get_or_create_family(conn, b, "Blade 14")
    f_blade15 = _get_or_create_family(conn, b, "Blade 15")
    f_blade16 = _get_or_create_family(conn, b, "Blade 16")
    f_blade18 = _get_or_create_family(conn, b, "Blade 18")

    m = _add_model(conn, f_blade15, "Blade 15 (2023)", year=2023, gpu="NVIDIA RTX 4070")
    _add_procs(conn, m, ["Intel Core i7-13800H", "Intel Core i9-13900H"])
    _add_ref(conn, m, "Razer Support", "https://support.razer.com/")

    m = _add_model(conn, f_blade14, "Blade 14 (2023)", year=2023, gpu="NVIDIA RTX 4060")
    _add_procs(conn, m, ["AMD Ryzen 9 7940HS"])
    _add_ref(conn, m, "Razer Support", "https://support.razer.com/")

    # ============================================
    # 19. LG
    # ============================================
    b = _get_or_create_brand(conn, "LG", "lg")
    f_gram = _get_or_create_family(conn, b, "gram")

    m = _add_model(conn, f_gram, "gram 14 (2023)", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1340P", "Intel Core i7-1360P"])
    _add_ref(conn, m, "LG Support", "https://www.lg.com/support")

    m = _add_model(conn, f_gram, "gram 16 (2023)", year=2023)
    _add_procs(conn, m, ["Intel Core i7-1360P"])
    _add_ref(conn, m, "LG Support", "https://www.lg.com/support")

    # ============================================
    # 20. FUJITSU
    # ============================================
    b = _get_or_create_brand(conn, "Fujitsu", "fujitsu")
    f_lh = _get_or_create_family(conn, b, "LIFEBOOK")
    f_uh = _get_or_create_family(conn, b, "LIFEBOOK U")

    m = _add_model(conn, f_lh, "LIFEBOOK A3510", year=2021)
    _add_procs(conn, m, ["Intel Core i5-1135G7"])
    _add_ref(conn, m, "Fujitsu Support", "https://www.fujitsu.com/support/")

    # ============================================
    # 21. PANASONIC
    # ============================================
    b = _get_or_create_brand(conn, "Panasonic", "panasonic")
    f_tf = _get_or_create_family(conn, b, "Toughbook")
    f_tl = _get_or_create_family(conn, b, "Toughbook Laptop")

    m = _add_model(conn, f_tf, "Toughbook 55", year=2021)
    _add_procs(conn, m, ["Intel Core i5-10310U", "Intel Core i7-10810U"])
    _add_ref(conn, m, "Panasonic Toughbook", "https://na.panasonic.com/us/computers-tablets-handhelds")

    # ============================================
    # 22. FRAMEWORK
    # ============================================
    b = _get_or_create_brand(conn, "Framework", "framework")
    f_fw = _get_or_create_family(conn, b, "Framework Laptop")

    m = _add_model(conn, f_fw, "Framework Laptop 13 (AMD Ryzen 7040)", year=2023)
    _add_procs(conn, m, ["AMD Ryzen 5 7640U", "AMD Ryzen 7 7840U"])
    _add_ref(conn, m, "Framework", "https://frame.work/")

    m = _add_model(conn, f_fw, "Framework Laptop 13 (Intel 13th Gen)", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1340P", "Intel Core i7-1360P"])
    _add_ref(conn, m, "Framework", "https://frame.work/")

    m = _add_model(conn, f_fw, "Framework Laptop 16", year=2023, gpu="AMD Radeon RX 7700S (optional)")
    _add_procs(conn, m, ["AMD Ryzen 7 7840HS", "AMD Ryzen 9 7940HS"])
    _add_ref(conn, m, "Framework", "https://frame.work/")

    # ============================================
    # 23. XIAOMI / RedmiBook
    # ============================================
    b = _get_or_create_brand(conn, "Xiaomi", "xiaomi")
    f_rb = _get_or_create_family(conn, b, "RedmiBook")
    f_mi = _get_or_create_family(conn, b, "Mi Notebook")
    f_pro = _get_or_create_family(conn, b, "Xiaomi Notebook Pro")

    m = _add_model(conn, f_rb, "RedmiBook 15", year=2022)
    _add_procs(conn, m, ["Intel Core i3-1115G4", "Intel Core i5-1155G7"])
    _add_ref(conn, m, "Xiaomi", "https://www.mi.com/")

    # ============================================
    # 24. HONOR
    # ============================================
    b = _get_or_create_brand(conn, "Honor", "honor")
    f_mb = _get_or_create_family(conn, b, "MagicBook")

    m = _add_model(conn, f_mb, "MagicBook 14", year=2023)
    _add_procs(conn, m, ["Intel Core i5-12450H", "AMD Ryzen 5 6600H"])
    _add_ref(conn, m, "Honor Support", "https://www.honor.com/support/")

    # ============================================
    # 25. CHUWI
    # ============================================
    b = _get_or_create_brand(conn, "Chuwi", "chuwi")
    f_herobook = _get_or_create_family(conn, b, "HeroBook")
    f_gemibook = _get_or_create_family(conn, b, "GemiBook")
    f_corebook = _get_or_create_family(conn, b, "CoreBook")

    m = _add_model(conn, f_herobook, "HeroBook Pro", year=2022)
    _add_procs(conn, m, ["Intel Celeron N4020"])
    _add_ref(conn, m, "Chuwi", "https://www.chuwi.com/")

    # ============================================
    # 26. TECNO
    # ============================================
    b = _get_or_create_brand(conn, "TECNO", "tecno")
    f_megabook = _get_or_create_family(conn, b, "MegaBook")

    m = _add_model(conn, f_megabook, "MegaBook T1", year=2023)
    _add_procs(conn, m, ["Intel Core i5-1155G7"])
    _add_ref(conn, m, "TECNO", "https://www.tecno-mobile.com/")

    # ============================================
    # 27. MEDION
    # ============================================
    b = _get_or_create_brand(conn, "Medion", "medion")
    f_akoya = _get_or_create_family(conn, b, "Akoya")
    f_erazer = _get_or_create_family(conn, b, "Erazer")

    m = _add_model(conn, f_akoya, "Akoya E15407", year=2022)
    _add_procs(conn, m, ["Intel Core i5-1135G7"])
    _add_ref(conn, m, "Medion Support", "https://www.medion.com/support/")

    # ============================================
    # 28. SYSTEM76
    # ============================================
    b = _get_or_create_brand(conn, "System76", "system76")
    f_lemur = _get_or_create_family(conn, b, "Lemur Pro")
    f_gazelle = _get_or_create_family(conn, b, "Gazelle")
    f_oryx = _get_or_create_family(conn, b, "Oryx Pro")
    f_darter = _get_or_create_family(conn, b, "Darter Pro")

    m = _add_model(conn, f_lemur, "Lemur Pro (2023)", year=2023)
    _add_procs(conn, m, ["Intel Core i7-1355U"])
    _add_ref(conn, m, "System76", "https://system76.com/")

    m = _add_model(conn, f_gazelle, "Gazelle (2023)", year=2023, gpu="NVIDIA RTX 4060")
    _add_procs(conn, m, ["Intel Core i7-13700H"])
    _add_ref(conn, m, "System76", "https://system76.com/")

    # ============================================
    # 29. CLEVO / Schenker (barebone / white label)
    # ============================================
    b = _get_or_create_brand(conn, "Clevo", "clevo")
    f_pb = _get_or_create_family(conn, b, "PBxx series")
    f_nh = _get_or_create_family(conn, b, "NHxx series")

    b = _get_or_create_brand(conn, "Schenker", "schenker")
    f_xmg = _get_or_create_family(conn, b, "XMG")
    f_vision = _get_or_create_family(conn, b, "VISION")

    # ============================================
    # PLACEHOLDER
    # ============================================
    _get_or_create_brand(conn, "Merek Lainnya / Tidak Ditemukan", "others")

    conn.commit()
