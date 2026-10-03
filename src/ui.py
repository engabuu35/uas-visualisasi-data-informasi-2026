"""Elemen tampilan kecil yang dipakai bersama oleh semua halaman."""

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

import theme
from config import (
    ACCESS_DATE, APP_TITLE, AUTHOR, AUTHOR_CLASS, AUTHOR_EMAIL, AUTHOR_ID, BPS_SOURCE_URL, COURSE,
    INSTITUTION, MADE_DATE, SOURCE_CITE,
)

# Warna lewat variabel --tk-* (theme.css_vars) sehingga ikut berganti seketika
# saat tema diganti; tidak ada kode warna di sini.
CSS = """
/* Navigasi atas rata tengah dan sedikit lebih besar (14 -> 16 px) agar menyatu
   dengan tipografi halaman cerita. Selektor memakai data-testid dan kelas
   rc-overflow (pustaka), bukan kelas emotion yang namanya berubah tiap versi. */
/* Area kanan (menu) punya lebar minimum tetap 12,5 rem sedangkan kiri (tombol
   sidebar) hanya selebar tombol, jadi flex biasa tidak bisa menengahkan. rc-overflow
   (anak langsung toolbar) dibuat absolut dengan jarak kiri = kanan sehingga item
   di dalamnya pas di tengah halaman. Lebar dibiarkan tetap agar deteksi muat/tidak
   muat (menu "...") di pustaka rc-overflow tetap bekerja. */
[data-testid="stToolbar"] { position: relative; }
[data-testid="stToolbar"] .rc-overflow {
  position: absolute; top: 0; bottom: 0; left: 14rem; right: 14rem; width: auto !important; max-width: none !important;
  display: flex; align-items: center; justify-content: center; min-width: 0; z-index: 1;
}
@media (max-width: 1100px) {
  /* Layar sempit: kurangi jarak simetris (14 -> 8 rem) agar kelima item tidak runtuh ke menu "...". */
  [data-testid="stToolbar"] .rc-overflow { left: 8rem; right: 8rem; }
}
[data-testid="stTopNavLink"], [data-testid="stTopNavLink"] * { font-size: .95rem !important; font-family: var(--font-head) !important; }
[data-testid="stTopNavLink"] { padding: .4rem .85rem !important; }
/* Tombol segmented/pills setinggi kotak dropdown (2,5 rem) supaya satu baris kontrol terlihat simetris. */
[data-testid="stMain"] [data-testid="stButtonGroup"] button { min-height: 2.5rem; padding-top: 0; padding-bottom: 0; }
/* Segmen/pill terpilih: isi persik yang sama di semua halaman (bawaan Streamlit hanya 10% oranye di atas
   latar halaman, sehingga di halaman berlatar hijau atau merah muda warnanya ikut berubah). */
[data-testid="stMain"] [data-testid="stButtonGroup"] button[aria-checked="true"] {
  background-color: var(--tk-seg-active) !important; border-color: var(--tk-accent) !important; color: var(--tk-accent) !important; }
/* Parallel coordinates digambar di kanvas WebGL; pada sebagian kartu grafis garisnya hilang bertahap saat halaman
   digulir. Lapisan komposit sendiri + isolasi gambar mengurangi masalah itu (kanvas juga dibuat tanpa skala 2x). */
[class*="st-key-pc_chart_"] { transform: translateZ(0); will-change: transform; contain: paint; }
/* Kartu unduhan data (Data & metode): gaya kartu halaman Cerita, yaitu latar krem, pita judul berikon, dan
   aksen hijau (warna babak III), dengan tombol unduh hijau. */
.st-key-dl-cards [data-testid="stHorizontalBlock"] { align-items: stretch; gap: 1.2rem; }
.st-key-dl-cards [data-testid="stColumn"] { background-color: var(--tk-paper); border: 1px solid var(--tk-hairline);
  border-radius: 1rem; padding: 1.15rem 1.35rem 1.25rem; box-shadow: 0 6px 18px -10px color-mix(in srgb, var(--tk-act3) 45%, transparent); }
.st-key-dl-cards [data-testid="stColumn"] > div { gap: .6rem; height: 100%; }
.st-key-dl-cards [class*="st-key-dl-h"] { background: color-mix(in srgb, var(--tk-act3) 14%, transparent); border-radius: .7rem;
  padding: 0 .75rem; margin: -.35rem -.5rem .2rem; min-height: 3.6rem; padding-top: .45rem; padding-bottom: .45rem; display: flex; flex-direction: column; justify-content: center; }
.st-key-dl-cards [class*="st-key-dl-h"] > div, .st-key-dl-cards [class*="st-key-dl-h"] [data-testid="stMarkdownContainer"] { margin: 0; }
.st-key-dl-cards [class*="st-key-dl-h"] p:first-child { font-size: 1.3rem; font-weight: 700; letter-spacing: 0; text-transform: none;
  color: var(--tk-ink); line-height: 1.25; }
.st-key-dl-cards [class*="st-key-dl-h"] p:first-child + p { margin-top: .05rem !important; font-size: .8rem; font-weight: 500;
  color: var(--tk-soft); }
.st-key-dl-cards [data-testid="stMarkdownContainer"] p { font-size: .92rem; color: var(--tk-soft); line-height: 1.55; }
.st-key-dl-cards .dl-meta { font-size: .78rem; color: var(--tk-muted); margin: 0; }
.st-key-dl-cards [class*="st-key-dl-h"] p { margin: 0 !important; }
.st-key-dl-cards [class*="st-key-dl-h"] [data-testid="stIconMaterial"] { color: var(--tk-act3); margin-right: .35rem; }
.st-key-dl-cards [data-testid="stElementContainer"]:has([data-testid="stDownloadButton"]) { margin-top: auto; }
.st-key-dl-cards [data-testid="stMarkdownContainer"] p { text-align: left !important; }
.st-key-dl-cards [data-testid="stDownloadButton"] button { min-height: 2.5rem; font-weight: 600; color: var(--tk-act3);
  background-color: color-mix(in srgb, var(--tk-act3) 14%, var(--tk-paper)); border-color: var(--tk-act3); }
.st-key-dl-cards [data-testid="stDownloadButton"] button:hover { filter: brightness(.96); }
.st-key-moran_text p { text-align: justify; text-justify: inter-word; }
/* Tombol reset brushing: kecil dan rata kanan, bukan selebar kolom; berwarna sama dengan segmen terpilih. */
.st-key-pc_reset_btn { display: flex; justify-content: flex-end; width: 100% !important; }
.st-key-pc_reset_btn button { min-height: 2rem; padding: .15rem .85rem; font-size: .85rem; border-radius: .6rem;
  background-color: var(--tk-seg-active); border-color: var(--tk-accent); color: var(--tk-accent); }
.st-key-pc_reset_btn button:hover { filter: brightness(.96); }
[data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 5.5rem; padding-bottom: 4rem; }
h1, h2, h3 { font-family: var(--font-head) !important; }
h1 { font-size: 2.35rem !important; line-height: 1.15 !important; letter-spacing: -0.01em; }
h2 { font-size: 1.55rem !important; line-height: 1.25 !important; margin-top: 1.6rem !important; }
h3 { font-size: 1.15rem !important; }
p, li { font-size: 1.04rem; line-height: 1.62; }
.lede { font-size: 1.2rem; line-height: 1.6; color: var(--tk-soft); max-width: 46rem; margin: .2rem 0 1.4rem; }
.prose { max-width: 44rem; }
.src { font-size: .58rem; color: var(--tk-muted); margin: -.4rem 0 1.2rem; text-align: center; }
.src a { color: var(--tk-muted); }
/* Judul grafik: satu gaya untuk semua halaman (sama dengan .ws-chart-t di Cerita). Rata tengah,
   satu baris, ukuran sama untuk semua judul pada lebar layar yang sama (1rem di laptop, sedikit
   lebih kecil di ponsel). Teks judul dibuat cukup pendek agar muat di kolom tersempit; elipsis
   hanya pengaman, dan teks lengkapnya tetap ada di atribut title. */
.chart-t { font-family: var(--font-head); font-weight: 600; font-size: clamp(.85rem, .75rem + .5vw, 1rem) !important;
  line-height: 1.35; color: var(--tk-ink); margin: .6rem 0 .3rem; text-align: center;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.figure-num { font-variant-numeric: tabular-nums; }
.stat-row { display: flex; flex-wrap: wrap; gap: 1.6rem 2.6rem; margin: .4rem 0 1.4rem; }
.stat-row div { min-width: 9rem; }
.stat-row b { display: block; font-size: 1.9rem; font-weight: 700; line-height: 1.1; color: var(--tk-ink); font-variant-numeric: tabular-nums; }
.stat-row span { font-size: .88rem; color: var(--tk-soft); }
.note { border-left: 3px solid var(--tk-accent); padding: .3rem 0 .3rem .9rem; color: var(--tk-soft); max-width: 46rem; }
.swatches { display: flex; flex-wrap: wrap; gap: .35rem 1.1rem; align-items: center; justify-content: center; text-align: center;
  font-size: .86rem; color: var(--tk-soft); margin: .5rem 0 .3rem; }
.swatches b { font-weight: 600; margin-right: .3rem; }
.swatches span { display: inline-flex; align-items: center; gap: .4rem; }
.swatches i { width: 14px; height: 14px; border-radius: 3px; display: inline-block; box-shadow: inset 0 0 0 1px var(--tk-hairline); }
.swatches.center { justify-content: center; text-align: center; }
.swatches.center b { flex-basis: 100%; margin: 0; }
/* Legenda LISA (rata tengah) dibuat lebih kecil: teks, kotak warna, dan jarak. */
.swatches.center { font-size: .74rem; gap: .25rem .9rem; }
.swatches.center span { gap: .3rem; }
.swatches.center i { width: 11px; height: 11px; border-radius: 2px; }
.swatches em { font-style: normal; color: var(--tk-muted); flex-basis: 100%; margin-top: .1rem; }
.legend-dots { display: flex; flex-wrap: wrap; gap: .35rem 1.1rem; align-items: center; justify-content: center;
  font-size: .86rem; color: var(--tk-soft); margin: .5rem 0 .3rem; }
.legend-dots b { font-weight: 600; margin-right: .3rem; }
.legend-dots span { display: inline-flex; align-items: center; gap: .4rem; font-size: .86rem; color: var(--tk-soft); }
.legend-dots i { display: inline-block; border-radius: 50%; background: var(--tk-ink); opacity: .45; }
/* Kicker halaman Jelajah: gaya sama dengan kicker babak cerita, warnanya aksen halaman (--pg-accent
   dipasang di app.py menurut urutan babak). */
/* Dicampur 25% dengan warna tinta agar teks kecil ini >= 4,5:1 di kedua tema (aksen murni gagal
   di latar halaman Peta tema gelap). */
.pg-kicker { color: var(--pg-accent, var(--tk-accent));
  color: color-mix(in srgb, var(--pg-accent, var(--tk-accent)) 75%, var(--tk-ink)); text-transform: uppercase; letter-spacing: .3em;
  font-size: .72rem; font-weight: 600; margin: 0 0 -.6rem !important; }
/* Teks pilihan aktif pada segmented control/pills: warna aksen bawaan Streamlit hanya 4,0:1 (terang)
   dan 3,7:1 (gelap) di atas latar oranye pucatnya. accent_deep memberi 6,1:1 dan 6,2:1 (WCAG 1.4.3). */
button[data-selected="true"], button[data-selected="true"] * { color: var(--tk-accent-deep) !important; }
/* Penanda fokus keyboard yang tegas untuk tautan (navigasi atas, kartu Jelajah, sumber). Bawaan
   Streamlit hanya latar tipis yang mirip efek hover. Hanya untuk :focus-visible, tidak saat diklik. */
a:focus-visible, [data-testid="stTopNavLink"]:focus-visible, [data-testid="stPageLink-NavLink"]:focus-visible {
  outline: 2px solid var(--tk-accent-deep) !important; outline-offset: 2px; border-radius: .4rem; }
/* Grup tombol boleh turun baris bila kolomnya sempit, alih-alih memotong pilihan terakhir. */
[data-testid="stButtonGroup"] div:has(> button[data-selected]) { flex-wrap: wrap; }
/* Kolofon */
.site-foot { margin: 3.5rem auto 0; padding: 1.5rem 1rem .6rem; border-top: 1px solid var(--tk-hairline);
  text-align: center; color: var(--tk-muted); font-size: .82rem; line-height: 1.6; }
.site-foot p { margin: 0 0 .25rem; font-size: .82rem; }
.site-foot b { color: var(--tk-ink); font-family: var(--font-head); font-weight: 600; }
.site-foot a { color: var(--tk-muted); }
.site-foot span { white-space: nowrap; }
@media (max-width: 640px) { .site-foot { padding-bottom: 5rem; } }  /* ruang untuk tombol Aksesibilitas */
@media (max-width: 640px) {
  h1 { font-size: 1.75rem !important; }
  .lede { font-size: 1.06rem; }
  .stat-row b { font-size: 1.5rem; }
}
"""


FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


@lru_cache(maxsize=1)
def _font_css() -> str:
    """Poppins untuk judul dan angka besar, disematkan sebagai data URI.

    Dibundel lokal (bukan Google Fonts) agar tampilan tidak berubah saat tidak ada
    internet. Isi teks, kartu, dan label grafik tetap Source Sans 3: lebar hurufnya
    sudah menjadi dasar kalibrasi tata letak (kolom kartu, label sumbu SVG, navigasi).
    """
    faces = []
    for weight in (500, 600, 700):
        f = FONT_DIR / f"poppins-latin-{weight}.woff2"
        if f.exists():
            b64 = base64.b64encode(f.read_bytes()).decode("ascii")
            faces.append("@font-face{font-family:'Poppins';font-style:normal;font-weight:" + str(weight) +
                         ";font-display:swap;src:url(data:font/woff2;base64," + b64 + ") format('woff2');}")
    return "".join(faces) + ":root{--font-head:'Poppins','Source Sans 3','Source Sans Pro',system-ui,sans-serif;}"


# Ukuran teks (panel Aksesibilitas): mengubah font-size <html>, sehingga semua satuan rem ikut.
TEXT_SIZES = ["100%", "115%", "130%"]

# Tombol Aksesibilitas di tepi kiri. Labelnya tersembunyi secara visual tetapi tetap dibaca
# pembaca layar; ikonnya mask CSS (SVG ter-enkode URL agar lolos sanitizer st.html).
_A11Y_ICON = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E"
              "%3Cpath d='M20.5 6c-2.61.7-5.67 1-8.5 1s-5.89-.3-8.5-1L3 8c1.86.5 4 .83 6 1v13h2v-6h2v6h2V9"
              "c2-.17 4.14-.5 6-1l-.5-2zM12 6c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z'/%3E%3C/svg%3E\")")
A11Y_CSS = """
.st-key-a11y { position: fixed; left: .75rem; top: 50%; transform: translateY(-50%); z-index: 999990;
  width: auto !important; }
.st-key-a11y [data-testid="stPopoverButton"] { width: 3rem; height: 3rem; min-height: 0; padding: 0;
  border-radius: 50%; border: none; justify-content: center; background: var(--tk-accent);
  color: var(--tk-on-accent); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
.st-key-a11y [data-testid="stPopoverButton"] { position: relative; }
/* Ikon diposisikan absolut di tengah: elemen anak Streamlit (kosong) dan gap bawaan tombol
   menggeser ikon bila ikut tata letak flex. */
.st-key-a11y [data-testid="stPopoverButton"]::before { content: ""; position: absolute; inset: 0; margin: auto;
  width: 1.7rem; height: 1.7rem;
  background: currentColor; -webkit-mask: ICON center / contain no-repeat; mask: ICON center / contain no-repeat; }
.st-key-a11y [data-testid="stPopoverButton"]:hover { filter: brightness(1.08); }
.st-key-a11y [data-testid="stPopoverButton"]:focus-visible { outline: 3px solid var(--tk-ink); outline-offset: 3px; }
.st-key-a11y [data-testid="stPopoverButton"] [data-testid="stMarkdownContainer"] {
  position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.st-key-a11y [data-testid="stPopoverButton"] [aria-hidden="true"] { display: none; }
[data-testid="stPopoverBody"] { width: min(21rem, calc(100vw - 2rem)) !important; max-width: none; }
@media (max-width: 640px) { .st-key-a11y { top: auto; bottom: 1rem; transform: none; } }
""".replace("ICON", _A11Y_ICON)

# "Hentikan animasi": aturan yang sama dengan @media (prefers-reduced-motion) di story.css,
# tetapi berlaku atas pilihan pengguna, bukan hanya pengaturan sistem operasi.
STILL_CSS = """
*, *::before, *::after { transition: none !important; animation: none !important; scroll-behavior: auto !important; }
.ws-chart .ws-draw { stroke-dashoffset: 0 !important; }
.ws-chart .ws-bar rect { transform: none !important; }
.ws-chart .ws-bar text, .ws-chart .ws-row, .ws-chart .ws-mini { opacity: 1 !important; }
"""


def inject_css(text_size: str = TEXT_SIZES[0], still: bool = False):
    extra = A11Y_CSS
    if text_size in TEXT_SIZES and text_size != TEXT_SIZES[0]:
        # Teks diperbesar: judul grafik boleh turun baris agar tidak terpotong (WCAG 1.4.4).
        extra += (f"html {{ font-size: {text_size} !important; }}"
                  ".chart-t, .ws .ws-chart-t { white-space: normal !important; }")
    if still:
        extra += STILL_CSS
    st.html(f"<style>{_font_css()}{theme.css_vars()}{CSS}{extra}</style>")


def lede(text: str):
    st.html(f'<p class="lede">{text}</p>')


# Kata tugas yang tetap huruf kecil dalam judul (kecuali di awal judul).
_SMALL_WORDS = {"dan", "atau", "di", "ke", "dari", "pada", "per", "untuk", "dengan", "terhadap",
                "yang", "vs", "oleh", "dalam", "sebagai", "&"}


def title_case(text: str) -> str:
    """Huruf kapital di awal setiap kata (juga tiap unsur kata ulang dan kata bergaris miring),
    kecuali kata tugas. Singkatan (PCA, LQ, TW II) dan notasi seperti z-score dibiarkan."""
    def cap(word):
        if not word or not word[0].islower() or word.startswith("z-"):
            return word
        return word[0].upper() + word[1:]

    out = []
    for i, w in enumerate(text.split(" ")):
        if i and w.lower() in _SMALL_WORDS:
            out.append(w.lower())
        else:
            out.append("/".join("-".join(cap(x) for x in part.split("-")) if not part.startswith("z-") else part
                                for part in w.split("/")))
    return " ".join(out)


def chart_title(text: str):
    """Judul yang menyebut isi grafik (apa, satuan, cakupan), di atas figur, dalam huruf judul."""
    text = title_case(text)
    st.html(f'<p class="chart-t" title="{escape(text)}">{text}</p>')


def page_kicker(text: str):
    """Label kecil berspasi di atas judul halaman Jelajah, sama gayanya dengan kicker babak cerita."""
    st.html(f'<p class="pg-kicker">{escape(text)}</p>')


def footer():
    """Kolofon di akhir setiap halaman: judul, pembuat, dan mata kuliah. Sumber data tidak diulang
    di sini; sudah ada di bawah setiap grafik dan di halaman Data & metode."""
    def line(*parts):
        # Tiap bagian dibungkus span agar baris hanya patah di antara bagian, bukan di tengahnya.
        return " · ".join(f"<span>{x}</span>" for x in parts if x)

    mail = f'<a href="mailto:{escape(AUTHOR_EMAIL)}">{escape(AUTHOR_EMAIL)}</a>' if AUTHOR_EMAIL else ""
    who = line(f"<b>{escape(APP_TITLE)}</b>", escape(AUTHOR), AUTHOR_ID and f"NIM {escape(AUTHOR_ID)}",
               AUTHOR_CLASS and f"Kelas {escape(AUTHOR_CLASS)}", mail)
    made = line(escape(COURSE), escape(INSTITUTION), escape(MADE_DATE))
    st.html(
        f'<footer class="site-foot" role="contentinfo"><p>{who}</p><p>{made}</p></footer>'
    )


def source(extra: str = ""):
    """Baris sumber di bawah setiap visualisasi (wajib menurut ketentuan ujian).
    Diawali "Sumber: BPS" persis seperti bunyi ketentuan, lalu rincian tabelnya."""
    tail = f" {extra[:1].upper()}{extra[1:]}." if extra else ""
    st.html(f'<p class="src">Sumber: BPS (<a href="{BPS_SOURCE_URL}" target="_blank">{SOURCE_CITE}</a>), '
            f'diolah {ACCESS_DATE}.{tail}</p>')


def stats(items):
    """items: [(angka, keterangan), ...]"""
    cells = "".join(f"<div><b>{v}</b><span>{k}</span></div>" for v, k in items)
    st.html(f'<div class="stat-row">{cells}</div>')


def note(text: str):
    st.html(f'<div class="note">{text}</div>')


def swatches(title: str, labels, colors, note_text: str = "", center: bool = False):
    """Legenda kelas peta sebagai HTML: membungkus rapi di layar sempit,
    dan teksnya tetap berwarna tinta (bukan warna kelas)."""
    items = "".join(
        f'<span><i style="background:{c}"></i>{lab}</span>' for lab, c in zip(labels, colors)
    )
    tail = f'<em>{note_text}</em>' if note_text else ""
    cls = "swatches center" if center else "swatches"
    st.html(f'<div class="{cls}"><b>{title}</b>{items}{tail}</div>')
