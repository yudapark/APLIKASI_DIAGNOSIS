"""
Skenario pengujian formal Forward Chaining
Minimal 5 skenario sesuai persyaratan UTS Sistem Pakar.

Setiap skenario:
- input gejala
- diagnosis yang diharapkan (kode)
- aturan yang diharapkan terpicu (opsional, subset)
- catatan

PENTING: Diagnosis tidak bergantung pada merek/model.
"""

from inference_engine import forward_chaining

SCENARIOS = [
    {
        "id": "S01",
        "nama": "Debu + udara panas ventilasi",
        "gejala": ["G01", "G04"],
        "expected_diagnosis": ["D01"],
        "expected_rules_subset": ["R01", "R07"],
        "expected_antara": ["I01"],
        "catatan": "Aliran terhambat + udara panas → D01 (tersumbat debu).",
    },
    {
        "id": "S02",
        "nama": "Kipas mati + bodi sangat panas + mati mendadak",
        "gejala": ["G06", "G04", "G09"],
        "expected_diagnosis": ["D02"],
        "expected_rules_subset": ["R04", "R09"],
        "expected_antara": ["I02"],
        "catatan": "Indikasi hardware kipas + mati mendadak → D02.",
    },
    {
        "id": "S03",
        "nama": "CPU tinggi + kipas cepat + lag",
        "gejala": ["G10", "G05", "G08"],
        "expected_diagnosis": ["D04"],
        "expected_rules_subset": ["R06", "R12"],
        "expected_antara": ["I03"],
        "catatan": "Beban kerja tinggi (bukan kerusakan pendinginan).",
    },
    {
        "id": "S04",
        "nama": "Penempatan di sofa + suhu ruangan tinggi",
        "gejala": ["G02", "G03"],
        "expected_diagnosis": ["D05"],
        "expected_rules_subset": ["R02", "R03", "R15"],
        "expected_antara": ["I01"],
        "catatan": "Sirkulasi udara eksternal tidak baik.",
    },
    {
        "id": "S05",
        "nama": "Lama tidak dibersihkan + panas beban ringan + udara panas",
        "gejala": ["G11", "G12", "G04"],
        "expected_diagnosis": ["D03"],
        "expected_rules_subset": ["R11"],
        "expected_antara": [],
        "catatan": "Hanya petunjuk thermal paste — perlu teknisi.",
    },
    {
        "id": "S06",
        "nama": "Gejala minimal / tidak cukup",
        "gejala": ["G08"],
        "expected_diagnosis": ["D06"],
        "expected_rules_subset": [],
        "expected_antara": [],
        "catatan": "Bukti tidak mencukupi → fallback D06.",
    },
    {
        "id": "S07",
        "nama": "Debu + panas beban ringan + udara panas (R16)",
        "gejala": ["G01", "G04", "G12"],
        "expected_diagnosis": ["D01"],
        "expected_rules_subset": ["R01", "R07", "R08", "R16"],
        "expected_antara": ["I01"],
        "catatan": "Kombinasi kuat untuk D01 setelah perbaikan R16 (AND).",
    },
    {
        "id": "S08",
        "nama": "Independensi merek (gejala sama → diagnosis sama)",
        "gejala": ["G02", "G04"],
        "expected_diagnosis": ["D01", "D05"],
        "expected_rules_subset": ["R02", "R07", "R14"],
        "expected_antara": ["I01"],
        "catatan": "G02→I01; I01+G04→D01; G02+G04→D05. Multi-diagnosis valid. Identik untuk semua merek.",
    },
]


def run_scenario(scenario):
    hasil = forward_chaining(scenario["gejala"])
    codes = sorted(d["kode"] for d in hasil["diagnosis"])
    expected = sorted(scenario["expected_diagnosis"])
    rules = [r["id"] for r in hasil["aturan"]]
    antara = sorted(hasil.get("kesimpulan_antara_tercapai") or [])

    diag_ok = codes == expected
    # subset rules: every expected rule must appear
    rules_ok = all(rid in rules for rid in scenario.get("expected_rules_subset") or [])
    antara_expected = sorted(scenario.get("expected_antara") or [])
    # jika expected_antara kosong, tidak memaksa (boleh ada atau tidak)
    if antara_expected:
        antara_ok = antara == antara_expected or set(antara_expected).issubset(set(antara))
    else:
        antara_ok = True

    passed = diag_ok and rules_ok and antara_ok
    return {
        "id": scenario["id"],
        "nama": scenario["nama"],
        "passed": passed,
        "gejala": scenario["gejala"],
        "expected_diagnosis": expected,
        "actual_diagnosis": codes,
        "expected_rules_subset": scenario.get("expected_rules_subset") or [],
        "actual_rules": rules,
        "expected_antara": antara_expected,
        "actual_antara": antara,
        "diag_ok": diag_ok,
        "rules_ok": rules_ok,
        "antara_ok": antara_ok,
        "catatan": scenario.get("catatan", ""),
    }


def run_all_scenarios():
    return [run_scenario(s) for s in SCENARIOS]


if __name__ == "__main__":
    results = run_all_scenarios()
    passed = sum(1 for r in results if r["passed"])
    print(f"Hasil: {passed}/{len(results)} skenario lulus\n")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['id']} {r['nama']}")
        print(f"  Gejala   : {r['gejala']}")
        print(f"  Expected : {r['expected_diagnosis']} | Actual: {r['actual_diagnosis']}")
        if not r["passed"]:
            print(f"  Rules exp: {r['expected_rules_subset']} | act: {r['actual_rules']}")
            print(f"  Antara   : exp {r['expected_antara']} act {r['actual_antara']}")
        print()
