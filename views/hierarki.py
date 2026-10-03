"""Jelajah 3: data berhierarki - treemap dan icicle dengan breadcrumb."""

import numpy as np
import streamlit as st

import charts as ch
import data
from charts import idn, signed
from config import PERIODS
from ui import chart_title, page_kicker, source

page_kicker("Jelajah · Wilayah & sektor")
st.title("Dari pulau sampai sektor")
# Paragraf halaman ini rata kiri-kanan, selebar halaman, tanpa pemenggalan kata (sama dengan "Pola ekonomi").
st.html(
    "<style>"
    '[data-testid="stMain"] [data-testid="stMarkdownContainer"] p, [data-testid="stMain"] p.lede '
    "{ text-align: justify; text-justify: inter-word; hyphens: none; word-break: normal; "
    "overflow-wrap: normal; }"
    '[data-testid="stMain"] [data-testid="stWidgetLabel"] p, [data-testid="stMain"] [data-testid="stButtonGroup"] p '
    "{ text-align: left; }"
    '[data-testid="stMain"] p.lede { max-width: none; }'
    "</style>"
)
st.html(
    '<p class="lede" style="margin-bottom:.7rem">Ukuran kotak menunjukkan besarnya PDRB, sedangkan warna '
    'menunjukkan perubahan PDRB dari Triwulan I ke Triwulan II. Jadi, satu tampilan memperlihatkan besaran '
    'ekonomi dan pertumbuhannya sekaligus. Setiap kotak juga menuliskan porsinya terhadap tingkat di '
    'atasnya dan angka pertumbuhannya, sehingga tidak perlu menebak dari warna.</p>'
    '<p class="lede" style="font-size:.95rem;font-style:italic">Klik kotak untuk melihat tingkat yang lebih '
    'rinci, dari pulau hingga sektor. Jalur di atas grafik menunjukkan posisi saat ini dan bisa diklik '
    'untuk kembali ke tingkat sebelumnya.</p>'
)

c1, c2, c3 = st.columns([1.3, 1, 1.6])
order_label = c1.segmented_control("Susunan", ["Wilayah → sektor", "Sektor → wilayah"],
                                   default="Wilayah → sektor", key="h_order") or "Wilayah → sektor"
order = "wilayah" if order_label.startswith("Wilayah") else "sektor"
period = c2.segmented_control("Ukuran kotak", PERIODS, default="Triwulan II", key="h_period") or "Triwulan II"

h = data.hierarchy(period, order)
jump_levels = ["Pulau", "Provinsi"] if order == "wilayah" else ["Kelompok", "Sektor"]
jump_nodes = h[h["tingkat"].isin(jump_levels)].sort_values(["tingkat", "label"])
jump_map = {"Indonesia": "Indonesia"}
for _, r in jump_nodes.iterrows():
    jump_map[f"{r['tingkat']} · {r['label']}"] = r["id"]
start = c3.selectbox("Langsung ke", list(jump_map), key=f"h_jump_{order}",
                     help="Pintasan untuk ponsel; sama dengan mengklik kotaknya.")
root = jump_map[start]

leaf = h[~h["id"].isin(h["parent"])]
lim = float(np.clip(np.nanpercentile(leaf["tumbuh"].abs(), 90), 3, 15))

st.header("Tampilan pertama: treemap")
hier_title = f"PDRB & pertumbuhan, {period.replace('Triwulan', 'TW')} 2026"  # satu baris; rinciannya di sumber
chart_title(f"Treemap {hier_title}")
st.plotly_chart(ch.treemap(h, lim, root), config=ch.PLOT_CONFIG, key=f"tm_{order}_{period}_{root}")
source(f"ukuran: PDRB ADHK {period} 2026 (miliar Rp); warna: pertumbuhan q-to-q, "
       f"dipotong pada ±{idn(lim, 0)}%")

# --- ringkasan simpul yang sedang dibuka -----------------------------------
node = h[h["id"] == root].iloc[0]
kids = h[h["parent"] == root]
if len(kids):
    big = kids.nlargest(1, "nilai").iloc[0]
    fast = kids.nlargest(1, "tumbuh").iloc[0]
    slow = kids.nsmallest(1, "tumbuh").iloc[0]
    def nama(r, awal=False):
        """Kelompok sektor ditulis 'sektor Primer' di kalimat; selain itu memakai label apa adanya."""
        t = f"sektor {r['label']}" if r["tingkat"] == "Kelompok" else r["label"]
        return t[:1].upper() + t[1:] if awal else t

    lead = f"Di tingkat <b>{node['label']}</b>" if node["tingkat"] == "Nasional" else         f"Di {node['tingkat'].lower()} <b>{node['label']}</b>"
    if fast["id"] == big["id"]:
        fastest = f"{nama(fast, awal=True)} juga mencatat pertumbuhan tercepat ({signed(fast['tumbuh'])}%)"
    else:
        fastest = f"Namun, pertumbuhan tercepat justru datang dari {nama(fast)} ({signed(fast['tumbuh'])}%)"
    st.markdown(
        f"{lead}, total PDRB mencapai Rp{idn(node['nilai'] / 1000, 1)} triliun dan tumbuh "
        f"{idn(node['tumbuh'], 1)}% dari Triwulan I ke Triwulan II. {nama(big, awal=True)} menyumbang bagian "
        f"terbesar, yaitu {idn(big['pangsa_induk'], 1)}% dari total PDRB. {fastest}, sedangkan {slow['label']} "
        f"tumbuh paling lambat ({signed(slow['tumbuh'])}%).",
        unsafe_allow_html=True,
    )

st.header("Tampilan kedua: icicle")
st.markdown(
    "Datanya sama, tetapi disusun berlapis dari atas ke bawah. Treemap memudahkan membandingkan "
    "luas. Icicle memudahkan melihat struktur, yaitu tingkat mana yang memuat apa, dan tetap "
    "terbaca di layar sempit."
)
chart_title(f"Icicle {hier_title}")
st.plotly_chart(ch.icicle(h, lim, root), config=ch.PLOT_CONFIG, key=f"ic_{order}_{period}_{root}")
source("ukuran dan warna sama dengan treemap di atas")

with st.expander("Mengapa warna simpul induk tidak sama dengan rata-rata wilayah di bawahnya?"):
    st.markdown(
        "Pertumbuhan setiap tingkat dihitung dari total nilai Triwulan I dan Triwulan II seluruh wilayah "
        "di dalamnya, dengan rumus:"
    )
    st.latex(r"\footnotesize \text{Pertumbuhan} = \left( \frac{\sum \text{TW II}}{\sum \text{TW I}} - 1 \right) \times 100\%")
    st.markdown(
        "Dengan cara ini, pertumbuhan mencerminkan perubahan total pada tingkat tersebut."
    )
    st.markdown(
        "Cara ini juga menghindari rata-rata sederhana antarwilayah. Daerah kecil yang tumbuh 20% tidak "
        "diperlakukan sama dengan kota besar yang tumbuh 2%, karena kontribusi masing-masing mengikuti "
        "besarnya nilai PDRB."
    )
