import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalog.db")

SEED_SQL = """
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS product_families (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE(brand_id, name)
);

CREATE TABLE IF NOT EXISTS laptop_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    generation TEXT,
    year INTEGER,
    cooling_info TEXT,
    gpu TEXT,
    notes TEXT,
    model_number TEXT,
    verification_status TEXT DEFAULT 'Belum diverifikasi',
    FOREIGN KEY (family_id) REFERENCES product_families(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS processor_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    processor TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES laptop_models(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    source_name TEXT,
    url TEXT,
    updated_at TEXT,
    source_type TEXT DEFAULT 'produsen',
    FOREIGN KEY (model_id) REFERENCES laptop_models(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS consultation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    brand TEXT,
    family TEXT,
    model TEXT,
    processor TEXT,
    mode TEXT,
    symptoms TEXT,
    diagnosis_codes TEXT,
    diagnosis_summary TEXT,
    rules_fired TEXT,
    device_profile_json TEXT
);

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gpus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    vendor TEXT,
    gpu_type TEXT,
    series TEXT,
    vram_gb REAL,
    notes TEXT,
    verification_status TEXT DEFAULT 'Belum diverifikasi'
);

CREATE TABLE IF NOT EXISTS model_gpu_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    gpu_id INTEGER NOT NULL,
    is_default INTEGER DEFAULT 0,
    FOREIGN KEY (model_id) REFERENCES laptop_models(id) ON DELETE CASCADE,
    FOREIGN KEY (gpu_id) REFERENCES gpus(id) ON DELETE CASCADE,
    UNIQUE(model_id, gpu_id)
);

CREATE TABLE IF NOT EXISTS cooling_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    fan_count INTEGER,
    heatpipe_count INTEGER,
    has_vapor_chamber INTEGER DEFAULT 0,
    notes TEXT,
    verification_status TEXT DEFAULT 'Belum diverifikasi'
);

CREATE TABLE IF NOT EXISTS model_cooling (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    cooling_id INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (model_id) REFERENCES laptop_models(id) ON DELETE CASCADE,
    FOREIGN KEY (cooling_id) REFERENCES cooling_profiles(id) ON DELETE CASCADE,
    UNIQUE(model_id, cooling_id)
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT,
    source_type TEXT DEFAULT 'produsen',
    publisher TEXT,
    accessed_at TEXT,
    notes TEXT,
    UNIQUE(name, url)
);

CREATE TABLE IF NOT EXISTS specification_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    field_supported TEXT,
    notes TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SEED_SQL)

    # Migration ringan: tambah kolom jika belum ada (untuk DB lama)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(laptop_models)").fetchall()]
        if "model_number" not in cols:
            conn.execute("ALTER TABLE laptop_models ADD COLUMN model_number TEXT")
        if "verification_status" not in cols:
            conn.execute(
                "ALTER TABLE laptop_models ADD COLUMN verification_status TEXT DEFAULT 'Belum diverifikasi'"
            )
    except Exception:
        pass

    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(device_references)").fetchall()]
        if "source_type" not in cols:
            conn.execute(
                "ALTER TABLE device_references ADD COLUMN source_type TEXT DEFAULT 'produsen'"
            )
    except Exception:
        pass

    conn.commit()

    # Seed admin default jika belum ada
    cur = conn.execute("SELECT COUNT(*) AS c FROM admin_users")
    if cur.fetchone()["c"] == 0:
        # password: admin123  (hash sederhana untuk demo; ganti di production)
        import hashlib
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        conn.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
            ("admin", pw),
        )
        conn.commit()

    # Migrate free-text GPU strings into gpus + model_gpu_options (once)
    try:
        _migrate_gpu_strings(conn)
    except Exception as e:
        print("GPU migration note:", e)

    # Template profil pendinginan generik (bukan klaim per-model)
    try:
        seed_cooling_templates(conn)
    except Exception as e:
        print("Cooling seed note:", e)

    # Registri sumber resmi
    try:
        seed_canonical_sources(conn)
    except Exception as e:
        print("Sources seed note:", e)

    # Seed / perluasan katalog (idempotent — aman dipanggil berulang)
    from catalog_seed import expand_catalog
    expand_catalog(conn)

    conn.close()


# ---------- Auth ----------
def verify_admin(username, password):
    import hashlib
    conn = get_db()
    row = conn.execute(
        "SELECT id, password_hash FROM admin_users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    h = hashlib.sha256(password.encode()).hexdigest()
    return h == row["password_hash"]


# ---------- Query helper ----------
def list_brands():
    conn = get_db()
    rows = conn.execute("SELECT id, name, slug FROM brands ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_families(brand_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name FROM product_families WHERE brand_id = ? ORDER BY name",
        (brand_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_models(family_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT id, name, generation, year, gpu, cooling_info, notes,
                  model_number, verification_status
           FROM laptop_models WHERE family_id = ? ORDER BY name""",
        (family_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_processors(model_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, processor FROM processor_variants WHERE model_id = ? ORDER BY processor",
        (model_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_model_detail(model_id):
    conn = get_db()
    row = conn.execute(
        """SELECT m.*, f.name AS family_name, b.name AS brand_name, b.id AS brand_id
           FROM laptop_models m
           JOIN product_families f ON m.family_id = f.id
           JOIN brands b ON f.brand_id = b.id
           WHERE m.id = ?""",
        (model_id,),
    ).fetchone()
    refs = conn.execute(
        "SELECT source_name, url, updated_at, source_type FROM device_references WHERE model_id = ?",
        (model_id,),
    ).fetchall()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["references"] = [dict(r) for r in refs]
    # GPU options from structured table
    
    try:
        conn2 = get_db()
        grows = conn2.execute(
            """SELECT g.*, mgo.is_default FROM model_gpu_options mgo
               JOIN gpus g ON g.id = mgo.gpu_id WHERE mgo.model_id = ?
               ORDER BY mgo.is_default DESC, g.name""",
            (model_id,),
        ).fetchall()
        conn2.close()
        d["gpu_options"] = [dict(g) for g in grows]
    except Exception:
        d["gpu_options"] = []
    try:
        d["cooling_options"] = list_model_cooling(model_id)
    except Exception:
        d["cooling_options"] = []
    # Explicit status for free-text field
    if not d.get("cooling_info"):
        d["cooling_info"] = "Belum tersedia"
    return d


def search_models(q, limit=30):
    """Pencarian sederhana nama model / merek / keluarga."""
    conn = get_db()
    like = f"%{q}%"
    rows = conn.execute(
        """SELECT m.id, m.name, m.year, m.generation, m.gpu,
                  f.name AS family_name, b.name AS brand_name
           FROM laptop_models m
           JOIN product_families f ON m.family_id = f.id
           JOIN brands b ON f.brand_id = b.id
           WHERE m.name LIKE ? OR b.name LIKE ? OR f.name LIKE ?
           ORDER BY b.name, f.name, m.name
           LIMIT ?""",
        (like, like, like, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- History ----------
def save_consultation(profile, symptoms, hasil):
    conn = get_db()
    diagnosis_codes = [d["kode"] for d in hasil.get("diagnosis", [])]
    diagnosis_summary = "; ".join(
        f"{d['kode']}: {d['nama']}" for d in hasil.get("diagnosis", [])
    )
    rules = [r["id"] for r in hasil.get("aturan", [])]
    conn.execute(
        """INSERT INTO consultation_history
           (created_at, brand, family, model, processor, mode,
            symptoms, diagnosis_codes, diagnosis_summary, rules_fired, device_profile_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            profile.get("brand"),
            profile.get("family"),
            profile.get("model"),
            profile.get("processor"),
            profile.get("mode"),
            json.dumps(symptoms),
            json.dumps(diagnosis_codes),
            diagnosis_summary,
            json.dumps(rules),
            json.dumps(profile),
        ),
    )
    conn.commit()
    conn.close()


def list_history(limit=50):
    conn = get_db()
    rows = conn.execute(
        """SELECT id, created_at, brand, family, model, processor, mode,
                  symptoms, diagnosis_codes, diagnosis_summary, rules_fired
           FROM consultation_history
           ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_history(history_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM consultation_history WHERE id = ?", (history_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- Admin CRUD ----------
def add_brand(name, slug):
    conn = get_db()
    conn.execute("INSERT INTO brands (name, slug) VALUES (?, ?)", (name, slug))
    conn.commit()
    conn.close()


def delete_brand(brand_id):
    conn = get_db()
    conn.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
    conn.commit()
    conn.close()


def add_family(brand_id, name):
    conn = get_db()
    conn.execute(
        "INSERT INTO product_families (brand_id, name) VALUES (?, ?)",
        (brand_id, name),
    )
    conn.commit()
    conn.close()


def delete_family(family_id):
    conn = get_db()
    conn.execute("DELETE FROM product_families WHERE id = ?", (family_id,))
    conn.commit()
    conn.close()


def add_model(
    family_id,
    name,
    generation=None,
    year=None,
    gpu=None,
    cooling_info=None,
    notes=None,
    model_number=None,
    verification_status="Belum diverifikasi",
):
    conn = get_db()
    conn.execute(
        """INSERT INTO laptop_models
           (family_id, name, generation, year, gpu, cooling_info, notes,
            model_number, verification_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            family_id,
            name,
            generation,
            year,
            gpu,
            cooling_info,
            notes,
            model_number,
            verification_status,
        ),
    )
    conn.commit()
    conn.close()


def delete_model(model_id):
    conn = get_db()
    conn.execute("DELETE FROM laptop_models WHERE id = ?", (model_id,))
    conn.commit()
    conn.close()


def add_processor(model_id, processor):
    conn = get_db()
    conn.execute(
        "INSERT INTO processor_variants (model_id, processor) VALUES (?, ?)",
        (model_id, processor),
    )
    conn.commit()
    conn.close()


def add_reference(model_id, source_name, url, updated_at, source_type="produsen"):
    conn = get_db()
    conn.execute(
        """INSERT INTO device_references
           (model_id, source_name, url, updated_at, source_type)
           VALUES (?, ?, ?, ?, ?)""",
        (model_id, source_name, url, updated_at, source_type),
    )
    conn.commit()
    conn.close()



def _guess_vendor(name):
    n = (name or "").lower()
    if "nvidia" in n or "geforce" in n or "rtx" in n or "gtx" in n or "mx " in n:
        return "NVIDIA"
    if "amd" in n or "radeon" in n:
        return "AMD"
    if "intel" in n or "iris" in n or "uhd" in n or "arc" in n:
        return "Intel"
    if "apple" in n:
        return "Apple"
    return None


def _guess_type(name):
    n = (name or "").lower()
    if any(x in n for x in ("rtx", "gtx", "mx ", "radeon rx", "arc")):
        return "dedicated"
    if any(x in n for x in ("uhd", "iris", "integrated", "apple")):
        return "integrated"
    return None


def _get_or_create_gpu(conn, name):
    name = (name or "").strip()
    if not name or name.lower() in ("informasi belum tersedia", "-", "n/a"):
        return None
    row = conn.execute("SELECT id FROM gpus WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    vendor = _guess_vendor(name)
    gpu_type = _guess_type(name)
    cur = conn.execute(
        """INSERT INTO gpus (name, vendor, gpu_type, verification_status)
           VALUES (?, ?, ?, ?)""",
        (name, vendor, gpu_type, "Diimpor dari teks model — perlu verifikasi"),
    )
    return cur.lastrowid


def _migrate_gpu_strings(conn):
    """Pindahkan nilai gpu TEXT di laptop_models ke tabel gpus (jika belum)."""
    rows = conn.execute(
        "SELECT id, gpu FROM laptop_models WHERE gpu IS NOT NULL AND TRIM(gpu) != ''"
    ).fetchall()
    for r in rows:
        mid, gpu_name = r["id"], r["gpu"]
        linked = conn.execute(
            "SELECT 1 FROM model_gpu_options WHERE model_id = ?", (mid,)
        ).fetchone()
        if linked:
            continue
        gpu_id = _get_or_create_gpu(conn, gpu_name)
        if gpu_id:
            conn.execute(
                "INSERT OR IGNORE INTO model_gpu_options (model_id, gpu_id, is_default) VALUES (?, ?, 1)",
                (mid, gpu_id),
            )
    conn.commit()


def list_gpus():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM gpus ORDER BY vendor, name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_model_gpus(model_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT g.*, mgo.is_default
           FROM model_gpu_options mgo
           JOIN gpus g ON g.id = mgo.gpu_id
           WHERE mgo.model_id = ?
           ORDER BY mgo.is_default DESC, g.name""",
        (model_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_gpu(name, vendor=None, gpu_type=None, series=None, vram_gb=None, notes=None):
    conn = get_db()
    vendor = vendor or _guess_vendor(name)
    gpu_type = gpu_type or _guess_type(name)
    cur = conn.execute(
        """INSERT INTO gpus (name, vendor, gpu_type, series, vram_gb, notes, verification_status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, vendor, gpu_type, series, vram_gb, notes, "Ditambahkan admin"),
    )
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid


def link_model_gpu(model_id, gpu_id, is_default=0):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO model_gpu_options (model_id, gpu_id, is_default) VALUES (?, ?, ?)",
        (model_id, gpu_id, is_default),
    )
    conn.commit()
    conn.close()


def filter_models(brand_id=None, year_from=None, year_to=None, gpu_vendor=None,
                  has_dedicated=None, q=None, verification_status=None, limit=50):
    """Filter katalog untuk halaman browse / API."""
    conn = get_db()
    sql = """
        SELECT DISTINCT m.id, m.name, m.year, m.generation, m.gpu, m.cooling_info,
               m.verification_status,
               f.name AS family_name, b.name AS brand_name, b.id AS brand_id
        FROM laptop_models m
        JOIN product_families f ON m.family_id = f.id
        JOIN brands b ON f.brand_id = b.id
        LEFT JOIN model_gpu_options mgo ON mgo.model_id = m.id
        LEFT JOIN gpus g ON g.id = mgo.gpu_id
        WHERE 1=1
    """
    params = []
    if brand_id:
        sql += " AND b.id = ?"
        params.append(int(brand_id))
    if year_from:
        sql += " AND m.year >= ?"
        params.append(int(year_from))
    if year_to:
        sql += " AND m.year <= ?"
        params.append(int(year_to))
    if gpu_vendor:
        sql += " AND (g.vendor = ? OR m.gpu LIKE ?)"
        params.extend([gpu_vendor, f"%{gpu_vendor}%"])
    if has_dedicated is True:
        sql += " AND (g.gpu_type = 'dedicated' OR m.gpu LIKE '%RTX%' OR m.gpu LIKE '%GTX%' OR m.gpu LIKE '%RX %')"
    if has_dedicated is False:
        sql += " AND (g.gpu_type = 'integrated' OR (m.gpu IS NULL OR m.gpu = '' OR m.gpu LIKE '%UHD%' OR m.gpu LIKE '%Iris%'))"
    if q:
        sql += " AND (m.name LIKE ? OR b.name LIKE ? OR f.name LIKE ? OR m.gpu LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like, like])
    if verification_status:
        sql += " AND m.verification_status = ?"
        params.append(verification_status)
    sql += " ORDER BY b.name, f.name, m.name LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]



def list_cooling_profiles():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM cooling_profiles ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_model_cooling(model_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT c.*, mc.notes AS link_notes
           FROM model_cooling mc
           JOIN cooling_profiles c ON c.id = mc.cooling_id
           WHERE mc.model_id = ?
           ORDER BY c.name""",
        (model_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_cooling_profile(name, fan_count=None, heatpipe_count=None,
                        has_vapor_chamber=0, notes=None, verification_status=None):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO cooling_profiles
           (name, fan_count, heatpipe_count, has_vapor_chamber, notes, verification_status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            name,
            fan_count,
            heatpipe_count,
            1 if has_vapor_chamber else 0,
            notes,
            verification_status or "Template profil — belum dilampirkan ke model",
        ),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def link_model_cooling(model_id, cooling_id, notes=None):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO model_cooling (model_id, cooling_id, notes) VALUES (?, ?, ?)",
        (model_id, cooling_id, notes),
    )
    conn.commit()
    conn.close()


def seed_cooling_templates(conn=None):
    """Profil pendinginan generik (bukan klaim per-model)."""
    close = False
    if conn is None:
        conn = get_db()
        close = True
    templates = [
        {
            "name": "Single Fan (tipikal ultrabook tipis)",
            "fan_count": 1,
            "heatpipe_count": None,
            "has_vapor_chamber": 0,
            "notes": "Template umum. Jumlah heatpipe bervariasi per model — verifikasi di service manual.",
            "verification_status": "Template generik",
        },
        {
            "name": "Dual Fan (tipikal gaming mid-range)",
            "fan_count": 2,
            "heatpipe_count": None,
            "has_vapor_chamber": 0,
            "notes": "Template umum untuk banyak laptop gaming. Jangan diasumsikan untuk semua model dalam satu seri.",
            "verification_status": "Template generik",
        },
        {
            "name": "Dual Fan + Vapor Chamber (tipikal gaming high-end)",
            "fan_count": 2,
            "heatpipe_count": None,
            "has_vapor_chamber": 1,
            "notes": "Beberapa model high-end mempublikasikan vapor chamber. Hanya tautkan jika ada sumber resmi.",
            "verification_status": "Template generik",
        },
        {
            "name": "Triple Fan / Advanced (tipikal workstation / flagship gaming)",
            "fan_count": 3,
            "heatpipe_count": None,
            "has_vapor_chamber": 0,
            "notes": "Hanya untuk model yang secara eksplisit menyebutkan 3 kipas di dokumen resmi.",
            "verification_status": "Template generik",
        },
        {
            "name": "Fanless / Passive cooling (tipikal beberapa convertibles tipis)",
            "fan_count": 0,
            "heatpipe_count": 0,
            "has_vapor_chamber": 0,
            "notes": "Sangat jarang. Jangan diasumsikan tanpa dokumentasi.",
            "verification_status": "Template generik",
        },
        {
            "name": "Belum tersedia / Belum diverifikasi",
            "fan_count": None,
            "heatpipe_count": None,
            "has_vapor_chamber": 0,
            "notes": "Gunakan jika produsen tidak memublikasikan detail kipas/heatpipe.",
            "verification_status": "Placeholder",
        },
    ]
    for t in templates:
        exists = conn.execute(
            "SELECT id FROM cooling_profiles WHERE name = ?", (t["name"],)
        ).fetchone()
        if not exists:
            conn.execute(
                """INSERT INTO cooling_profiles
                   (name, fan_count, heatpipe_count, has_vapor_chamber, notes, verification_status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    t["name"],
                    t["fan_count"],
                    t["heatpipe_count"],
                    t["has_vapor_chamber"],
                    t["notes"],
                    t["verification_status"],
                ),
            )
    conn.commit()
    if close:
        conn.close()



# ---------- Sources & verification ----------
VERIFICATION_STATUSES = [
    "Terverifikasi dari produsen",
    "Terverifikasi dari dokumentasi teknis",
    "Contoh seed — perlu verifikasi detail",
    "Diimpor dari teks model — perlu verifikasi",
    "Ditambahkan admin",
    "Input manual",
    "Belum diverifikasi",
    "Belum tersedia",
    "Template generik",
    "Placeholder",
]


def list_sources():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sources ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_source(name, url=None, source_type="produsen", publisher=None, notes=None):
    from datetime import date
    conn = get_db()
    cur = conn.execute(
        """INSERT OR IGNORE INTO sources (name, url, source_type, publisher, accessed_at, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, url, source_type, publisher, date.today().isoformat(), notes),
    )
    conn.commit()
    # fetch id
    row = conn.execute(
        "SELECT id FROM sources WHERE name = ? AND IFNULL(url,'') = IFNULL(?, '')",
        (name, url),
    ).fetchone()
    conn.close()
    return row["id"] if row else cur.lastrowid


def link_specification_source(entity_type, entity_id, source_id, field_supported=None, notes=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO specification_sources
           (entity_type, entity_id, source_id, field_supported, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (entity_type, entity_id, source_id, field_supported, notes),
    )
    conn.commit()
    conn.close()


def list_entity_sources(entity_type, entity_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT s.*, ss.field_supported, ss.notes AS link_notes
           FROM specification_sources ss
           JOIN sources s ON s.id = ss.source_id
           WHERE ss.entity_type = ? AND ss.entity_id = ?
           ORDER BY s.name""",
        (entity_type, entity_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_model_verification(model_id, status, notes=None):
    conn = get_db()
    conn.execute(
        "UPDATE laptop_models SET verification_status = ? WHERE id = ?",
        (status, model_id),
    )
    if notes:
        # append to notes field
        row = conn.execute("SELECT notes FROM laptop_models WHERE id = ?", (model_id,)).fetchone()
        old = (row["notes"] or "") if row else ""
        merged = (old + "\n" + notes).strip() if old else notes
        conn.execute("UPDATE laptop_models SET notes = ? WHERE id = ?", (merged, model_id))
    conn.commit()
    conn.close()


def verification_summary():
    """Ringkasan kualitas data katalog."""
    conn = get_db()
    by_status = conn.execute(
        """SELECT verification_status, COUNT(*) AS c
           FROM laptop_models
           GROUP BY verification_status
           ORDER BY c DESC"""
    ).fetchall()
    with_gpu = conn.execute(
        """SELECT COUNT(DISTINCT model_id) FROM model_gpu_options"""
    ).fetchone()[0]
    with_cooling = conn.execute(
        """SELECT COUNT(DISTINCT model_id) FROM model_cooling"""
    ).fetchone()[0]
    with_ref = conn.execute(
        """SELECT COUNT(DISTINCT model_id) FROM device_references"""
    ).fetchone()[0]
    sources_n = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM laptop_models").fetchone()[0]
    conn.close()
    return {
        "by_status": [dict(r) for r in by_status],
        "models_with_gpu_link": with_gpu,
        "models_with_cooling_link": with_cooling,
        "models_with_reference": with_ref,
        "sources_registered": sources_n,
        "total_models": total,
    }


def seed_canonical_sources(conn=None):
    """Registri sumber resmi yang sering dipakai (bukan klaim verifikasi model)."""
    close = False
    if conn is None:
        conn = get_db()
        close = True
    from datetime import date
    today = date.today().isoformat()
    items = [
        ("Dell Support", "https://www.dell.com/support/", "produsen", "Dell"),
        ("ASUS Support", "https://www.asus.com/support/", "produsen", "ASUS"),
        ("HP Support", "https://support.hp.com/", "produsen", "HP"),
        ("Lenovo Support", "https://pcsupport.lenovo.com/", "produsen", "Lenovo"),
        ("Acer Support", "https://www.acer.com/support/", "produsen", "Acer"),
        ("MSI Support", "https://www.msi.com/support", "produsen", "MSI"),
        ("Apple Support", "https://support.apple.com/", "produsen", "Apple"),
        ("Intel ARK", "https://ark.intel.com/", "teknis", "Intel"),
        ("AMD Product Specs", "https://www.amd.com/en/products/specifications/processors.html", "teknis", "AMD"),
        ("NVIDIA Product Specs", "https://www.nvidia.com/en-us/geforce/", "teknis", "NVIDIA"),
        ("Framework", "https://frame.work/", "produsen", "Framework"),
        ("System76", "https://system76.com/", "produsen", "System76"),
        ("Razer Support", "https://support.razer.com/", "produsen", "Razer"),
        ("LG Support", "https://www.lg.com/support", "produsen", "LG"),
        ("Notebookcheck", "https://www.notebookcheck.net/", "pihak-ketiga", "Notebookcheck"),
    ]
    for name, url, stype, pub in items:
        exists = conn.execute(
            "SELECT id FROM sources WHERE name = ?", (name,)
        ).fetchone()
        if not exists:
            conn.execute(
                """INSERT INTO sources (name, url, source_type, publisher, accessed_at, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, url, stype, pub, today, "Sumber referensi katalog / basis pengetahuan"),
            )
    conn.commit()
    if close:
        conn.close()



def export_catalog_rows():
    """Flat rows for CSV export."""
    conn = get_db()
    rows = conn.execute(
        """SELECT b.name AS brand, f.name AS family, m.name AS model,
                  m.generation, m.year, m.gpu, m.cooling_info, m.model_number,
                  m.verification_status, m.notes, m.id AS model_id
           FROM laptop_models m
           JOIN product_families f ON m.family_id = f.id
           JOIN brands b ON f.brand_id = b.id
           ORDER BY b.name, f.name, m.name"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def import_catalog_csv_rows(rows):
    """
    Import list of dicts with keys:
    brand, family, model, generation, year, gpu, cooling_info, model_number, processor
    Idempotent-ish: creates brand/family/model if missing.
    Returns (created_models, skipped, errors)
    """
    from catalog_seed import _get_or_create_brand, _get_or_create_family, _add_model, _add_procs
    conn = get_db()
    created, skipped, errors = 0, 0, []
    for i, row in enumerate(rows, start=1):
        try:
            brand = (row.get("brand") or "").strip()
            family = (row.get("family") or "").strip()
            model = (row.get("model") or "").strip()
            if not brand or not family or not model:
                errors.append(f"Baris {i}: brand/family/model wajib")
                continue
            slug = brand.lower().replace(" ", "-")
            bid = _get_or_create_brand(conn, brand, slug)
            fid = _get_or_create_family(conn, bid, family)
            year = row.get("year")
            try:
                year = int(year) if year not in (None, "") else None
            except ValueError:
                year = None
            mid = _add_model(
                conn, fid, model,
                generation=(row.get("generation") or None) or None,
                year=year,
                gpu=(row.get("gpu") or None) or None,
                cooling_info=(row.get("cooling_info") or None) or None,
                model_number=(row.get("model_number") or None) or None,
            )
            # _add_model returns existing id if duplicate name in family
            procs = row.get("processor") or row.get("processors") or ""
            if procs:
                plist = [x.strip() for x in str(procs).replace(";", ",").split(",") if x.strip()]
                if plist:
                    _add_procs(conn, mid, plist)
            created += 1
        except Exception as e:
            errors.append(f"Baris {i}: {e}")
    conn.commit()
    conn.close()
    return created, skipped, errors


def get_stats():
    conn = get_db()
    stats = {
        "brands": conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0],
        "families": conn.execute("SELECT COUNT(*) FROM product_families").fetchone()[0],
        "models": conn.execute("SELECT COUNT(*) FROM laptop_models").fetchone()[0],
        "processors": conn.execute("SELECT COUNT(*) FROM processor_variants").fetchone()[0],
        "history": conn.execute("SELECT COUNT(*) FROM consultation_history").fetchone()[0],
        "gpus": conn.execute("SELECT COUNT(*) FROM gpus").fetchone()[0],
        "cooling_profiles": conn.execute("SELECT COUNT(*) FROM cooling_profiles").fetchone()[0],
        "sources": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
    }
    conn.close()
    return stats
