"""Jelajah 1: data berdimensi tinggi (17 pangsa sektor x 514 kab/kota)."""

import numpy as np
import pandas as pd
import streamlit as st

import charts as ch
import data
from charts import idn
from config import PERIODS, SECTOR_CODES, SECTOR_SHORT
import theme
from ui import chart_title, page_kicker, source, swatches

reg = data.regions()
names = reg["kabkota"]

page_kicker("Jelajah · Pola ekonomi")
st.title("Siapa mirip siapa")
# Paragraf halaman ini rata kiri-kanan; kata tidak dipenggal (tanpa tanda hubung) supaya tidak terpotong.
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
    '<p class="lede" style="margin-bottom:.7rem">Setiap titik mewakili satu kabupaten/kota dan posisinya '
    'ditentukan oleh komposisi 17 lapangan usaha. Daerah dengan struktur ekonomi yang mirip akan berada '
    'lebih berdekatan.</p>'
    '<p class="lede" style="font-size:.95rem;font-style:italic">Gunakan Lasso atau Box Select untuk memilih beberapa daerah. Informasi lain di halaman '
    'akan menyesuaikan dengan pilihan tersebut. Untuk menghapus pilihan, klik dua kali pada area kosong di '
    'grafik.</p>'
)

# --- kontrol ----------------------------------------------------------------
c1, c2, c3, c4 = st.columns([1.1, 1, 2, 1])
period = c1.segmented_control("Triwulan", PERIODS, default="Triwulan II", key="mv_period") or "Triwulan II"
tw = period.replace("Triwulan", "TW")  # bentuk pendek untuk judul grafik satu baris
k = c2.segmented_control("Jumlah klaster", [4, 5, 6], default=6, key="mv_k") or 6
mv = data.multivariate(period, k)
colors = data.cluster_colors(mv)
prov = reg.loc[mv.shares.index, "provinsi"]

focus_opts = ["Tidak ada"] + [f"Klaster · {c}" for c in colors] + \
             [f"Provinsi · {p}" for p in sorted(prov.unique())]
focus = c3.selectbox("Sorot Klaster/Provinsi", focus_opts, key="mv_focus",
                     help="Cara lain memilih daerah, lebih mudah di ponsel daripada laso.")
arrows = c4.toggle("Panah loading", value=True, help="Arah dan kekuatan setiap sektor pada PC1–PC2")

focus_set = set()
if focus.startswith("Klaster · "):
    focus_set = set(mv.cluster.index[mv.cluster == focus.split(" · ", 1)[1]])
elif focus.startswith("Provinsi · "):
    focus_set = set(prov.index[prov == focus.split(" · ", 1)[1]])

# --- biplot (dengan seleksi) -----------------------------------------------
mobile = "Mobi" in st.context.headers.get("User-Agent", "")  # ponsel: tata letak grafik ringkas
fig, trace_index = ch.pca_biplot(
    mv.scores, mv.explained, mv.loadings, mv.cluster, colors, names, prov,
    highlight=focus_set, outliers=mv.mahalanobis.where(mv.outlier).dropna(), show_arrows=arrows,
    compact=mobile,
)
# Biplot selebar kontainer (skala sumbu setara); teks sumbu dan scree berdampingan di bawahnya.
left = st.container()
with left:
    chart_title(f"Biplot PCA pangsa sektor, {tw} 2026")
    event = st.plotly_chart(fig, key=f"pca_{period}_{k}", on_select="rerun",
                            selection_mode=("box", "lasso"), config=ch.SELECT_CONFIG)
    source(f"PCA pada z-score pangsa 17 sektor, {period} 2026; warna dan bentuk = klaster Ward")

brushed = set()
for p in (event.selection.points if event and event.selection else []):
    curve, idx = p.get("curve_number"), p.get("point_index")
    if curve is not None and curve < len(trace_index) and idx is not None:
        brushed.add(trace_index[curve][idx])

# Plotly menghapus seleksi laso saat figur berubah (mis. ganti tema/palet); simpan seleksi
# dan pulihkan untuk tampilan yang tertaut.
look = (theme.mode(), theme.variant())
look_changed = st.session_state.get("_brush_look", look) != look
st.session_state["_brush_look"] = look
store = st.session_state.setdefault("_brush", {})
skey = f"{period}_{k}"
restored = False
if brushed:
    store[skey] = {"codes": sorted(brushed), "restored": False}
elif skey in store and (store[skey]["restored"] or look_changed):
    brushed, restored = set(store[skey]["codes"]), True
    store[skey]["restored"] = True
else:
    store.pop(skey, None)
if restored:
    with left:
        c_info, c_btn = st.columns([3, 1], vertical_alignment="center")
        c_info.caption(f"Seleksi {len(brushed)} daerah dipulihkan setelah tampilan berganti. "
                       "Tarik laso baru untuk menggantinya.")
        if c_btn.button("Hapus seleksi", key=f"clear_{skey}"):
            store.pop(skey, None)
            st.rerun()

selected = brushed or focus_set
sel_label = ("Hasil seleksi" if brushed else (focus.split(" · ", 1)[1] if focus_set else ""))

txt, scr = st.columns([1.15, 1], gap="large")
with txt:
    pc1 = mv.loadings["PC1"].sort_values()
    pc2 = mv.loadings["PC2"].sort_values()
    cum2 = mv.explained[:2].sum() * 100
    st.markdown("**Cara membaca sumbu**")

    def nm(code):  # nama sektor untuk kalimat: huruf kecil, "&" ditulis "dan"
        return SECTOR_SHORT[code].lower().replace(" & ", " dan ")

    st.markdown(
        f"Ke **kanan (PC1)** menunjukkan porsi {nm(pc1.index[-1])}, {nm(pc1.index[-2])}, serta "
        f"{nm(pc1.index[-3])} yang lebih besar, yang cenderung mencerminkan karakter ekonomi perkotaan. "
        f"Ke **kiri**, daerah lebih bertumpu pada {nm(pc1.index[0])} dan {nm(pc1.index[1])}.\n\n"
        f"Ke **atas (PC2)** menunjukkan porsi {nm(pc2.index[-1])} serta {nm(pc2.index[-2])} yang lebih besar. "
        f"Ke **bawah**, porsi {nm(pc2.index[0])} dan {nm(pc2.index[1])} lebih menonjol.\n\n"
        f"Kedua sumbu ini hanya menjelaskan **{idn(cum2, 0)}% variasi** dalam data. Sisanya tersebar pada "
        f"komponen lain, sehingga jarak antardaerah pada bidang ini sebaiknya dibaca sebagai gambaran "
        f"pendekatan, bukan ukuran kemiripan secara keseluruhan."
    )
with scr:
    chart_title("Varians tiap komponen utama (%)")
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
        chart_title("Median pangsa: terpilih vs semua (%)")
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
        "Setiap baris menunjukkan **profil rata-rata satu klaster**. Nilai z-score menunjukkan posisi tiap "
        "sektor dibandingkan rata-rata seluruh daerah: **jingga** berarti porsi sektor tersebut lebih tinggi "
        "dari rata-rata, sedangkan **biru** berarti lebih rendah. Nama klaster ditentukan berdasarkan sektor "
        "yang paling menonjol dalam profilnya."
    )
    chart_title("Profil klaster: rata-rata z-score pangsa")
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
st.markdown(
    "Setiap garis mewakili satu kabupaten/kota. Seret pada salah satu sumbu untuk memilih rentang nilai dan "
    "menyaring daerah yang sesuai. Sumbu yang dipilih dapat digunakan secara bersamaan untuk melihat daerah "
    "dengan kombinasi karakteristik tertentu. "
    + ("Garis jingga tua adalah daerah terpilih." if selected else "Warna garis menunjukkan klaster.")
)
# Brushing Plotly hidup di sisi klien; cara paling andal mengosongkannya adalah memasang ulang grafik
# dengan key baru. Tombol ini hanya menaikkan penghitung key.
hint, reset = st.columns([5, 1], vertical_alignment="center")
hint.caption("*Seret pada sumbu untuk memilih rentang. Garis yang tidak memenuhi pilihan akan tersaring dari "
             "tampilan.*")
reset.button("Reset pilihan", key="pc_reset_btn",
             on_click=lambda: st.session_state.update(pc_reset=st.session_state.get("pc_reset", 0) + 1))
if len(dims) >= 2:
    chart_title(f"Pangsa sektor tiap daerah (%), {tw} 2026")
    st.plotly_chart(ch.parallel_coords(mv.shares, mv.cluster, colors, dims, selected, compact=mobile), config={**ch.PLOT_CONFIG, "plotGlPixelRatio": 1},
                    key=f"pc_chart_{st.session_state.get('pc_reset', 0)}")
    # Parallel coordinates Plotly tidak punya legenda bawaan; tanpa ini warna
    # klaster tidak bisa dibaca sama sekali.
    if selected:
        tk = theme.tokens()
        swatches("Garis", ["Daerah terpilih", "Lainnya"], [tk.accent_deep, tk.rule])
    else:
        swatches("Klaster", list(colors), list(colors.values()))
    source("pangsa sektor (%) terhadap PDRB daerah; nilai di atas persentil 99,5 diletakkan di puncak sumbu (≥)")
else:
    st.info("Pilih minimal dua sektor.")

# --- heatmap terklaster -----------------------------------------------------
st.header("Heatmap terklaster")
st.markdown(
    "Baris diurutkan menurut dendrogram Ward dan kolom menurut kemiripan pola antarsektor, sehingga "
    "blok warna yang searah menandai kelompok. "
    + ("Hanya daerah terpilih yang ditampilkan." if selected else "Pilih daerah untuk memperbesar.")
)
chart_title("Heatmap terklaster z-score pangsa sektor")
st.plotly_chart(
    ch.clustered_heatmap(mv.z, mv.row_order, mv.col_order, mv.cluster, colors, names, selected or None),
    config=ch.PLOT_CONFIG,
)
swatches("Klaster", list(colors), list(colors.values()))
source("z-score pangsa sektor dipotong pada ±3")

# --- pencilan ---------------------------------------------------------------
st.header("Yang tidak masuk pola mana pun")
out = mv.mahalanobis[mv.outlier].sort_values(ascending=False)
st.markdown(
    f"**{len(out)} daerah** memiliki susunan sektor yang sangat berbeda dari sebagian besar daerah lainnya, "
    f"sehingga terdeteksi sebagai pencilan. Jaraknya diukur dengan Mahalanobis menggunakan "
    f"{mv.n_pc_outlier} komponen utama pertama yang sudah menjelaskan setidaknya 80% variasi data, dengan "
    f"ambang 99% distribusi chi-square. Biasanya, perbedaannya muncul karena satu sektor jauh lebih "
    f"dominan dibanding sektor lain, misalnya kilang, pembangkit listrik, pariwisata, atau kantor pusat "
    f"korporasi."
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
