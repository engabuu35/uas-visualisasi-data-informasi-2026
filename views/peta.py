"""Jelajah 2: geospasial - choropleth rasio, simbol proporsional, LISA."""

import numpy as np
import pandas as pd
import streamlit as st

import analysis as an
import charts as ch
import data
from charts import idn
import theme
from config import GEO_SOURCE, PERIODS, SECTOR_CODES, SECTOR_SHORT
from ui import chart_title, lede, page_kicker, source, swatches

reg = data.regions()
TK = theme.tokens()
geo = data.geojson()

page_kicker("Jelajah · Peta")
st.title("Peta spesialisasi daerah")
st.html(
    '<style>[data-testid="stMain"] p.lede { max-width: none; text-align: justify; text-justify: inter-word; '
    "hyphens: none; word-break: normal; overflow-wrap: normal; }</style>"
)
lede(
    "Warna pada peta menunjukkan <b>rasio</b>, seperti porsi sektor, location quotient (LQ), atau laju "
    "pertumbuhan, bukan nilai rupiah. Dengan begitu, perbandingan antarwilayah tidak didominasi oleh "
    "daerah yang memang memiliki nilai PDRB lebih besar. Nilai rupiah ditampilkan terpisah sebagai "
    "lingkaran dan dapat disembunyikan untuk melihat pola spesialisasi dengan lebih jelas."
)

# --- kontrol ----------------------------------------------------------------
r1 = st.columns([2.1, 1.3, 1])
indicator = r1[0].segmented_control("Indikator", list(data.INDICATORS), default="Location quotient",
                                    key="map_ind") or "Location quotient"
sector_opts = SECTOR_CODES + (["TOTAL"] if indicator == "Pertumbuhan q-to-q" else [])
sector = r1[1].selectbox("Lapangan usaha", sector_opts, index=1,
                         format_func=lambda c: "Semua sektor (PDRB)" if c == "TOTAL" else SECTOR_SHORT[c],
                         key=f"map_sector_{indicator == 'Pertumbuhan q-to-q'}")
if indicator == "Pertumbuhan q-to-q":
    period = "Triwulan II"
    r1[2].markdown("<div style='padding-top:2rem;color:var(--tk-soft)'>TW II vs TW I</div>", unsafe_allow_html=True)
else:
    period = r1[2].segmented_control("Triwulan", PERIODS, default="Triwulan II", key="map_period") \
        or "Triwulan II"

method_opts = {
    "Pangsa sektor": ["Natural breaks (Jenks)", "Kuantil"],
    "Location quotient": ["Ambang bermakna", "Natural breaks (Jenks)", "Kuantil"],
    "Pertumbuhan q-to-q": ["Ambang bermakna", "Kuantil"],
}[indicator]
r2 = st.columns([2.1, 1.3, 1])
method = r2[0].segmented_control("Klasifikasi", method_opts, default=method_opts[0],
                                 key=f"map_method_{indicator}") or method_opts[0]
province = r2[1].selectbox("Perbesar ke provinsi", ["Seluruh Indonesia"] + sorted(reg["provinsi"].unique()),
                           key="map_prov")
layers = r2[2].pills("Lapisan", ["Choropleth", "Lingkaran PDRB"], default=["Choropleth", "Lingkaran PDRB"],
                     selection_mode="multi", key="map_layers")

# --- nilai dan kelas ----------------------------------------------------------
vals = data.indicator_values(indicator, sector, period)
df = reg.loc[vals.index, ["kabkota", "provinsi", "lat", "lon"]].copy()
df["kode"] = df.index
df["nilai"] = vals.values
df["pdrb"] = data.sector_values(sector, period).reindex(df.index).values

K = 5
if method == "Ambang bermakna" and indicator == "Location quotient":
    breaks = [0, 0.5, 0.8, 1.25, 2, np.inf]
    labels = ["< 0,5 · jauh di bawah", "0,5–0,8", "0,8–1,25 · setara nasional", "1,25–2", "> 2 · basis kuat"]
    kind = "diverging"
elif method == "Ambang bermakna":
    breaks = [-np.inf, -2, 0, 2, 5, np.inf]
    labels = ["< −2%", "−2% s.d. 0%", "0% s.d. 2%", "2% s.d. 5%", "> 5%"]
    kind = "diverging"
else:
    clean = df["nilai"].dropna()
    breaks = (data.jenks(indicator, sector, period, K) if method.startswith("Natural")
              else an.quantile_breaks(clean, K))
    breaks = sorted(set(breaks))
    labels = None
    kind = "signed" if indicator == "Pertumbuhan q-to-q" else "sequential"

# Pangsa dan pertumbuhan dalam persen: satuannya ikut tertulis di setiap label kelas legenda.
fmt = "{:.2f}" if indicator == "Location quotient" else "{:.1f}%"
if labels is None:
    df["kelas"] = an.classify(df["nilai"], breaks, fmt)
    labels = list(df["kelas"].cat.categories)
else:
    df["kelas"] = pd.cut(df["nilai"], bins=breaks, labels=labels, include_lowest=True, right=False)

if kind == "signed":
    colors = ch.signed_class_colors(breaks[: len(labels) + 1])
else:
    colors = ch.class_colors(len(labels), kind)
if kind == "diverging" and len(labels) == 5:
    # Simetris: langkah yang sama jauhnya dari titik tengah di kedua lengan.
    colors = [TK.div_neg[0], TK.div_neg[1], TK.div_mid, TK.div_pos[1], TK.div_pos[2]]
df["kelas"] = df["kelas"].astype(object).where(df["kelas"].notna(), "Tidak dapat dihitung")
if (df["kelas"] == "Tidak dapat dihitung").any():
    labels = labels + ["Tidak dapat dihitung"]
    colors = colors + [TK.na]

unit = {"Pangsa sektor": "%", "Location quotient": "", "Pertumbuhan q-to-q": "%"}[indicator]
sector_name = "PDRB" if sector == "TOTAL" else SECTOR_SHORT[sector]
sector_lc = sector_name if sector == "TOTAL" else sector_name.lower()  # singkatan tetap kapital
df["nilai_txt"] = df["nilai"].map(lambda v: idn(v, 2 if unit == "" else 1) + unit)
hover = ("<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
         f"{indicator} {sector_lc}: " + "%{customdata[2]}<br>"
         f"Nilai {sector_lc}: Rp" + "%{customdata[3]:,.1f} miliar<extra></extra>")

view = reg if province == "Seluruh Indonesia" else reg[reg["provinsi"] == province]
highlight = None if province == "Seluruh Indonesia" else list(view.index)

title_ind = {"Pangsa sektor": f"Porsi {sector_lc} dalam PDRB daerah",
             "Location quotient": f"Seberapa terkonsentrasi {sector_lc} dibanding nasional",
             "Pertumbuhan q-to-q": f"Perubahan {sector_lc} TW II terhadap TW I"}[indicator]
st.subheader(title_ind)
# Judul grafik satu baris: indikator, sektor, dan satuan. Periodenya ditulis di baris sumber.
tw = period.replace("Triwulan", "TW")
when = "TW II terhadap TW I" if indicator == "Pertumbuhan q-to-q" else f"{tw} 2026"
u_t = "" if unit == "" else f" ({unit})"
full, abbr = {"Pangsa sektor": ("Pangsa", "Pangsa"), "Location quotient": ("Location Quotient", "LQ"),
              "Pertumbuhan q-to-q": ("Pertumbuhan", "Tumbuh")}[indicator]


def fit(*options, limit=38):
    """Judul terpanjang yang masih muat satu baris di ponsel (~38 karakter)."""
    return next((o for o in options if len(o) <= limit), options[-1])


chart_title(fit(f"Peta {full} {sector_lc}{u_t}", f"{full} {sector_lc}{u_t}", f"{abbr} {sector_lc}{u_t}"))

show_choro = "Choropleth" in (layers or [])
show_bubble = "Lingkaran PDRB" in (layers or [])
plot_df = df if show_choro else df.assign(kelas="Tidak dapat dihitung")
fig = ch.choropleth_classes(
    geo, plot_df, "kelas", labels if show_choro else ["Tidak dapat dihitung"],
    colors if show_choro else [TK.land],
    ["kabkota", "provinsi", "nilai_txt", "pdrb"], hover,
    view_regions=view, height=560, highlight=highlight, width_px=1000,
)
if show_bubble:
    bub = df[df["pdrb"] > 0]
    ch.add_bubbles(fig, bub, "pdrb",
                   "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                   f"{sector_name}: " + "Rp%{customdata[2]:,.1f} miliar<extra></extra>")
st.plotly_chart(fig, config=ch.MAP_CONFIG, key="main_map")
if show_choro:
    swatches("Location quotient (LQ, tanpa satuan)" if indicator == "Location quotient"
             else f"{indicator} (%) · {method.lower()}", labels, colors)

if show_bubble:
    sizes = ch.bubble_legend(df["pdrb"])
    dots = "".join(
        f'<span><i style="width:{max(s, 3):.0f}px;height:{max(s, 3):.0f}px"></i>Rp{idn(v, 0)} miliar</span>'
        for v, s in sizes)
    st.html(f'<div class="legend-dots"><b>Luas lingkaran = Nilai {sector_name}, {period}</b>{dots}</div>')

why = {
    "Ambang bermakna": "Batas kelas dipilih karena maknanya, bukan karena sebaran datanya. Untuk LQ, "
                       "0,8–1,25 dianggap setara nasional dan di atas 2 menandakan sektor basis yang kuat. "
                       "Untuk pertumbuhan, nol menjadi titik tengah. Karena kedua sisinya bermakna, "
                       "skala warnanya divergen (biru di bawah acuan, jingga di atas).",
    "Natural breaks (Jenks)": "Batas kelas meminimalkan variasi di dalam kelas. Cocok untuk sebaran yang "
                              "menceng seperti pangsa sektor, karena kelompok alami dalam data tetap terlihat.",
    "Kuantil": "Setiap kelas berisi jumlah daerah yang kurang lebih sama. Perbedaan peringkat jadi mudah "
               "dilihat, tetapi rentang nilai antarkelas bisa sangat timpang.",
}[method]
source(f"{indicator} {sector_lc}, {when}. {why} Batas wilayah: {GEO_SOURCE}")

# --- ringkasan + tampilan tabel ---------------------------------------------
in_view = df.loc[view.index].dropna(subset=["nilai"])
top = in_view.nlargest(5, "nilai")
a, b = st.columns([1, 1.2], gap="large")
with a:
    where = "Indonesia" if province == "Seluruh Indonesia" else province
    st.html(f'<p style="height:2.5rem;margin:0;display:flex;align-items:center;font-weight:600">Lima tertinggi di {where}</p>')
    for _, r in top.iterrows():
        st.markdown(f"- {r['kabkota']} ({r['provinsi']}): **{r['nilai_txt']}**")
    if indicator == "Location quotient":
        n_base = int((in_view["nilai"] > 1).sum())
        st.markdown(f"{n_base} dari {len(in_view)} daerah memiliki LQ > 1 untuk {sector_lc}.")
with b:
    with st.expander("Lihat sebagai tabel"):
        st.dataframe(
            in_view[["kabkota", "provinsi", "nilai", "pdrb"]].rename(columns={
                "kabkota": "Kab/Kota", "provinsi": "Provinsi", "nilai": f"{indicator}",
                "pdrb": "Nilai (miliar Rp)"}).sort_values(indicator, ascending=False),
            hide_index=True, height=320,
        )

# --- LISA -------------------------------------------------------------------
st.header("Apakah pola ini mengelompok?")
mo = data.moran(indicator, sector, period)
# Kalimat disusun dari indikator, sektor, dan hasil uji, sehingga ikut berubah saat kontrol diganti.
subject, short = {
    "Location quotient": (f"nilai <em>location quotient</em> (LQ) {sector_lc}", "LQ"),
    "Pangsa sektor": (f"porsi {sector_lc} dalam PDRB daerah", "porsi"),
    "Pertumbuhan q-to-q": (f"pertumbuhan {sector_lc}", "pertumbuhan"),
}[indicator]
significant = mo["p"] < 0.05
if mo["I"] > 0 and significant:
    verdict = (f"cenderung mengelompok secara spasial. Daerah dengan {short} yang tinggi cenderung berdekatan "
               f"dengan daerah yang juga tinggi, begitu pula daerah dengan {short} rendah.")
elif not significant:
    verdict = "tidak menunjukkan pengelompokan spasial yang berarti."
else:
    verdict = (f"cenderung berselang-seling: daerah dengan {short} tinggi bertetangga dengan daerah yang "
               f"{short} rendah.")
with st.container(key="moran_text"):
    st.markdown(
        f"**Moran’s I = {idn(mo['I'], 3)}** menunjukkan bahwa {subject} {verdict} "
        f"Hasil ini {'signifikan' if significant else 'tidak signifikan'} (p = {idn(mo['p'], 3)}); jika polanya acak, "
        f"nilai Moran’s I yang diharapkan sekitar {idn(mo['expected'], 3)}. Pada peta, hanya daerah dengan hasil "
        f"analisis lokal yang signifikan (p < 0,05) yang diberi warna, tanpa koreksi uji berganda "
        f"(lihat Data & metode).",
        unsafe_allow_html=True,
    )
ldf = df.loc[mo["kode"]].copy()
ldf["kuadran"] = mo["quadrant"]
lisa_labels = [q for q in TK.lisa if q in set(ldf["kuadran"])]
c1, c2 = st.columns([1.5, 1], gap="large")
with c1:
    chart_title(fit(f"Peta LISA {short} {sector_lc}", f"LISA {short} {sector_lc}",
                    f"LISA {'tumbuh' if short == 'pertumbuhan' else short} {sector_lc}"))
    fig = ch.choropleth_classes(
        geo, ldf, "kuadran", lisa_labels, [TK.lisa[q] for q in lisa_labels],
        ["kabkota", "provinsi", "kuadran", "nilai_txt"],
        "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}<br>"
        "Nilai: %{customdata[3]}<extra></extra>",
        view_regions=view, height=480, highlight=highlight, width_px=580,
    )
    st.plotly_chart(fig, config=ch.MAP_CONFIG, key="lisa_map")
    swatches("LISA", lisa_labels, [TK.lisa[q] for q in lisa_labels], "hanya p < 0,05", center=True)
    source(f"{short} {sector_lc}, {when}; hanya p < 0,05 yang diwarnai; bobot 6 tetangga terdekat, "
           "999 permutasi bersyarat")
with c2:
    chart_title(f"Moran scatterplot {short}")
    st.plotly_chart(ch.moran_scatter(mo["z"], mo["lag"], np.asarray(mo["quadrant"]),
                                     ldf["kabkota"].to_numpy(), mo["I"]), config=ch.PLOT_CONFIG)
    source(f"{short} {sector_lc}, {when}; kemiringan garis = Moran's I; bobot 6 tetangga terdekat")
