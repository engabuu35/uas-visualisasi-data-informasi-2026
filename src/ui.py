"""Elemen tampilan kecil yang dipakai bersama oleh semua halaman."""

import streamlit as st

from config import ACCESS_DATE, BPS_SOURCE_URL, INK, INK_MUTED, INK_SOFT

CSS = """
<style>
[data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }
h1 { font-size: 2.35rem !important; line-height: 1.15 !important; letter-spacing: -0.01em; }
h2 { font-size: 1.55rem !important; line-height: 1.25 !important; margin-top: 1.6rem !important; }
h3 { font-size: 1.15rem !important; }
p, li { font-size: 1.04rem; line-height: 1.62; }
.lede { font-size: 1.2rem; line-height: 1.6; color: %(soft)s; max-width: 46rem; margin: .2rem 0 1.4rem; }
.prose { max-width: 44rem; }
.src { font-size: .8rem; color: %(muted)s; margin: -.4rem 0 1.2rem; }
.src a { color: %(muted)s; }
.figure-num { font-variant-numeric: tabular-nums; }
.stat-row { display: flex; flex-wrap: wrap; gap: 1.6rem 2.6rem; margin: .4rem 0 1.4rem; }
.stat-row div { min-width: 9rem; }
.stat-row b { display: block; font-size: 1.9rem; font-weight: 700; line-height: 1.1; color: %(ink)s; font-variant-numeric: tabular-nums; }
.stat-row span { font-size: .88rem; color: %(soft)s; }
.note { border-left: 3px solid #C98500; padding: .3rem 0 .3rem .9rem; color: %(soft)s; max-width: 46rem; }
.swatches { display: flex; flex-wrap: wrap; gap: .35rem 1.1rem; align-items: center; font-size: .86rem; color: %(soft)s; margin: .5rem 0 .3rem; }
.swatches b { font-weight: 600; margin-right: .3rem; }
.swatches span { display: inline-flex; align-items: center; gap: .4rem; }
.swatches i { width: 14px; height: 14px; border-radius: 3px; display: inline-block; box-shadow: inset 0 0 0 1px rgba(255,255,255,.14); }
.swatches em { font-style: normal; color: %(muted)s; }
.legend-dots span { display: inline-flex; align-items: center; gap: .35rem; margin-right: 1rem; font-size: .88rem; color: %(soft)s; }
.legend-dots i { display: inline-block; border-radius: 50%%; background: %(ink)s; opacity: .45; }
@media (max-width: 640px) {
  h1 { font-size: 1.75rem !important; }
  .lede { font-size: 1.06rem; }
  .stat-row b { font-size: 1.5rem; }
}
</style>
""" % {"muted": INK_MUTED, "soft": INK_SOFT, "ink": INK}


def inject_css():
    st.html(CSS)


def lede(text: str):
    st.html(f'<p class="lede">{text}</p>')


def source(extra: str = ""):
    """Baris sumber di bawah setiap visualisasi (wajib menurut ketentuan ujian)."""
    tail = f" · {extra}" if extra else ""
    st.html(f'<p class="src">Sumber: BPS, PDRB ADHK 2010 menurut lapangan usaha, kab/kota 2026 '
            f'(<a href="{BPS_SOURCE_URL}" target="_blank">tabel</a>, diakses {ACCESS_DATE}), diolah{tail}.</p>')


def stats(items):
    """items: [(angka, keterangan), ...]"""
    cells = "".join(f"<div><b>{v}</b><span>{k}</span></div>" for v, k in items)
    st.html(f'<div class="stat-row">{cells}</div>')


def note(text: str):
    st.html(f'<div class="note">{text}</div>')


def swatches(title: str, labels, colors, note_text: str = ""):
    """Legenda kelas peta sebagai HTML: membungkus rapi di layar sempit,
    dan teksnya tetap berwarna tinta (bukan warna kelas)."""
    items = "".join(
        f'<span><i style="background:{c}"></i>{lab}</span>' for lab, c in zip(labels, colors)
    )
    tail = f'<em>{note_text}</em>' if note_text else ""
    st.html(f'<div class="swatches"><b>{title}</b>{items}{tail}</div>')
