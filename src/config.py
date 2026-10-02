"""Konstanta proyek: lokasi berkas, metadata sumber, sektor, wilayah, dan palet."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Berkas
# ---------------------------------------------------------------------------
RAW_XLSX = ROOT / "data" / "raw" / "pdrb_2026.xlsx"
RAW_GEOJSON = ROOT / "data" / "geo" / "kabkota.geojson"

PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_CSV = PROCESSED_DIR / "pdrb_long.csv"        # tidy: 1 baris = wilayah x sektor x triwulan
REGIONS_CSV = PROCESSED_DIR / "wilayah.csv"            # kode, nama, provinsi, pulau, titik pusat
GEOJSON = PROCESSED_DIR / "kabkota_simplified.geojson"  # batas yang sudah disederhanakan untuk web

# ---------------------------------------------------------------------------
# Sumber data
# ---------------------------------------------------------------------------
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

# Batas wilayah adalah data pendukung non-BPS. Isi sesuai asal berkas
# kabkota.geojson yang Anda pakai (penyedia, tahun batas, dan URL).
GEO_SOURCE = "Batas administrasi kabupaten/kota (kode wilayah BPS 2019)"
GEO_SOURCE_URL = ""

SOURCE_NOTE = "Sumber: BPS, PDRB ADHK 2010 kab/kota, 2026 (diolah)"

PERIODS = ["Triwulan I", "Triwulan II"]

# Parameter metode yang ikut dikutip di teks. Disimpan di sini agar teks dan
# perhitungan tidak bisa berbeda.
SPATIAL_K = 6          # tetangga terdekat untuk bobot spasial
PERMUTATIONS = 999     # permutasi uji Moran's I / LISA
N_CLUSTERS = 6         # klaster Ward (silhouette tertinggi pada k = 3-8)
PERIOD_SHORT = {"Triwulan I": "TW I", "Triwulan II": "TW II"}

# ---------------------------------------------------------------------------
# Sektor (17 kategori lapangan usaha KBLI)
# kode -> (nama singkat untuk grafik, kelompok)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Provinsi (kode BPS 2019, 34 provinsi) -> (nama tampilan, pulau/kawasan)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Warna (tema gelap)
# Latar gelap kebiruan, bukan hitam murni. Semua warna yang membawa data
# diambil dari palet rujukan yang sudah divalidasi untuk permukaan gelap
# (validate_palette.js, simulasi CVD Machado 2009). Hasil uji dicatat di
# samping setiap palet agar tidak "dirapikan" tanpa diuji ulang.
# ---------------------------------------------------------------------------
INK = "#E8E4DE"          # teks utama, kontras 14,7:1 terhadap PAPER
INK_SOFT = "#B5AEA6"     # teks sekunder, 8,5:1
INK_MUTED = "#8A847D"    # sumbu, catatan, 5,0:1
PAPER = "#0F1318"        # latar halaman
SURFACE = "#141A21"      # latar grafik
GRID = "#232A33"
RULE = "#38404A"
ACCENT = "#C98500"       # amber: identitas aplikasi
ACCENT_DEEP = "#F4B175"  # penekanan; di latar gelap "lebih kuat" berarti lebih terang
CONTEXT_GRAY = "#4A4F57"  # elemen yang tidak sedang disorot / tidak dapat dihitung
LAND = "#20252A"          # daratan pada peta SVG cerita
LAND_EDGE = "#2D3135"

# Kategorikal 6 slot, urutan tetap dari palet rujukan (mode gelap).
# Lolos semua uji pada pasangan bersebelahan (CVD terburuk dE 8,4).
# Enam warna tidak bisa lolos uji semua-pasangan, jadi setiap tampilan klaster
# wajib punya encoding kedua: bentuk penanda (biplot), label langsung
# (dumbbell), atau small multiples satu warna per peta (cerita).
CLUSTER_COLORS = ["#3987E5", "#D95926", "#199E70", "#C98500", "#D55181", "#008300"]
CLUSTER_SYMBOLS = ["circle", "diamond", "square", "triangle-up", "cross", "x"]

# Sekuensial satu hue (jingga), urutan nilai rendah -> tinggi. Di latar gelap
# jangkarnya terbalik: nilai tinggi = lebih terang. Lolos uji ordinal
# (monoton, dL >= 0,06, ujung tergelap 2,3:1 terhadap SURFACE).
SEQ_ORANGE = ["#76491D", "#9B5E1E", "#C07525", "#E28E3A", "#F4B175", "#FED5B2"]

# Divergen biru <-> jingga dengan titik tengah abu netral, untuk LQ dan
# pertumbuhan. DIV_BLUE berurut ekstrem -> dekat tengah, DIV_ORANGE dekat
# tengah -> ekstrem; kedua lengan setara lightness-nya (0,43 / 0,62 / 0,81).
DIV_BLUE = ["#9EC5F4", "#3987E5", "#184F95"]
DIV_MID = "#44454A"
DIV_ORANGE = ["#834018", "#D36C1B", "#EFB787"]

# LISA: lengan jingga (tinggi) dan biru (rendah); kelas "campuran" memakai
# langkah pucat dari lengan yang sama. Uji semua-pasangan untuk empat kelas
# bermakna: CVD terburuk dE 15,0, penglihatan normal 16,9. "Tidak signifikan"
# sengaja resesif dan selalu dibantu legenda + tooltip.
LISA_COLORS = {
    "Tinggi-Tinggi": "#D36C1B",
    "Rendah-Rendah": "#3987E5",
    "Tinggi-Rendah": "#EFB787",
    "Rendah-Tinggi": "#9EC5F4",
    "Tidak signifikan": "#30353C",
}

# ---------------------------------------------------------------------------
# Babak cerita. Aksen tiap babak membawa makna, bukan sekadar hiasan, dan
# diambil dari slot kategorikal yang sama supaya tetap ramah buta warna
# (merah-hijau pada arahan aslinya justru pasangan yang hilang pada
# deuteranopia). "tint" adalah latar babak; gradien hero berakhir tepat di
# tint babak I sehingga peralihan hero -> cerita tidak terlihat jahitannya.
# ---------------------------------------------------------------------------
ACTS = [
    {"key": "pusat", "roman": "I", "label": "Pusat", "accent": "#C98500", "tint": "#181107"},
    {"key": "jurang", "roman": "II", "label": "Jurang", "accent": "#D95926", "tint": "#1B0F0B"},
    {"key": "arus", "roman": "III", "label": "Arus balik", "accent": "#199E70", "tint": "#091610"},
    {"key": "kini", "roman": "IV", "label": "Belum berubah", "accent": "#3987E5", "tint": "#0C131C"},
]
