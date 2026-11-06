from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from datetime import datetime
from functools import wraps
import os
import csv
import io

from knowledge_base import GEJALA, KESIMPULAN_ANTARA, KESIMPULAN_AKHIR, RULES
from inference_engine import forward_chaining
from database import (
    init_db, list_brands, list_families, list_models,
    list_processors, get_model_detail, search_models,
    add_brand, add_family, add_model, add_processor, add_reference,
    delete_brand, delete_family, delete_model,
    verify_admin, save_consultation, list_history, get_history, get_stats,
    list_gpus, filter_models, add_gpu, link_model_gpu,
    list_cooling_profiles, add_cooling_profile, link_model_cooling,
    list_sources, add_source, link_specification_source,
    update_model_verification, verification_summary, VERIFICATION_STATUSES,
    export_catalog_rows, import_catalog_csv_rows,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "thermal-diagnose-dev-key-change-in-production")

# Inisialisasi database saat start
with app.app_context():
    init_db()


@app.context_processor
def inject_globals():
    return {
        "app_name": "ThermalDiagnose",
        "app_year": 2026,
        "is_admin": session.get("admin_logged_in", False),
    }


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Silakan login sebagai administrator.", "info")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# ROUTE: HALAMAN IDENTIFIKASI PERANGKAT (Tahap 1)
# ============================================================
@app.route("/")
def identifikasi():
    brands = list_brands()
    saved = session.get("device_profile")
    return render_template(
        "identifikasi.html",
        brands=brands,
        saved_device=saved,
        active="identifikasi",
    )


# ============================================================
# API: Dependent dropdown + search
# ============================================================
@app.route("/api/families/<int:brand_id>")
def api_families(brand_id):
    return jsonify(list_families(brand_id))


@app.route("/api/models/<int:family_id>")
def api_models(family_id):
    return jsonify(list_models(family_id))


@app.route("/api/processors/<int:model_id>")
def api_processors(model_id):
    return jsonify(list_processors(model_id))


@app.route("/api/model-detail/<int:model_id>")
def api_model_detail(model_id):
    detail = get_model_detail(model_id)
    if not detail:
        return jsonify({"error": "Model tidak ditemukan"}), 404
    return jsonify(detail)


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify(search_models(q))


# ============================================================
# ROUTE: Simpan profil perangkat
# ============================================================
@app.route("/simpan-perangkat", methods=["POST"])
def simpan_perangkat():
    mode = request.form.get("mode", "catalog")

    if mode == "catalog":
        model_id = request.form.get("model_id")
        processor = request.form.get("processor", "").strip()
        if not model_id:
            flash("Pilih model laptop terlebih dahulu.", "error")
            return redirect(url_for("identifikasi"))

        detail = get_model_detail(int(model_id))
        if not detail:
            flash("Model tidak ditemukan di katalog.", "error")
            return redirect(url_for("identifikasi"))

        profile = {
            "mode": "catalog",
            "brand": detail["brand_name"],
            "family": detail["family_name"],
            "model": detail["name"],
            "generation": detail.get("generation") or "Informasi belum tersedia",
            "year": detail.get("year") or "-",
            "gpu": detail.get("gpu") or "Informasi belum tersedia",
            "cooling_info": detail.get("cooling_info") or "Informasi belum tersedia",
            "processor": processor or "Informasi belum tersedia",
            "references": detail.get("references", []),
            "model_id": detail["id"],
            "verification_status": detail.get("verification_status") or "Belum diverifikasi",
        }
    else:  # mode manual
        brand = request.form.get("manual_brand", "").strip()
        family = request.form.get("manual_family", "").strip()
        model = request.form.get("manual_model", "").strip()
        processor = request.form.get("manual_processor", "").strip()
        notes = request.form.get("manual_notes", "").strip()

        if not brand or not model:
            flash("Merek dan model wajib diisi pada input manual.", "error")
            return redirect(url_for("identifikasi"))

        profile = {
            "mode": "manual",
            "brand": brand,
            "family": family or "Informasi belum tersedia",
            "model": model,
            "generation": "Informasi belum tersedia",
            "year": "-",
            "gpu": "Informasi belum tersedia",
            "cooling_info": "Informasi belum tersedia",
            "processor": processor or "Informasi belum tersedia",
            "notes": notes,
            "references": [],
            "label": "Input manual pengguna (belum diverifikasi)",
            "verification_status": "Input manual",
        }

    session["device_profile"] = profile
    session["identified_at"] = datetime.now().strftime("%d %B %Y, %H:%M")
    flash("Profil perangkat berhasil disimpan.", "success")
    return redirect(url_for("home"))


# ============================================================
# ROUTE: Halaman konsultasi gejala (Tahap 2)
# ============================================================
@app.route("/konsultasi")
def home():
    profile = session.get("device_profile")
    if not profile:
        flash("Silakan identifikasi perangkat laptop terlebih dahulu.", "info")
        return redirect(url_for("identifikasi"))
    return render_template(
        "index.html",
        gejala=GEJALA,
        device_profile=profile,
        active="home",
    )


@app.route("/ganti-perangkat")
def ganti_perangkat():
    session.pop("device_profile", None)
    session.pop("identified_at", None)
    flash("Profil perangkat dihapus. Silakan pilih ulang.", "info")
    return redirect(url_for("identifikasi"))


# ============================================================
# ROUTE: Diagnosis
# ============================================================
@app.route("/diagnosis", methods=["POST"])
def diagnosis():
    profile = session.get("device_profile")
    if not profile:
        flash("Silakan identifikasi perangkat terlebih dahulu.", "info")
        return redirect(url_for("identifikasi"))

    gejala_dipilih = request.form.getlist("gejala")
    if not gejala_dipilih:
        return render_template(
            "error.html",
            title="Tidak Ada Gejala Dipilih",
            message="Silakan pilih minimal satu gejala sebelum memulai diagnosis.",
        ), 400

    hasil = forward_chaining(gejala_dipilih)

    # Konteks perangkat terstruktur (tidak mengubah hasil FC)
    device_context = {
        "gpu_options": [],
        "cooling_options": [],
        "contextual_notes": [],
    }
    try:
        mid = profile.get("model_id")
        if mid and profile.get("mode") == "catalog":
            detail = get_model_detail(int(mid))
            if detail:
                device_context["gpu_options"] = detail.get("gpu_options") or []
                device_context["cooling_options"] = detail.get("cooling_options") or []
    except Exception:
        pass

    # Catatan konteks (bukan diagnosis) — hanya saran umum
    notes = []
    gpu_text = (profile.get("gpu") or "").lower()
    if any(x in gpu_text for x in ("rtx", "gtx", "radeon rx")):
        notes.append(
            "Perangkat ini tercatat memiliki GPU dedicated. Beban GPU tinggi dapat "
            "meningkatkan suhu; pastikan ventilasi tidak terhalang saat gaming/render."
        )
    if profile.get("mode") == "manual":
        notes.append(
            "Profil perangkat berasal dari input manual dan belum diverifikasi terhadap katalog resmi."
        )
    cool = (profile.get("cooling_info") or "").lower()
    if "belum" in cool or cool in ("", "-", "informasi belum tersedia"):
        notes.append(
            "Informasi sistem pendinginan spesifik model belum tersedia di katalog. "
            "Diagnosis tetap memakai aturan umum yang telah divalidasi."
        )
    device_context["contextual_notes"] = notes

    # Simpan riwayat
    try:
        save_consultation(profile, gejala_dipilih, hasil)
    except Exception:
        pass  # jangan gagalkan diagnosis jika history gagal

    return render_template(
        "hasil.html",
        hasil=hasil,
        gejala_dipilih=gejala_dipilih,
        daftar_gejala=GEJALA,
        kesimpulan_antara=KESIMPULAN_ANTARA,
        device_profile=profile,
        device_context=device_context,
        identified_at=session.get("identified_at", "-"),
        active="hasil",
    )


# ============================================================
# ROUTE: Validasi Pakar
# ============================================================
@app.route("/validasi")
def validasi():
    return render_template("validasi.html", active="validasi")


# ============================================================
# ROUTE: Riwayat Konsultasi
# ============================================================
@app.route("/riwayat")
def riwayat():
    items = list_history(100)
    return render_template("riwayat.html", history=items, active="riwayat")


@app.route("/riwayat/<int:history_id>")
def riwayat_detail(history_id):
    item = get_history(history_id)
    if not item:
        flash("Riwayat tidak ditemukan.", "error")
        return redirect(url_for("riwayat"))
    return render_template("riwayat_detail.html", item=item, active="riwayat")


# ============================================================
# ROUTE: Katalog Browse + Filter
# ============================================================
@app.route("/katalog")
def katalog():
    brands = list_brands()
    brand_id = request.args.get("brand_id") or None
    year_from = request.args.get("year_from") or None
    year_to = request.args.get("year_to") or None
    gpu_vendor = request.args.get("gpu_vendor") or None
    dedicated = request.args.get("dedicated")
    q = request.args.get("q") or None
    has_dedicated = None
    if dedicated == "1":
        has_dedicated = True
    elif dedicated == "0":
        has_dedicated = False
    models = filter_models(
        brand_id=brand_id,
        year_from=year_from,
        year_to=year_to,
        gpu_vendor=gpu_vendor,
        has_dedicated=has_dedicated,
        q=q,
        limit=100,
    )
    return render_template(
        "katalog.html",
        brands=brands,
        models=models,
        filters={
            "brand_id": brand_id or "",
            "year_from": year_from or "",
            "year_to": year_to or "",
            "gpu_vendor": gpu_vendor or "",
            "dedicated": dedicated or "",
            "q": q or "",
        },
        active="katalog",
    )


@app.route("/api/filter-models")
def api_filter_models():
    brand_id = request.args.get("brand_id") or None
    year_from = request.args.get("year_from") or None
    year_to = request.args.get("year_to") or None
    gpu_vendor = request.args.get("gpu_vendor") or None
    dedicated = request.args.get("dedicated")
    q = request.args.get("q") or None
    has_dedicated = True if dedicated == "1" else (False if dedicated == "0" else None)
    return jsonify(filter_models(
        brand_id=brand_id, year_from=year_from, year_to=year_to,
        gpu_vendor=gpu_vendor, has_dedicated=has_dedicated, q=q, limit=80,
    ))


@app.route("/api/gpus")
def api_gpus():
    return jsonify(list_gpus())


# ============================================================
# ADMIN AUTH
# ============================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if verify_admin(username, password):
            session["admin_logged_in"] = True
            session["admin_user"] = username
            flash("Login berhasil.", "success")
            return redirect(url_for("admin"))
        flash("Username atau password salah.", "error")
    return render_template("admin_login.html", active="admin")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_user", None)
    flash("Anda telah logout.", "info")
    return redirect(url_for("identifikasi"))


# ============================================================
# ROUTE: Admin katalog
# ============================================================
@app.route("/admin")
@admin_required
def admin():
    brands = list_brands()
    stats = get_stats()
    cooling = list_cooling_profiles()
    gpus = list_gpus()
    sources = list_sources()
    vsum = verification_summary()
    return render_template(
        "admin.html",
        brands=brands,
        stats=stats,
        cooling_profiles=cooling,
        gpus=gpus,
        sources=sources,
        verification_summary=vsum,
        verification_statuses=VERIFICATION_STATUSES,
        active="admin",
    )


@app.route("/admin/brand/add", methods=["POST"])
@admin_required
def admin_brand_add():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
    if name and slug:
        try:
            add_brand(name, slug)
            flash(f"Merek '{name}' ditambahkan.", "success")
        except Exception as e:
            flash(f"Gagal menambah merek: {e}", "error")
    else:
        flash("Nama dan slug wajib diisi.", "error")
    return redirect(url_for("admin"))


@app.route("/admin/brand/delete/<int:brand_id>", methods=["POST"])
@admin_required
def admin_brand_delete(brand_id):
    delete_brand(brand_id)
    flash("Merek dihapus (beserta keluarga & model di dalamnya).", "success")
    return redirect(url_for("admin"))


@app.route("/admin/family/add", methods=["POST"])
@admin_required
def admin_family_add():
    brand_id = request.form.get("brand_id")
    name = request.form.get("name", "").strip()
    if brand_id and name:
        try:
            add_family(int(brand_id), name)
            flash(f"Keluarga '{name}' ditambahkan.", "success")
        except Exception as e:
            flash(f"Gagal menambah keluarga: {e}", "error")
    else:
        flash("Merek dan nama keluarga wajib diisi.", "error")
    return redirect(url_for("admin"))


@app.route("/admin/family/delete/<int:family_id>", methods=["POST"])
@admin_required
def admin_family_delete(family_id):
    delete_family(family_id)
    flash("Keluarga produk dihapus.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/model/add", methods=["POST"])
@admin_required
def admin_model_add():
    family_id = request.form.get("family_id")
    name = request.form.get("name", "").strip()
    generation = request.form.get("generation", "").strip() or None
    year = request.form.get("year", "").strip() or None
    gpu = request.form.get("gpu", "").strip() or None
    cooling = request.form.get("cooling_info", "").strip() or None
    notes = request.form.get("notes", "").strip() or None
    model_number = request.form.get("model_number", "").strip() or None

    if family_id and name:
        try:
            add_model(
                int(family_id),
                name,
                generation=generation,
                year=int(year) if year else None,
                gpu=gpu,
                cooling_info=cooling,
                notes=notes,
                model_number=model_number,
            )
            flash(f"Model '{name}' ditambahkan.", "success")
        except Exception as e:
            flash(f"Gagal menambah model: {e}", "error")
    else:
        flash("Keluarga dan nama model wajib diisi.", "error")
    return redirect(url_for("admin"))


@app.route("/admin/model/delete/<int:model_id>", methods=["POST"])
@admin_required
def admin_model_delete(model_id):
    delete_model(model_id)
    flash("Model dihapus.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/processor/add", methods=["POST"])
@admin_required
def admin_processor_add():
    model_id = request.form.get("model_id")
    proc = request.form.get("processor", "").strip()
    if model_id and proc:
        try:
            add_processor(int(model_id), proc)
            flash("Varian prosesor ditambahkan.", "success")
        except Exception as e:
            flash(f"Gagal menambah prosesor: {e}", "error")
    else:
        flash("Model ID dan nama prosesor wajib diisi.", "error")
    return redirect(url_for("admin"))


@app.route("/admin/export.csv")
@admin_required
def admin_export_csv():
    from flask import Response
    rows = export_catalog_rows()
    buf = io.StringIO()
    fields = ["brand", "family", "model", "generation", "year", "gpu",
              "cooling_info", "model_number", "verification_status", "notes", "model_id"]
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    resp = Response(buf.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = "attachment; filename=thermal_diagnose_catalog.csv"
    return resp


@app.route("/admin/import-csv", methods=["POST"])
@admin_required
def admin_import_csv():
    f = request.files.get("csv_file")
    if not f or not f.filename:
        flash("Pilih file CSV terlebih dahulu.", "error")
        return redirect(url_for("admin"))
    try:
        raw = f.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)
        created, skipped, errors = import_catalog_csv_rows(rows)
        msg = f"Impor selesai: {created} baris diproses."
        if errors:
            msg += f" {len(errors)} error (lihat log/admin)."
            for e in errors[:5]:
                flash(e, "error")
        flash(msg, "success" if not errors else "info")
    except Exception as e:
        flash(f"Gagal impor CSV: {e}", "error")
    return redirect(url_for("admin"))


@app.route("/admin/csv-template")
@admin_required
def admin_csv_template():
    from flask import Response
    buf = io.StringIO()
    fields = ["brand", "family", "model", "generation", "year", "gpu",
              "cooling_info", "model_number", "processor"]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    w.writerow({
        "brand": "ContohBrand",
        "family": "ContohFamily",
        "model": "Model Contoh 14",
        "generation": "Gen 1",
        "year": "2023",
        "gpu": "Intel UHD Graphics",
        "cooling_info": "",
        "model_number": "",
        "processor": "Intel Core i5-1235U, Intel Core i7-1255U",
    })
    resp = Response(buf.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = "attachment; filename=catalog_template.csv"
    return resp


@app.route("/admin/source/add", methods=["POST"])
@admin_required
def admin_source_add():
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip() or None
    source_type = request.form.get("source_type", "produsen").strip()
    publisher = request.form.get("publisher", "").strip() or None
    notes = request.form.get("notes", "").strip() or None
    if not name:
        flash("Nama sumber wajib diisi.", "error")
        return redirect(url_for("admin"))
    try:
        add_source(name, url=url, source_type=source_type, publisher=publisher, notes=notes)
        flash(f"Sumber '{name}' didaftarkan.", "success")
    except Exception as e:
        flash(f"Gagal menambah sumber: {e}", "error")
    return redirect(url_for("admin"))


@app.route("/admin/model/verify", methods=["POST"])
@admin_required
def admin_model_verify():
    model_id = request.form.get("model_id", "").strip()
    status = request.form.get("verification_status", "").strip()
    notes = request.form.get("notes", "").strip() or None
    source_id = request.form.get("source_id", "").strip() or None
    field_supported = request.form.get("field_supported", "").strip() or None
    if not model_id or not status:
        flash("Model ID dan status verifikasi wajib.", "error")
        return redirect(url_for("admin"))
    try:
        update_model_verification(int(model_id), status, notes=notes)
        if source_id:
            link_specification_source(
                "model", int(model_id), int(source_id),
                field_supported=field_supported or "model_identity",
                notes=notes,
            )
        flash(f"Status verifikasi model #{model_id} diperbarui.", "success")
    except Exception as e:
        flash(f"Gagal update verifikasi: {e}", "error")
    return redirect(url_for("admin"))


@app.route("/basis-pengetahuan")
def basis_pengetahuan():
    """Transparansi akademis: gejala, kesimpulan, aturan IF-THEN."""
    return render_template(
        "basis_pengetahuan.html",
        gejala=GEJALA,
        kesimpulan_antara=KESIMPULAN_ANTARA,
        kesimpulan_akhir=KESIMPULAN_AKHIR,
        rules=RULES,
        active="basis",
    )


@app.route("/skenario-uji")
def skenario_uji():
    """Dokumentasi skenario pengujian Forward Chaining (minimal 5)."""
    from test_scenarios import SCENARIOS, run_all_scenarios
    results = run_all_scenarios()
    return render_template(
        "skenario_uji.html",
        scenarios=SCENARIOS,
        results=results,
        active="basis",
    )


@app.route("/sumber")
def sumber():
    """Halaman transparansi sumber & kualitas data."""
    sources = list_sources()
    vsum = verification_summary()
    return render_template(
        "sumber.html",
        sources=sources,
        verification_summary=vsum,
        active="sumber",
    )


@app.route("/admin/cooling/add", methods=["POST"])
@admin_required
def admin_cooling_add():
    name = request.form.get("name", "").strip()
    fan = request.form.get("fan_count", "").strip() or None
    hp = request.form.get("heatpipe_count", "").strip() or None
    vapor = 1 if request.form.get("has_vapor_chamber") == "1" else 0
    notes = request.form.get("notes", "").strip() or None
    model_id = request.form.get("model_id", "").strip() or None
    if not name:
        flash("Nama profil pendinginan wajib diisi.", "error")
        return redirect(url_for("admin"))
    try:
        cid = add_cooling_profile(
            name,
            fan_count=int(fan) if fan else None,
            heatpipe_count=int(hp) if hp else None,
            has_vapor_chamber=vapor,
            notes=notes,
            verification_status="Ditambahkan admin",
        )
        if model_id:
            link_model_cooling(int(model_id), cid, notes="Ditautkan dari admin")
        flash(f"Profil pendinginan '{name}' ditambahkan.", "success")
    except Exception as e:
        flash(f"Gagal menambah profil pendinginan: {e}", "error")
    return redirect(url_for("admin"))


@app.route("/admin/cooling/link", methods=["POST"])
@admin_required
def admin_cooling_link():
    model_id = request.form.get("model_id", "").strip()
    cooling_id = request.form.get("cooling_id", "").strip()
    notes = request.form.get("notes", "").strip() or None
    if not model_id or not cooling_id:
        flash("Model ID dan profil pendinginan wajib diisi.", "error")
        return redirect(url_for("admin"))
    try:
        link_model_cooling(int(model_id), int(cooling_id), notes=notes)
        flash("Profil pendinginan ditautkan ke model.", "success")
    except Exception as e:
        flash(f"Gagal menautkan: {e}", "error")
    return redirect(url_for("admin"))


@app.route("/admin/gpu/add", methods=["POST"])
@admin_required
def admin_gpu_add():
    name = request.form.get("name", "").strip()
    vendor = request.form.get("vendor", "").strip() or None
    gpu_type = request.form.get("gpu_type", "").strip() or None
    series = request.form.get("series", "").strip() or None
    vram = request.form.get("vram_gb", "").strip() or None
    model_id = request.form.get("model_id", "").strip() or None
    if not name:
        flash("Nama GPU wajib diisi.", "error")
        return redirect(url_for("admin"))
    try:
        gid = add_gpu(
            name, vendor=vendor, gpu_type=gpu_type, series=series,
            vram_gb=float(vram) if vram else None,
        )
        if model_id:
            link_model_gpu(int(model_id), gid, is_default=1)
        flash(f"GPU '{name}' ditambahkan.", "success")
    except Exception as e:
        flash(f"Gagal menambah GPU: {e}", "error")
    return redirect(url_for("admin"))


@app.route("/admin/reference/add", methods=["POST"])
@admin_required
def admin_reference_add():
    model_id = request.form.get("model_id")
    source_name = request.form.get("source_name", "").strip()
    url = request.form.get("url", "").strip()
    updated_at = request.form.get("updated_at", "").strip() or datetime.now().date().isoformat()
    source_type = request.form.get("source_type", "produsen").strip()
    if model_id and source_name:
        add_reference(int(model_id), source_name, url, updated_at, source_type)
        flash("Referensi ditambahkan.", "success")
    else:
        flash("Model ID dan nama sumber wajib diisi.", "error")
    return redirect(url_for("admin"))


# ============================================================
# ERROR HANDLER
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return render_template(
        "error.html",
        title="Halaman Tidak Ditemukan",
        message="Halaman yang Anda cari tidak tersedia.",
    ), 404


@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html",
        title="Kesalahan Server",
        message="Terjadi kesalahan internal. Silakan coba lagi.",
    ), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
