"""Satu Negeri, 514 Wajah Ekonomi - PDRB kabupaten/kota Indonesia, TW I-II 2026.

Struktur "martini glass" (Segel & Heer, 2010): halaman Cerita dipandu penulis,
lalu tiga halaman Jelajah membebaskan pembaca menggali sendiri.
"""

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import theme  # noqa: E402
from config import GEOJSON, PROCESSED_CSV  # noqa: E402
from ui import TEXT_SIZES, footer, inject_css  # noqa: E402

st.set_page_config(
    page_title="514 Wajah Ekonomi",
    page_icon="assets/favicon.png" if (ROOT / "assets" / "favicon.png").exists() else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

if not (PROCESSED_CSV.exists() and GEOJSON.exists()):
    st.error("Data olahan belum ada. Jalankan dulu: `python scripts/prepare_data.py`")
    st.stop()

# Panel Aksesibilitas melayang di tepi kiri (menggantikan sidebar). Pembaca tema ikut di sini:
# wadahnya fixed, jadi keduanya tidak memakan ruang halaman.
with st.container(key="a11y"):
    theme.sync()
    with st.popover("Aksesibilitas"):
        st.markdown("**Aksesibilitas**")
        st.segmented_control("Ukuran teks", TEXT_SIZES, key="a11y_text", default=TEXT_SIZES[0])
        st.toggle("Hentikan animasi", key="a11y_still",
                  help="Cerita tampil tanpa transisi dan efek gulir. Otomatis berlaku juga bila "
                       "perangkat Anda diatur untuk mengurangi gerak.")
        st.radio(
            "Palet warna", theme.VARIANTS, key="palette",
            help="Kedua palet tetap terbaca oleh penyandang buta warna (protanopia, deuteranopia, "
                 "dan tritanopia). Viridis: warna klaster tervalidasi, Viridis untuk besaran, dan "
                 "biru–jingga untuk nilai di atas/bawah acuan. Okabe-Ito / Cividis: warna klaster "
                 "Okabe-Ito, Cividis untuk besaran, dan merah–biru untuk nilai di atas/bawah acuan.",
        )
        st.caption("Tema terang/gelap: klik menu ⋮ di kanan atas, lalu pilih System (mengikuti "
                   "pengaturan perangkat), Light, atau Dark.")
inject_css(text_size=st.session_state.get("a11y_text") or TEXT_SIZES[0],
           still=bool(st.session_state.get("a11y_still")))

pages = [
    st.Page("views/cerita.py", title="Potret PDRB", default=True),
    st.Page("views/struktur.py", title="Pola ekonomi"),
    st.Page("views/peta.py", title="Peta"),
    st.Page("views/hierarki.py", title="Wilayah & sektor"),
    st.Page("views/tentang.py", title="Data & metode"),
]
current = st.navigation(pages, position="top")
# Latar isi halaman Jelajah mengikuti warna babaknya; navbar tetap warna bawaan di semua halaman.
# Bukan di .stApp: theme.sync membaca latar itu.
PAGE_BG = {"struktur": 1, "peta": 2, "hierarki": 3, "tentang": 4}
if current.url_path in PAGE_BG:
    i = PAGE_BG[current.url_path]
    st.html(f'<style>[data-testid="stMain"] {{ background: var(--tk-page{i}); }} '
            f':root {{ --pg-accent: var(--tk-act{i}); }}</style>')
current.run()
footer()
