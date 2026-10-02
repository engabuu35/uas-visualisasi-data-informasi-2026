"""Satu Negeri, 514 Wajah Ekonomi - PDRB kabupaten/kota Indonesia, TW I-II 2026.

Struktur "martini glass" (Segel & Heer, 2010): halaman Cerita dipandu penulis,
lalu tiga halaman Jelajah membebaskan pembaca menggali sendiri.
"""

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from config import GEOJSON, PROCESSED_CSV  # noqa: E402
from ui import inject_css  # noqa: E402

st.set_page_config(
    page_title="514 Wajah Ekonomi",
    page_icon="assets/favicon.png" if (ROOT / "assets" / "favicon.png").exists() else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

if not (PROCESSED_CSV.exists() and GEOJSON.exists()):
    st.error("Data olahan belum ada. Jalankan dulu: `python scripts/prepare_data.py`")
    st.stop()

inject_css()

pages = [
    st.Page("views/cerita.py", title="Cerita", default=True),
    st.Page("views/struktur.py", title="Struktur ekonomi"),
    st.Page("views/peta.py", title="Peta"),
    st.Page("views/hierarki.py", title="Hierarki"),
    st.Page("views/tentang.py", title="Data & metode"),
]
st.navigation(pages, position="top").run()
