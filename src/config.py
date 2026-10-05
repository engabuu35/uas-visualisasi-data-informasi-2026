"""Konstanta proyek: lokasi berkas, metadata sumber, sektor, wilayah, dan palet."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- Berkas ---
RAW_XLSX = ROOT / "data" / "raw" / "pdrb_2026.xlsx"
RAW_GEOJSON = ROOT / "data" / "geo" / "kabkota.geojson"

PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_CSV = PROCESSED_DIR / "pdrb_long.csv"        # tidy: 1 baris = wilayah x sektor x triwulan
REGIONS_CSV = PROCESSED_DIR / "wilayah.csv"            # kode, nama, provinsi, pulau, titik pusat
GEOJSON = PROCESSED_DIR / "kabkota_simplified.geojson"  # batas yang sudah disederhanakan untuk web

# --- Sumber data ---
BPS_TABLE_TITLE = (
    "PDRB Triwulanan Atas Dasar Harga Konstan (2010=100) Menurut 17 Kategori "
    "Lapangan Usaha di Kabupaten/Kota (Milyar Rupiah), 2026"
)
BPS_SOURCE_URL = (
    "https://www.bps.go.id/id/statistics-table/2/Mjc3NSMy/"
    "pdrb-triwulanan-atas-dasar-harga-konstan-2010-100-menurut-17-kategori-"
    "lapangan-usaha-di-kabupaten-kota-milyar-rupiah.html"
)
ACCESS_DATE = "27 September 2026"
# Identitas pembuat untuk footer di setiap halaman (ui.footer).
APP_TITLE = "514 Wajah Ekonomi"
AUTHOR = "Arif Budiman"
AUTHOR_ID = "222312994"
AUTHOR_CLASS = "3SD2"
AUTHOR_EMAIL = "222312994@stis.ac.id"
COURSE = "UAS Visualisasi Data dan Informasi"
INSTITUTION = "Politeknik Statistika STIS"
MADE_DATE = "3 Oktober 2026"
# Kutipan sumber tunggal; dipakai di bawah semua visualisasi (ui.source, cerita.source).
SOURCE_CITE = ("Badan Pusat Statistik, PDRB Triwulanan Atas Dasar Harga Konstan (2010=100) Menurut "
               "17 Kategori Lapangan Usaha di Kabupaten/Kota 2026")

# Batas wilayah: data pendukung non-BPS.
GEO_SOURCE = "Bahan praktikum Sistem Informasi Geografis, Dr. Rindang Bangun Prasetyo, Politeknik Statistika STIS"
GEO_SOURCE_URL = ""

SOURCE_NOTE = "Sumber: BPS, PDRB ADHK 2010 kab/kota, 2026 (diolah)"

PERIODS = ["Triwulan I", "Triwulan II"]

# Parameter metode yang ikut dikutip di teks, agar teks dan perhitungan selalu sama.
SPATIAL_K = 6          # tetangga terdekat untuk bobot spasial
PERMUTATIONS = 999     # permutasi uji Moran's I / LISA
N_CLUSTERS = 6         # klaster Ward (silhouette tertinggi pada k = 3-8)
PERIOD_SHORT = {"Triwulan I": "TW I", "Triwulan II": "TW II"}

# --- Sektor (17 kategori KBLI): kode -> (nama singkat, kelompok) ---
SECTORS = {
    "A": ("Pertanian", "Primer"),
    "B": ("Pertambangan", "Primer"),
    "C": ("Industri pengolahan", "Sekunder"),
    "D": ("Listrik & gas", "Sekunder"),
    "E": ("Air & limbah", "Sekunder"),
    "F": ("Konstruksi", "Sekunder"),
    "G": ("Perdagangan", "Tersier"),
    "H": ("Transportasi", "Tersier"),
    "I": ("Akomodasi & makan minum", "Tersier"),
    "J": ("Informasi & komunikasi", "Tersier"),
    "K": ("Keuangan", "Tersier"),
    "L": ("Real estat", "Tersier"),
    "M,N": ("Jasa perusahaan", "Tersier"),
    "O": ("Administrasi pemerintahan", "Tersier"),
    "P": ("Pendidikan", "Tersier"),
    "Q": ("Kesehatan", "Tersier"),
    "R,S,T,U": ("Jasa lainnya", "Tersier"),
}
SECTOR_CODES = list(SECTORS)
SECTOR_SHORT = {k: v[0] for k, v in SECTORS.items()}
SECTOR_GROUP = {k: v[1] for k, v in SECTORS.items()}
TOTAL_LABEL = "Produk Domestik Regional Bruto"

# --- Provinsi (kode BPS 2019, 34 provinsi) -> (nama tampilan, pulau/kawasan) ---
PROVINCES = {
    "11": ("Aceh", "Sumatera"),
    "12": ("Sumatera Utara", "Sumatera"),
    "13": ("Sumatera Barat", "Sumatera"),
    "14": ("Riau", "Sumatera"),
    "15": ("Jambi", "Sumatera"),
    "16": ("Sumatera Selatan", "Sumatera"),
    "17": ("Bengkulu", "Sumatera"),
    "18": ("Lampung", "Sumatera"),
    "19": ("Kep. Bangka Belitung", "Sumatera"),
    "21": ("Kepulauan Riau", "Sumatera"),
    "31": ("DKI Jakarta", "Jawa"),
    "32": ("Jawa Barat", "Jawa"),
    "33": ("Jawa Tengah", "Jawa"),
    "34": ("DI Yogyakarta", "Jawa"),
    "35": ("Jawa Timur", "Jawa"),
    "36": ("Banten", "Jawa"),
    "51": ("Bali", "Bali–Nusa Tenggara"),
    "52": ("Nusa Tenggara Barat", "Bali–Nusa Tenggara"),
    "53": ("Nusa Tenggara Timur", "Bali–Nusa Tenggara"),
    "61": ("Kalimantan Barat", "Kalimantan"),
    "62": ("Kalimantan Tengah", "Kalimantan"),
    "63": ("Kalimantan Selatan", "Kalimantan"),
    "64": ("Kalimantan Timur", "Kalimantan"),
    "65": ("Kalimantan Utara", "Kalimantan"),
    "71": ("Sulawesi Utara", "Sulawesi"),
    "72": ("Sulawesi Tengah", "Sulawesi"),
    "73": ("Sulawesi Selatan", "Sulawesi"),
    "74": ("Sulawesi Tenggara", "Sulawesi"),
    "75": ("Gorontalo", "Sulawesi"),
    "76": ("Sulawesi Barat", "Sulawesi"),
    "81": ("Maluku", "Maluku–Papua"),
    "82": ("Maluku Utara", "Maluku–Papua"),
    "91": ("Papua Barat", "Maluku–Papua"),
    "94": ("Papua", "Maluku–Papua"),
}
ISLAND_ORDER = [
    "Sumatera", "Jawa", "Bali–Nusa Tenggara", "Kalimantan", "Sulawesi", "Maluku–Papua",
]

# --- Babak cerita (warnanya di theme.ACT_COLORS, urutan sama) ---
ACTS = [
    {"key": "pusat", "roman": "I", "label": "Konsentrasi PDRB"},
    {"key": "jurang", "roman": "II", "label": "Pola Ekonomi"},
    {"key": "arus", "roman": "III", "label": "Pertumbuhan"},
    {"key": "kini", "roman": "IV", "label": "Pergeseran"},
]
