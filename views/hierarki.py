"""Jelajah 3: data berhierarki - treemap dan icicle dengan breadcrumb."""

import numpy as np
import streamlit as st

import charts as ch
import data
from charts import idn, signed
from config import PERIODS
from ui import lede, source

st.title("Dari pulau sampai sektor")
lede(
    "Luas setiap kotak menunjukkan <b>besarnya PDRB</b>, sedangkan warnanya menunjukkan "
    "<b>laju perubahan TW II terhadap TW I</b>. Jadi satu tampilan memuat dua variabel yang "
    "berbeda. Klik sebuah kotak untuk masuk satu tingkat; jalur di atas grafik (breadcrumb) "
    "menunjukkan posisi Anda dan bisa diklik untuk kembali."
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
    st.markdown(
        f"Di dalam **{node['label']}** (Rp{idn(node['nilai'] / 1000, 1)} triliun, "
        f"{signed(node['tumbuh'])}% q-to-q), bagian terbesar adalah **{big['label']}** "
        f"({idn(big['pangsa_induk'], 1)}%). Laju tercepat ada di **{fast['label']}** "
        f"({signed(fast['tumbuh'])}%), paling lambat di **{slow['label']}** ({signed(slow['tumbuh'])}%)."
    )

st.header("Tampilan kedua: icicle")
st.markdown(
    "Datanya sama, tetapi disusun berlapis dari atas ke bawah. Treemap memudahkan membandingkan "
    "luas. Icicle memudahkan melihat struktur, yaitu tingkat mana yang memuat apa, dan tetap "
    "terbaca di layar sempit."
)
st.plotly_chart(ch.icicle(h, lim, root), config=ch.PLOT_CONFIG, key=f"ic_{order}_{period}_{root}")
source("ukuran dan warna sama dengan treemap di atas")

with st.expander("Mengapa warna simpul induk tidak sama dengan rata-rata anaknya?"):
    st.markdown(
        "Pertumbuhan setiap simpul dihitung ulang dari **jumlah** nilai TW I dan TW II seluruh "
        "isinya, (ΣTW II / ΣTW I − 1) × 100. Plotly secara bawaan merata-ratakan warna anak, dan "
        "itu keliru untuk laju pertumbuhan karena daerah kecil yang tumbuh 20% akan tampak sama "
        "penting dengan kota besar yang tumbuh 2%."
    )
