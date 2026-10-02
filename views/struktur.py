"""Jelajah 1: data berdimensi tinggi (17 pangsa sektor x 514 kab/kota)."""

import numpy as np
import pandas as pd
import streamlit as st

import charts as ch
import data
from charts import idn
from config import PERIODS, SECTOR_CODES, SECTOR_SHORT
from ui import lede, source

reg = data.regions()
names = reg["kabkota"]

st.title("Siapa mirip siapa")
lede(
    "Setiap titik adalah satu kabupaten/kota yang diposisikan menurut <b>porsi</b> 17 lapangan "
    "usahanya. Daerah yang struktur ekonominya mirip akan berdekatan. Tarik laso atau kotak pada "
    "grafik untuk memilih sekelompok daerah; tampilan lain di halaman ini akan ikut menyesuaikan."
)

# --- kontrol ----------------------------------------------------------------
c1, c2, c3, c4 = st.columns([1.1, 1, 2, 1])
period = c1.segmented_control("Triwulan", PERIODS, default="Triwulan II", key="mv_period") or "Triwulan II"
k = c2.segmented_control("Jumlah klaster", [4, 5, 6], default=6, key="mv_k") or 6
mv = data.multivariate(period, k)
colors = data.cluster_colors(mv)
prov = reg.loc[mv.shares.index, "provinsi"]

focus_opts = ["Tidak ada"] + [f"Klaster · {c}" for c in colors] + \
             [f"Provinsi · {p}" for p in sorted(prov.unique())]
focus = c3.selectbox("Sorot", focus_opts, key="mv_focus",
                     help="Cara lain memilih daerah, lebih mudah di ponsel daripada laso.")
arrows = c4.toggle("Panah loading", value=True, help="Arah dan kekuatan setiap sektor pada PC1–PC2")

focus_set = set()
if focus.startswith("Klaster · "):
    focus_set = set(mv.cluster.index[mv.cluster == focus.split(" · ", 1)[1]])
elif focus.startswith("Provinsi · "):
    focus_set = set(prov.index[prov == focus.split(" · ", 1)[1]])

# --- biplot (dengan seleksi) -----------------------------------------------
fig, trace_index = ch.pca_biplot(
    mv.scores, mv.explained, mv.loadings, mv.cluster, colors, names, prov,
    highlight=focus_set, outliers=mv.mahalanobis.where(mv.outlier).dropna(), show_arrows=arrows,
)
left, right = st.columns([1.75, 1], gap="large")
with left:
    event = st.plotly_chart(fig, key=f"pca_{period}_{k}", on_select="rerun",
                            selection_mode=("box", "lasso"), config=ch.SELECT_CONFIG)
    source(f"PCA pada z-score pangsa 17 sektor, {period} 2026; warna dan bentuk = klaster Ward")

brushed = set()
for p in (event.selection.points if event and event.selection else []):
    curve, idx = p.get("curve_number"), p.get("point_index")
    if curve is not None and curve < len(trace_index) and idx is not None:
        brushed.add(trace_index[curve][idx])

selected = brushed or focus_set
sel_label = ("Hasil seleksi" if brushed else (focus.split(" · ", 1)[1] if focus_set else ""))

with right:
    pc1 = mv.loadings["PC1"].sort_values()
    pc2 = mv.loadings["PC2"].sort_values()
    cum2 = mv.explained[:2].sum() * 100
    st.markdown("**Cara membaca sumbu**")
    st.markdown(
        f"Ke **kanan** (PC1) berarti porsi {SECTOR_SHORT[pc1.index[-1]].lower()}, "
        f"{SECTOR_SHORT[pc1.index[-2]].lower()}, dan {SECTOR_SHORT[pc1.index[-3]].lower()} lebih besar, "
        f"ciri ekonomi kota. Ke kiri berarti lebih bertumpu pada "
        f"{SECTOR_SHORT[pc1.index[0]].lower()} dan {SECTOR_SHORT[pc1.index[1]].lower()}.\n\n"
        f"Ke **atas** (PC2) berarti lebih industri ({SECTOR_SHORT[pc2.index[-1]].lower()}, "
        f"{SECTOR_SHORT[pc2.index[-2]].lower()}). Ke bawah berarti lebih bergantung pada "
        f"{SECTOR_SHORT[pc2.index[0]].lower()} dan {SECTOR_SHORT[pc2.index[1]].lower()}.\n\n"
        f"Dua sumbu ini baru menangkap **{idn(cum2, 0)}%** variasi. Sisanya tersebar di banyak "
        f"komponen kecil, sehingga jarak di bidang ini hanya pendekatan."
    )
    st.plotly_chart(ch.scree(mv.explained, mv.n_pc_outlier), config=ch.PLOT_CONFIG)
    source("proporsi varians per komponen")

# --- profil seleksi ---------------------------------------------------------
st.header("Profil daerah terpilih" if selected else "Profil per klaster")
if selected:
    sel = sorted(selected)
    sel_med = mv.shares.loc[sel].median()
    all_med = mv.shares.median()
    diff = (sel_med - all_med).sort_values()
    st.markdown(
        f"**{sel_label}** ({len(sel)} daerah). Dibanding median nasional, porsi "
        f"**{SECTOR_SHORT[diff.index[-1]].lower()}** paling menonjol "
        f"({idn(sel_med[diff.index[-1]], 1)}% vs {idn(all_med[diff.index[-1]], 1)}%), sedangkan "
        f"**{SECTOR_SHORT[diff.index[0]].lower()}** paling tertinggal "
        f"({idn(sel_med[diff.index[0]], 1)}% vs {idn(all_med[diff.index[0]], 1)}%)."
    )
    a, b = st.columns([1.2, 1], gap="large")
    with a:
        st.plotly_chart(ch.profile_dumbbell(sel_med, all_med, "Median terpilih"), config=ch.PLOT_CONFIG)
        source("median pangsa sektor")
    with b:
        tbl = pd.DataFrame({
            "Kab/Kota": names.loc[sel], "Provinsi": prov.loc[sel], "Klaster": mv.cluster.loc[sel],
            "Sektor terbesar": mv.shares.loc[sel].idxmax(axis=1).map(SECTOR_SHORT),
            "Porsinya (%)": mv.shares.loc[sel].max(axis=1).round(1),
        }).sort_values("Porsinya (%)", ascending=False)
        st.dataframe(tbl, hide_index=True, height=440)
else:
    counts = mv.cluster.value_counts().to_dict()
    st.markdown(
        "Setiap baris adalah rata-rata z-score satu klaster. Jingga berarti porsi sektor itu di atas "
        "rata-rata semua daerah, biru berarti di bawahnya. Nama klaster diberikan dari sektor yang "
        "paling menonjol."
    )
    st.plotly_chart(ch.cluster_profile_heatmap(mv.cluster_profile, mv.col_order, counts),
                    config=ch.PLOT_CONFIG)
    source("rata-rata z-score pangsa sektor per klaster Ward")

# --- parallel coordinates ---------------------------------------------------
st.header("Garis-garis yang searah")
mag = np.hypot(mv.loadings["PC1"], mv.loadings["PC2"]).sort_values(ascending=False)
default_dims = [c for c in SECTOR_CODES if c in set(mag.index[:8])]
dims = st.multiselect(
    "Sumbu yang ditampilkan", SECTOR_CODES, default=default_dims, format_func=SECTOR_SHORT.get,
    key="pc_dims", help="Bawaan: 8 sektor dengan loading terbesar pada PC1–PC2",
)
st.caption(
    "Setiap garis satu daerah. Seret di sepanjang sumbu untuk menyaring rentang nilai (brushing). "
    + ("Garis jingga tua adalah daerah terpilih." if selected else "Warna mengikuti klaster.")
)
if len(dims) >= 2:
    st.plotly_chart(ch.parallel_coords(mv.shares, mv.cluster, colors, dims, selected), config=ch.PLOT_CONFIG)
    source("pangsa sektor (%) terhadap PDRB daerah; sumbu dipotong pada persentil 99,5")
else:
    st.info("Pilih minimal dua sektor.")

# --- heatmap terklaster -----------------------------------------------------
st.header("Heatmap terklaster")
st.markdown(
    "Baris diurutkan menurut dendrogram Ward dan kolom menurut kemiripan pola antarsektor, sehingga "
    "blok warna yang searah menandai kelompok. "
    + ("Hanya daerah terpilih yang ditampilkan." if selected else "Pilih daerah untuk memperbesar.")
)
st.plotly_chart(
    ch.clustered_heatmap(mv.z, mv.row_order, mv.col_order, mv.cluster, colors, names, selected or None),
    config=ch.PLOT_CONFIG,
)
source("z-score pangsa sektor dipotong pada ±3")

# --- pencilan ---------------------------------------------------------------
st.header("Yang tidak masuk pola mana pun")
out = mv.mahalanobis[mv.outlier].sort_values(ascending=False)
st.markdown(
    f"**{len(out)} daerah** jaraknya terlalu jauh dari pusat data untuk dianggap kebetulan. Jaraknya "
    f"diukur dengan Mahalanobis pada {mv.n_pc_outlier} komponen pertama (≥ 80% varians), dengan ambang "
    f"χ² 99%. Biasanya penyebabnya satu sektor yang sangat dominan, misalnya kilang, pembangkit listrik, "
    f"pariwisata, atau kantor pusat korporasi."
)
dom = mv.z.loc[out.index].idxmax(axis=1)
otbl = pd.DataFrame({
    "Kab/Kota": names.loc[out.index], "Provinsi": prov.loc[out.index],
    "Jarak²": out.round(1), "Paling menonjol": dom.map(SECTOR_SHORT),
    "Porsinya (%)": [round(mv.shares.loc[i, d], 1) for i, d in dom.items()],
    "Klaster": mv.cluster.loc[out.index],
})
st.dataframe(otbl, hide_index=True, height=360)
source("jarak Mahalanobis kuadrat")
