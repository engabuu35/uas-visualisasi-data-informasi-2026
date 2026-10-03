"""Semua figur Plotly. Fungsi di sini hanya menggambar; perhitungan ada di analysis.py."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import SECTOR_SHORT
from theme import LABEL_INK, diverging_scale, tokens

FONT = "'Source Sans 3', 'Source Sans Pro', system-ui, sans-serif"
PLOT_CONFIG = {"displaylogo": False, "responsive": True,
               "modeBarButtonsToRemove": ["toImage", "select2d", "lasso2d"]}
SELECT_CONFIG = {"displaylogo": False, "responsive": True, "modeBarButtonsToRemove": ["toImage"]}
MAP_CONFIG = {"displaylogo": False, "responsive": True, "scrollZoom": True,
              "modeBarButtonsToRemove": ["toImage"]}

# Warna TIDAK disimpan sebagai konstanta modul: setiap fungsi membaca token
# aktif (mode terang/gelap x palet) saat dipanggil, lewat `tk = tokens()`.


def idn(value, nd=1):
    """Format angka gaya Indonesia: 1.234,5"""
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "–"
    s = f"{value:,.{nd}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def signed(value, nd=1):
    return ("+" if value > 0 else "") + idn(value, nd).replace("-", "−")


def _symbol(color):
    """Bentuk penanda mengikuti warna klaster (encoding ganda yang konsisten)."""
    tk = tokens()
    return tk.symbols[tk.cluster.index(color) % len(tk.symbols)]


def base_layout(fig, height=420, title=None, legend=True, margin=None):
    tk = tokens()
    fig.update_layout(
        height=height,
        separators=",.",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=tk.ink, size=13),
        margin=margin or dict(l=8, r=8, t=40 if title else 12, b=8),
        title=dict(text=title, x=0, xanchor="left", font=dict(size=15, color=tk.ink)) if title else None,
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="center", x=0.5,
                    font=dict(size=12, color=tk.soft), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=tk.paper, bordercolor=tk.rule, font=dict(family=FONT, color=tk.ink, size=13)),
    )
    fig.update_xaxes(gridcolor=tk.grid, zerolinecolor=tk.rule, linecolor=tk.rule,
                     tickfont=dict(color=tk.soft), title_font=dict(color=tk.soft, size=12))
    fig.update_yaxes(gridcolor=tk.grid, zerolinecolor=tk.rule, linecolor=tk.rule,
                     tickfont=dict(color=tk.soft), title_font=dict(color=tk.soft, size=12))
    return fig


# ---------------------------------------------------------------------------
# Peta (dasar)
# ---------------------------------------------------------------------------

def _hbar(title, **kw):
    """Colorbar mendatar di bawah grafik, rata tengah."""
    return dict(title=dict(text=title, side="top"), orientation="h", x=0.5, xanchor="center",
                y=-0.04, yanchor="top", thickness=10, len=0.5, **kw)


def _map_view(regions: pd.DataFrame | None, width_px: int = 900):
    """Pusat dan zoom agar kotak batas wilayah muat pada lebar peta perkiraan.

    Pada Web Mercator, lebar dunia = 512 x 2^zoom piksel, sehingga
    zoom = log2(lebar_px x 360 / (rentang_bujur x 512)).
    """
    if regions is None or regions.empty:
        lat0, lat1, lon0, lon1 = -11.0, 6.0, 95.0, 141.0
    else:
        lat0, lat1 = regions["lat"].min(), regions["lat"].max()
        lon0, lon1 = regions["lon"].min(), regions["lon"].max()
    span = max(lon1 - lon0, (lat1 - lat0) * 1.6, 0.8) * 1.3
    zoom = float(np.clip(np.log2(width_px * 360 / (span * 512)), 2.4, 9.5))
    return {"lat": (lat0 + lat1) / 2, "lon": (lon0 + lon1) / 2}, zoom


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def discrete_scale(colors):
    """Skala warna bertingkat untuk z = indeks kelas + 0,5."""
    n = len(colors)
    scale = []
    for i, c in enumerate(colors):
        scale += [[i / n, c], [(i + 1) / n, c]]
    return scale


def class_colors(n: int, kind: str):
    tk = tokens()
    if kind == "diverging":
        ramp = tk.div_neg + [tk.div_mid] + tk.div_pos
        if n == len(ramp):
            return ramp
        idx = np.linspace(0, len(ramp) - 1, n).round().astype(int)
        return [ramp[i] for i in idx]
    idx = np.linspace(0, len(tk.seq) - 1, n).round().astype(int)
    return [tk.seq[i] for i in idx]


def signed_class_colors(breaks):
    """Warna divergen untuk kelas yang batasnya tidak simetris terhadap nol
    (mis. kuantil pertumbuhan). Kelas sepenuhnya < 0 diberi lengan biru,
    sepenuhnya > 0 lengan jingga, kelas yang memuat nol diberi abu tengah.
    Skema sekuensial di sini keliru: data bertanda butuh titik tengah."""
    tk = tokens()
    blue_arm = tk.div_neg[::-1]           # dekat tengah -> ekstrem
    edges = list(zip(breaks[:-1], breaks[1:]))
    neg = [i for i, (lo, hi) in enumerate(edges) if hi <= 0]
    pos = [i for i, (lo, hi) in enumerate(edges) if lo >= 0]
    out = [tk.div_mid] * len(edges)
    for rank, i in enumerate(reversed(neg)):
        out[i] = blue_arm[min(rank, len(blue_arm) - 1)]
    for rank, i in enumerate(pos):
        out[i] = tk.div_pos[min(rank, len(tk.div_pos) - 1)]
    return out


def choropleth_classes(geojson, df, class_col, labels, colors, hover_cols,
                       hover_template, view_regions=None, height=560,
                       highlight=None, width_px=900):
    """Choropleth kelas diskret dalam SATU trace (GeoJSON tidak diduplikasi
    per kelas, penting untuk ukuran halaman di ponsel)."""
    tk = tokens()
    codes = {lab: i for i, lab in enumerate(labels)}
    z = df[class_col].map(codes).astype(float) + 0.5
    fig = go.Figure(go.Choroplethmap(
        geojson=geojson, featureidkey="properties.kode", locations=df["kode"],
        z=z, zmin=0, zmax=len(labels), colorscale=discrete_scale(colors),
        marker=dict(line=dict(width=0.4, color=tk.paper), opacity=0.92),
        customdata=df[hover_cols].to_numpy(), hovertemplate=hover_template,
        showscale=False,
        name="",
    ))
    if highlight is not None and len(highlight):
        fig.add_trace(go.Choroplethmap(
            geojson=geojson, featureidkey="properties.kode", locations=highlight,
            z=[1] * len(highlight), colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False, marker=dict(line=dict(width=1.6, color=tk.ink)), hoverinfo="skip",
        ))
    center, zoom = _map_view(view_regions, width_px)
    fig.update_layout(
        map=dict(style=tk.basemap, center=center, zoom=zoom),
        height=height, margin=dict(l=0, r=0, t=0, b=0), separators=",.",
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, color=tk.ink),
        hoverlabel=dict(bgcolor=tk.paper, bordercolor=tk.rule, font=dict(family=FONT, color=tk.ink)),
    )
    return fig


def add_bubbles(fig, df, size_col, hover_template, max_px=34, name="Simbol proporsional"):
    """Simbol proporsional: LUAS lingkaran sebanding nilai (sizemode='area')."""
    tk = tokens()
    vmax = df[size_col].max()
    fig.add_trace(go.Scattermap(
        lat=df["lat"], lon=df["lon"], mode="markers", name=name,
        marker=dict(size=df[size_col], sizemode="area", sizeref=2 * vmax / max_px ** 2,
                    sizemin=1.5, color=tk.ink, opacity=0.45),
        customdata=df[["kabkota", "provinsi", size_col]].to_numpy(),
        hovertemplate=hover_template, showlegend=False,
    ))
    return fig


def bubble_legend(values, max_px=34):
    """Teks keterangan ukuran simbol (dirender di Streamlit, bukan di peta)."""
    vmax = float(np.nanmax(values))
    nice = [vmax, vmax / 4, vmax / 16]
    return [(v, max_px * math.sqrt(v / vmax)) for v in nice]


# ---------------------------------------------------------------------------
# Multivariat
# ---------------------------------------------------------------------------

def pca_biplot(scores, explained, loadings, cluster, colors, names, provinces,
               highlight=None, outliers=None, show_arrows=True, label_outliers=5, n_arrows=7, compact=False):
    """Biplot PC1-PC2. Satu trace per klaster (warna + bentuk = encoding ganda).

    Mengembalikan (fig, trace_index) - trace_index[curve][point] = kode wilayah,
    dipakai untuk menerjemahkan event seleksi Streamlit.
    """
    tk = tokens()
    fig = go.Figure()
    trace_index = []
    highlight = set(highlight or [])
    for name in colors:
        members = cluster.index[cluster == name]
        if len(members) == 0:
            continue
        s = scores.loc[members]
        dim = highlight and not s.index.isin(list(highlight)).all()
        opac = [1.0 if (not highlight or k in highlight) else 0.18 for k in s.index]
        fig.add_trace(go.Scatter(
            x=s["PC1"], y=s["PC2"], mode="markers", name=f"{name} ({len(s)})",
            marker=dict(size=9, color=colors[name], symbol=_symbol(colors[name]),
                        opacity=opac if dim else 0.85, line=dict(color=tk.surface, width=0.8)),
            customdata=np.column_stack([names.loc[s.index], provinces.loc[s.index], [name] * len(s)]),
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}"
                          "<br>PC1 %{x:.2f} · PC2 %{y:.2f}<extra></extra>",
        ))
        trace_index.append(list(s.index))

    if show_arrows:
        span = max(scores["PC1"].abs().quantile(0.98), scores["PC2"].abs().quantile(0.98))
        mag = np.hypot(loadings["PC1"], loadings["PC2"])
        scale = span / mag.max() * 0.95
        for code in mag.sort_values(ascending=False).index[:n_arrows]:
            x, y = loadings.loc[code, "PC1"] * scale, loadings.loc[code, "PC2"] * scale
            fig.add_annotation(x=x, y=y, ax=0, ay=0, axref="x", ayref="y", showarrow=True,
                               arrowhead=2, arrowsize=1, arrowwidth=1.3, arrowcolor=tk.soft,
                               text="", standoff=0)
            fig.add_annotation(x=x, y=y, text=SECTOR_SHORT[code], showarrow=False,
                               font=dict(size=11, color=tk.ink),
                               xanchor="left" if x >= 0 else "right", yanchor="bottom" if y >= 0 else "top")

    if outliers is not None and label_outliers:
        top = outliers.sort_values(ascending=False).index[:label_outliers]
        offsets = [(-10, -22), (10, 22), (-36, 14), (30, -18), (0, 26), (-24, -30)]
        for i, code in enumerate(top):
            ax, ay = offsets[i % len(offsets)]
            fig.add_annotation(x=scores.loc[code, "PC1"], y=scores.loc[code, "PC2"],
                               text=names.loc[code].replace("Kota ", "Kt. "), showarrow=True,
                               arrowwidth=0.8, arrowcolor=tk.muted, ax=ax, ay=ay,
                               font=dict(size=11, color=tk.soft))

    # Rentang sumbu mengikuti sebaran data dengan skala X:Y setara. Kelebihan ruang mendatar
    # diisi rentang X; kelebihan ruang tegak memperkecil area plot (bukan rentang Y kosong).
    pad = lambda lo, hi: [lo - (hi - lo) * .08, hi + (hi - lo) * .08]
    base_layout(fig, height=440 if compact else 600)
    fig.update_layout(dragmode="lasso", legend=dict(y=1.02, font=dict(size=11)),
                      margin=dict(l=8, r=8, t=56, b=8))
    fig.update_xaxes(title=f"PC1 · {idn(explained[0] * 100)}% varians<br>makin besar: ke arah jasa perkotaan",
                     zeroline=True, range=pad(scores["PC1"].min(), scores["PC1"].max()))
    fig.update_yaxes(title=f"PC2 · {idn(explained[1] * 100)}% varians<br>makin besar: ke arah industri",
                     zeroline=True, scaleanchor="x", scaleratio=1, constrain="domain",
                     range=pad(scores["PC2"].min(), scores["PC2"].max()))
    return fig, trace_index


def scree(explained, n_pc_outlier):
    tk = tokens()
    n = min(10, len(explained))
    d = pd.DataFrame({"pc": [f"PC{i + 1}" for i in range(n)], "v": explained[:n] * 100})
    d["cum"] = d["v"].cumsum()
    fig = go.Figure(go.Bar(
        x=d["pc"], y=d["v"], marker=dict(color=[tk.accent if i < 2 else tk.context for i in range(n)],
                                         cornerradius=3),
        customdata=d[["cum"]].to_numpy(),
        hovertemplate="%{x}: %{y:.1f}% (kumulatif %{customdata[0]:.1f}%)<extra></extra>",
    ))
    base_layout(fig, height=260, legend=False)
    fig.update_yaxes(title="% varians", ticksuffix="%")
    fig.update_xaxes(title=None)
    return fig


def parallel_coords(shares, cluster, colors, dims, highlight=None):
    """Parallel coordinates pangsa sektor. Garis terpilih digambar paling akhir
    agar berada di atas."""
    tk = tokens()
    d = shares[dims].copy()
    d["_c"] = cluster
    names = list(colors)
    if highlight:
        d["_v"] = d.index.isin(list(highlight)).astype(int)
        d = d.sort_values("_v")
        color = d["_v"]
        scale = [[0, _rgba(tk.rule, .45)], [1, tk.accent_deep]]
        cmin, cmax = 0, 1
    else:
        # Klaster terkecil digambar terakhir (di atas) agar tidak tertimbun.
        size = d["_c"].map(d["_c"].value_counts())
        d = d.assign(_s=size).sort_values("_s", ascending=False, kind="stable")
        color = d["_c"].map({n: i for i, n in enumerate(names)})
        # Transparansi menurut ukuran klaster: yang besar memudar jadi "awan", yang kecil tetap tegas.
        counts = d["_c"].value_counts()
        nmax = max(int(counts.max()), 1)
        scale = discrete_scale([_rgba(colors[n], round(0.28 + 0.62 * (1 - counts.get(n, 0) / nmax), 2))
                                for n in names])
        cmin, cmax = -0.5, len(names) - 0.5

    def axis(c):
        top = float(np.ceil(d[c].quantile(0.995)))
        # Tiga penanda saja (0, tengah, maks) dengan satuan %, agar angka tidak menimpa garis.
        vals = [0, round(top / 2), top]
        return dict(label=SECTOR_SHORT[c], values=d[c], range=[0, top], tickvals=vals,
                    ticktext=[f"{idn(v, 0)}%" for v in vals])

    fig = go.Figure(go.Parcoords(
        line=dict(color=color, colorscale=scale, cmin=cmin, cmax=cmax),
        unselected=dict(line=dict(color=tk.rule, opacity=0.05)),
        dimensions=[axis(c) for c in dims],
        labelfont=dict(size=13, color=tk.ink), tickfont=dict(size=11, color=tk.soft),
        rangefont=dict(size=11, color=tk.soft), labelangle=-18, labelside="top",
    ))
    base_layout(fig, height=540, legend=False, margin=dict(l=48, r=48, t=96, b=28))
    return fig


def clustered_heatmap(z, row_order, col_order, cluster, colors, names, highlight=None):
    """Heatmap terklaster: baris = wilayah (urutan dendrogram Ward),
    kolom = sektor (urutan dendrogram korelasi). Strip kiri = klaster."""
    tk = tokens()
    rows = [r for r in row_order if (not highlight or r in highlight)]
    zz = z.loc[rows, col_order].clip(-3, 3)
    cl_names = list(colors)
    strip = cluster.loc[rows].map({n: i for i, n in enumerate(cl_names)}).to_numpy()[:, None]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.035, 0.965],
                        horizontal_spacing=0.006)
    fig.add_trace(go.Heatmap(
        z=strip + 0.5, x=["Klaster"], y=list(range(len(rows))), zmin=0, zmax=len(cl_names),
        colorscale=discrete_scale([colors[n] for n in cl_names]), showscale=False,
        customdata=np.array(cluster.loc[rows])[:, None],
        hovertemplate="%{customdata}<extra></extra>",
    ), 1, 1)
    hover_names = np.repeat(names.loc[rows].to_numpy()[:, None], len(col_order), axis=1)
    fig.add_trace(go.Heatmap(
        z=zz.to_numpy(), x=[SECTOR_SHORT[c] for c in col_order], y=list(range(len(rows))),
        zmin=-3, zmax=3, zmid=0, colorscale=diverging_scale(tk), customdata=hover_names,
        colorbar=_hbar("z-score pangsa", tickvals=[-3, -1.5, 0, 1.5, 3], ticktext=["≤ −3", "−1,5", "0", "1,5", "≥ 3"]),
        hovertemplate="<b>%{customdata}</b><br>%{x}: z = %{z:.2f}<extra></extra>",
    ), 1, 2)
    show_labels = len(rows) <= 45
    fig.update_yaxes(autorange="reversed", showticklabels=show_labels,
                     tickvals=list(range(len(rows))) if show_labels else None,
                     ticktext=list(names.loc[rows]) if show_labels else None, row=1, col=1)
    fig.update_xaxes(tickangle=-40, side="top", row=1, col=2)
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    base_layout(fig, height=max(360, min(620, 14 * len(rows) + 140)), legend=False,
                margin=dict(l=8, r=8, t=110, b=64))
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return fig


def cluster_profile_heatmap(profile, col_order, counts):
    tk = tokens()
    p = profile[col_order].clip(-3, 3)
    ylab = [f"{k} ({counts.get(k, 0)})" for k in p.index]
    text = np.vectorize(lambda v: idn(v, 1))(p.to_numpy())
    fig = go.Figure(go.Heatmap(
        z=p.to_numpy(), x=[SECTOR_SHORT[c] for c in col_order], y=ylab, zmin=-3, zmax=3, zmid=0,
        colorscale=diverging_scale(tk), text=text, texttemplate="%{text}", textfont=dict(size=10),
        colorbar=_hbar("rata-rata z"),
        hovertemplate="<b>%{y}</b><br>%{x}: z rata-rata %{z:.2f}<extra></extra>",
    ))
    base_layout(fig, height=390, legend=False, margin=dict(l=8, r=8, t=100, b=64))
    fig.update_xaxes(tickangle=-40, side="top", gridcolor="rgba(0,0,0,0)")
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
    return fig


def profile_dumbbell(sel_median, all_median, label="Terpilih"):
    tk = tokens()
    d = pd.DataFrame({"sel": sel_median, "all": all_median})
    d["diff"] = d["sel"] - d["all"]
    d = d.sort_values("sel")
    ylab = [SECTOR_SHORT[c] for c in d.index]
    fig = go.Figure()
    for y, a, b in zip(ylab, d["all"], d["sel"]):
        fig.add_shape(type="line", y0=y, y1=y, x0=a, x1=b, line=dict(color=tk.rule, width=3))
    fig.add_trace(go.Scatter(x=d["all"], y=ylab, mode="markers", name="Median 514 daerah",
                             marker=dict(size=10, color=tk.surface, line=dict(color=tk.soft, width=2)),
                             hovertemplate="%{y}: %{x:.1f}% (median nasional)<extra></extra>"))
    fig.add_trace(go.Scatter(x=d["sel"], y=ylab, mode="markers", name=label,
                             marker=dict(size=11, color=tk.accent_deep),
                             hovertemplate="%{y}: %{x:.1f}% (median terpilih)<extra></extra>"))
    base_layout(fig, height=470)
    fig.update_xaxes(title="Median pangsa sektor (%)", ticksuffix="%", rangemode="tozero")
    fig.update_yaxes(title=None, gridcolor="rgba(0,0,0,0)")
    return fig


# ---------------------------------------------------------------------------
# Geospasial - Moran
# ---------------------------------------------------------------------------

def moran_scatter(z, lag, quadrant, names, I):
    tk = tokens()
    fig = go.Figure()
    for q, col in tk.lisa.items():
        m = quadrant == q
        if not m.any():
            continue
        fig.add_trace(go.Scatter(
            x=z[m], y=lag[m], mode="markers", name=q,
            marker=dict(size=7, color=col, line=dict(color=tk.surface, width=0.6),
                        opacity=0.9 if q != "Tidak signifikan" else 0.7),
            customdata=names[m][:, None],
            hovertemplate="<b>%{customdata[0]}</b><br>z = %{x:.2f}<br>rata-rata tetangga = %{y:.2f}"
                          "<extra></extra>",
        ))
    lo, hi = float(min(z.min(), lag.min())), float(max(z.max(), lag.max()))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[I * lo, I * hi], mode="lines", name=f"kemiringan = I = {idn(I, 2)}",
                             line=dict(color=tk.ink, width=1.5), hoverinfo="skip"))
    base_layout(fig, height=420)
    fig.update_layout(legend=dict(font=dict(size=11), entrywidth=0, itemsizing="constant"),
                      margin=dict(l=8, r=8, t=80, b=8))
    fig.update_xaxes(title="Nilai wilayah (z-score)", zeroline=True)
    fig.update_yaxes(title="Rata-rata 6 tetangga terdekat (z)", zeroline=True)
    return fig


# ---------------------------------------------------------------------------
# Hierarki
# ---------------------------------------------------------------------------

def _luminance(hex_color):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (lin(int(hex_color[i:i + 2], 16)) for i in (1, 3, 5))
    return .2126 * r + .7152 * g + .0722 * b


def _label_colors(values, scale, lim):
    """Warna teks per kotak: hitam atau putih, mana yang kontrasnya lebih tinggi
    terhadap warna kotak. Plotly memilih #444/putih sendiri, dan keduanya hanya
    sekitar 3:1 di warna tengah skala. Warna kotak dihitung ulang seperti Plotly
    (interpolasi RGB linear di antara titik skala)."""
    dark_txt, light_txt = LABEL_INK
    l_dark, l_light = _luminance(dark_txt), _luminance(light_txt)
    pos = [p for p, _ in scale]
    rgb = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for _, c in scale], dtype=float)
    out = []
    for v in values:
        t = (min(max(v, -lim), lim) + lim) / (2 * lim)
        cell = "#" + "".join(f"{round(np.interp(t, pos, rgb[:, j])):02X}" for j in range(3))
        lc = _luminance(cell)
        out.append(dark_txt if (lc + .05) / (l_dark + .05) >= (l_light + .05) / (lc + .05) else light_txt)
    return out


def _hier_common(h, color_lim):
    tk = tokens()
    # Pertumbuhan dari basis nol tidak terdefinisi; tampilkan apa adanya alih-alih "nan%".
    growth_txt = h["tumbuh"].map(lambda v: "tidak dapat dihitung (TW I = 0)" if pd.isna(v)
                                 else signed(v, 2) + "%")
    # Versi pendek untuk label kotak: pertumbuhan ikut ditulis, bukan hanya lewat
    # warna (WCAG 1.4.1), dengan tanda +/− sebagai teks, bukan panah berwarna.
    growth_short = h["tumbuh"].map(lambda v: "–" if pd.isna(v) else signed(v, 1) + "%")
    custom = np.column_stack([
        h["tingkat"], h["nilai"], h["pangsa_induk"].fillna(100), growth_txt, h["q1"], h["q2"], growth_short,
    ])
    hover = ("<b>%{label}</b> · %{customdata[0]}<br>"
             "PDRB: Rp%{customdata[1]:,.1f} miliar<br>"
             "Porsi dari induk: %{customdata[2]:.1f}%<br>"
             "TW II vs TW I: %{customdata[3]}<extra></extra>")
    scale = diverging_scale(tk)
    values = h["tumbuh"].fillna(0)
    marker = dict(
        colors=values, colorscale=scale, cmid=0, cmin=-color_lim, cmax=color_lim,
        line=dict(color=tk.paper, width=0.6),
        colorbar=_hbar("Tumbuh q-to-q (%)", ticksuffix="%"),
    )
    return custom, hover, marker, _label_colors(values, scale, color_lim)


def treemap(h, color_lim, root_id="Indonesia", height=560):
    tk = tokens()
    custom, hover, marker, text_colors = _hier_common(h, color_lim)
    fig = go.Figure(go.Treemap(
        ids=h["id"], labels=h["label"], parents=h["parent"], values=h["nilai"],
        branchvalues="total", customdata=custom, hovertemplate=hover, marker=marker,
        maxdepth=3, level=root_id, pathbar=dict(visible=True, side="top", thickness=26,
                                                textfont=dict(size=13)),
        texttemplate="<b>%{label}</b><br>Porsi %{customdata[2]:.1f}%<br>Tumbuh %{customdata[6]}",
        textfont=dict(size=13, color=text_colors),
        tiling=dict(pad=2), root=dict(color="rgba(0,0,0,0)"),
    ))
    base_layout(fig, height=height, legend=False, margin=dict(l=0, r=0, t=8, b=64))
    return fig


def icicle(h, color_lim, root_id="Indonesia", height=560):
    tk = tokens()
    custom, hover, marker, text_colors = _hier_common(h, color_lim)
    fig = go.Figure(go.Icicle(
        ids=h["id"], labels=h["label"], parents=h["parent"], values=h["nilai"],
        branchvalues="total", customdata=custom, hovertemplate=hover, marker=marker,
        maxdepth=3, level=root_id, tiling=dict(orientation="v", pad=2),
        pathbar=dict(visible=True, side="top", thickness=26, textfont=dict(size=13)),
        texttemplate="<b>%{label}</b><br>Porsi %{customdata[2]:.1f}%<br>Tumbuh %{customdata[6]}",
        textfont=dict(size=13, color=text_colors),
        root=dict(color="rgba(0,0,0,0)"),
    ))
    base_layout(fig, height=height, legend=False, margin=dict(l=0, r=0, t=8, b=64))
    return fig
