# ==========================================
# BASIS PENGETAHUAN SISTEM PAKAR
# Identifikasi Penyebab Laptop Overheating
# Metode Forward Chaining
#
# Sumber referensi:
# - Dell Support: how-to-troubleshoot-a-overheating-shutdown-or-thermal-issue
# - ASUS Support FAQ 1015064
# - HP Support: Computer Overheating (Windows)
# - Intel Support: How to Check if My Intel® Processor is Overheating
# ==========================================

# ------------------------------------------
# 1. GEJALA / FAKTA YANG DAPAT DIAMATI PENGGUNA
# ------------------------------------------
GEJALA = {
    "G01": "Ventilasi laptop terlihat tertutup debu atau kotoran",
    "G02": "Laptop diletakkan di permukaan lunak (tempat tidur/sofa) saat digunakan",
    "G03": "Suhu ruangan sekitar saat digunakan melebihi 35°C",
    "G04": "Udara yang keluar dari ventilasi terasa sangat panas",
    "G05": "Kipas berputar sangat cepat atau suara kipas jelas terdengar",
    "G06": "Kipas sama sekali tidak berputar dan bodi laptop sudah sangat panas",
    "G07": "Kipas mengeluarkan suara gesekan, derit, atau suara tidak normal",
    "G08": "Performa sistem jelas menurun (lag, respons lambat)",
    "G09": "Laptop pernah mati atau restart mendadak",
    "G10": "Penggunaan CPU di Task Manager terus-menerus tinggi",
    "G11": "Laptop sudah digunakan >2 tahun dan belum pernah dibersihkan bagian dalam",
    "G12": "Laptop terasa sangat panas meskipun hanya menjalankan aplikasi ringan",
}

# ------------------------------------------
# 2. KESIMPULAN ANTARA
# ------------------------------------------
KESIMPULAN_ANTARA = {
    "I01": "Aliran udara pendingin terhambat (dicurigai debu/kotoran atau penempatan)",
    "I02": "Indikasi masalah perangkat keras kipas pendingin",
    "I03": "Sistem berada dalam kondisi beban panas tinggi (bukan kesalahan pendinginan)",
}

# ------------------------------------------
# 3. KESIMPULAN AKHIR / DIAGNOSIS
# ------------------------------------------
KESIMPULAN_AKHIR = {
    "D01": {
        "nama": "Sistem pendingin tersumbat debu",
        "penjelasan": (
            "Ventilasi atau saluran pembuangan panas laptop terhalang debu/kotoran, "
            "menyebabkan udara panas tidak dapat keluar secara efektif."
        ),
        "solusi": (
            "Gunakan kaleng udara bertekanan untuk membersihkan ventilasi dari luar "
            "(hindari kompresor udara bertekanan tinggi). Jika suhu tetap tidak turun "
            "setelah dibersihkan, disarankan menghubungi teknisi untuk pembersihan menyeluruh."
        ),
        "sumber": "Dell Support: Debu adalah penyebab yang umum overheating; ASUS juga menekankan pembersihan ventilasi.",
        "tingkat": "kuat",
    },
    "D02": {
        "nama": "Kipas pendingin memerlukan pemeriksaan",
        "penjelasan": (
            "Terdapat indikasi kipas mungkin mengalami masalah mekanis atau koneksi. "
            "Catatan: kipas yang tidak berputar pada suhu rendah adalah strategi kontrol normal. "
            "Hanya 'tidak berputar + bodi sangat panas' atau 'suara abnormal' yang merupakan indikasi masalah."
        ),
        "solusi": (
            "Jangan membongkar sendiri. Disarankan menggunakan alat diagnostik resmi produsen "
            "(Dell SupportAssist / ASUS MyASUS) untuk pengujian perangkat keras, atau menghubungi "
            "pusat layanan resmi."
        ),
        "sumber": "Dell Support: 0 RPM + CPU>90°C dianggap abnormal; ASUS menyarankan menggunakan MyASUS untuk diagnosis perangkat keras.",
        "tingkat": "kuat/sedang",
    },
    "D03": {
        "nama": "Efektivitas konduksi panas menurun (perlu pemeriksaan teknisi)",
        "penjelasan": (
            "Ini hanya petunjuk, bukan diagnosis pasti. Thermal paste (TIM) dapat mengering atau "
            "kehilangan kinerja seiring waktu, tetapi 'lama tidak diganti' bukan bukti kegagalan. "
            "Perlu pembongkaran untuk memeriksa kondisi aktual."
        ),
        "solusi": (
            "Jangan mengganti thermal paste sendiri. Bawa ke teknisi profesional untuk pembongkaran "
            "dan pemeriksaan, konfirmasi apakah perlu penggantian."
        ),
        "sumber": "Intel Support: Thermal Interface Material mungkin mengering atau tidak terpasang dengan baik, perlu diperiksa; tetapi tidak disebutkan bahwa 'lama tidak diganti' berarti harus diganti.",
        "tingkat": "hanya petunjuk",
    },
    "D04": {
        "nama": "Beban kerja CPU/GPU terlalu tinggi",
        "penjelasan": (
            "Ini bukan kerusakan perangkat keras. Saat menjalankan program yang memakan sumber daya, "
            "CPU/GPU menghasilkan panas dalam jumlah besar dan kipas berputar cepat untuk membuang panas — "
            "ini perilaku normal. Selama suhu turun setelah beban menurun, sistem pendingin berfungsi normal."
        ),
        "solusi": (
            "Periksa Task Manager, tutup proses yang tidak diperlukan. Jika hanya panas saat tugas berat, "
            "pertimbangkan cooling pad atau kurangi beban. Jika beban ringan tetap panas, pertimbangkan "
            "masalah pendinginan."
        ),
        "sumber": "ASUS Support: Beban tinggi menyebabkan suhu naik dan kipas berputar cepat adalah fenomena normal; Intel juga membedakan throttle dengan kegagalan.",
        "tingkat": "sedang",
    },
    "D05": {
        "nama": "Sirkulasi udara eksternal tidak baik",
        "penjelasan": (
            "Permukaan lunak atau suhu ruangan terlalu tinggi menyebabkan pembuangan panas laptop terganggu."
        ),
        "solusi": (
            "Gunakan laptop di permukaan keras dan datar, pastikan ventilasi memiliki ruang, hindari "
            "penggunaan jangka panjang di tempat tidur/sofa. Jaga suhu ruangan dalam kisaran 5–35°C."
        ),
        "sumber": "Dell dan ASUS keduanya menyebutkan lingkungan penggunaan dan penempatan mempengaruhi pendinginan.",
        "tingkat": "kuat/sedang",
    },
    "D06": {
        "nama": "Bukti tidak mencukupi",
        "penjelasan": (
            "Berdasarkan gejala yang dipilih, tidak ada kombinasi aturan yang cukup untuk membentuk "
            "diagnosis yang jelas."
        ),
        "solusi": (
            "Disarankan melengkapi gejala, atau langsung membawa ke teknisi untuk pemeriksaan. Jangan "
            "memaksakan diagnosis berdasarkan informasi yang tidak lengkap."
        ),
        "sumber": "Prinsip sistem pakar: hindari pengambilan keputusan yang terlalu percaya diri.",
        "tingkat": "tidak mencukupi",
    },
}

# ------------------------------------------
# 4. ATURAN PRODUKSI IF-THEN
# ------------------------------------------
RULES = [
    # --- Kesimpulan antara ---
    {
        "id": "R01",
        "conditions": ["G01"],
        "operator": "AND",
        "result": "I01",
        "description": "Ventilasi terlihat tertutup debu/kotoran → aliran udara pendingin terhambat.",
        "source": "Dell: Debu adalah penyebab yang umum overheating.",
    },
    {
        "id": "R02",
        "conditions": ["G02"],
        "operator": "AND",
        "result": "I01",
        "description": "Penempatan di permukaan lunak → aliran udara pendingin terhambat.",
        "source": "Dell/ASUS: Permukaan lunak menghalangi ventilasi.",
    },
    {
        "id": "R03",
        "conditions": ["G03"],
        "operator": "AND",
        "result": "I01",
        "description": "Suhu ruangan >35°C → pendinginan terganggu.",
        "source": "ASUS: Lingkungan penggunaan yang disarankan adalah 5–35°C.",
    },
    {
        "id": "R04",
        "conditions": ["G06", "G04"],
        "operator": "AND",
        "result": "I02",
        "description": "Kipas tidak berputar dan bodi sangat panas → indikasi masalah perangkat keras kipas.",
        "source": "Dell: 0 RPM + CPU>90°C dianggap abnormal.",
    },
    {
        "id": "R05",
        "conditions": ["G07"],
        "operator": "AND",
        "result": "I02",
        "description": "Suara kipas abnormal → indikasi masalah perangkat keras kipas.",
        "source": "Dell: Suara gesekan/derit abnormal menunjukkan masalah kipas.",
    },
    {
        "id": "R06",
        "conditions": ["G05", "G10"],
        "operator": "AND",
        "result": "I03",
        "description": "Kipas cepat + CPU tinggi → beban panas tinggi (bukan kesalahan).",
        "source": "ASUS: Beban tinggi menyebabkan suhu naik dan kipas berputar cepat adalah reaksi normal.",
    },

    # --- Diagnosis akhir ---
    {
        "id": "R07",
        "conditions": ["I01", "G04"],
        "operator": "AND",
        "result": "D01",
        "description": "Aliran terhambat + udara ventilasi sangat panas → dicurigai sistem pendingin tersumbat debu.",
        "source": "Dell.",
    },
    {
        "id": "R08",
        "conditions": ["I01", "G12"],
        "operator": "AND",
        "result": "D01",
        "description": "Aliran terhambat + panas saat beban ringan → dicurigai sistem pendingin tersumbat debu.",
        "source": "Dell.",
    },
    {
        "id": "R09",
        "conditions": ["I02", "G09"],
        "operator": "AND",
        "result": "D02",
        "description": "Indikasi kipas + mati mendadak → perlu memeriksa kipas.",
        "source": "Dell: Mati mendadak mungkin terkait suhu, tetapi juga mungkin masalah daya.",
    },
    {
        "id": "R10",
        "conditions": ["I02", "G08"],
        "operator": "AND",
        "result": "D02",
        "description": "Indikasi kipas + performa turun → perlu memeriksa kipas.",
        "source": "Dell.",
    },
    {
        "id": "R11",
        "conditions": ["G11", "G12", "G04"],
        "operator": "AND",
        "result": "D03",
        "description": "Lama tidak dibersihkan + panas beban ringan + udara ventilasi panas → perlu memeriksa thermal paste (hanya petunjuk).",
        "source": "Intel: Thermal paste mungkin mengering, tetapi perlu pembongkaran untuk verifikasi.",
    },
    {
        "id": "R12",
        "conditions": ["G10", "G05", "G08"],
        "operator": "AND",
        "result": "D04",
        "description": "CPU tinggi + kipas cepat + lag → beban kerja terlalu tinggi.",
        "source": "ASUS/Intel.",
    },
    {
        "id": "R13",
        "conditions": ["G10", "G05"],
        "operator": "AND",
        "result": "D04",
        "description": "CPU tinggi + kipas cepat → beban tinggi (bukan kerusakan).",
        "source": "ASUS.",
    },
    {
        "id": "R14",
        "conditions": ["G02", "G04"],
        "operator": "AND",
        "result": "D05",
        "description": "Penempatan + udara ventilasi panas → sirkulasi tidak baik.",
        "source": "Dell/ASUS.",
    },
    {
        "id": "R15",
        "conditions": ["G02", "G03"],
        "operator": "AND",
        "result": "D05",
        "description": "Penempatan + suhu ruangan tinggi → sirkulasi tidak baik.",
        "source": "ASUS.",
    },
    # R16 diperbaiki: sebelumnya OR terlalu longgar (hanya G01 sudah cukup).
    # Sekarang membutuhkan minimal dua indikasi yang lebih spesifik.
    {
        "id": "R16",
        "conditions": ["G01", "G04", "G12"],
        "operator": "AND",
        "result": "D01",
        "description": "Debu + udara ventilasi panas + panas saat beban ringan → sistem pendingin tersumbat debu.",
        "source": "Dell/ASUS.",
    },
    # OR akademis: indikasi kipas abnormal dari SUARA atau dari (sudah di I02).
    # R17: salah satu gejala lingkungan ekstrem cukup untuk menegaskan D05 bila G04 ada.
    {
        "id": "R17",
        "conditions": ["G07", "G06"],
        "operator": "OR",
        "result": "I02",
        "description": "Suara kipas abnormal ATAU kipas tidak berputar (dengan konteks panas terpisah) → indikasi masalah kipas.",
        "source": "Dell: suara abnormal atau 0 RPM pada suhu tinggi.",
    },
]
