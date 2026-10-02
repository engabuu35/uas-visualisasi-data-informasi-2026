"""Lapisan data halaman Cerita: satu-satunya sumber angka yang tampil di sana.

Templat teks dan grafik SVG hanya memformat nilai dari `figures()`; tidak ada
angka yang diketik sebagai string. Kalau data BPS diperbarui, seluruh cerita
ikut berubah, termasuk kalimat yang bergantung pada urutan (siapa tercepat,
siapa paling lambat). Versi sebelumnya menulis "Jawa hanya +2,2%" seolah
Jawa paling lambat, padahal Maluku-Papua lebih lambat; kalimat semacam itu
sekarang dibentuk dari peringkat, bukan dari asumsi penulis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

import analysis as an
import data
import preprocess as pp
from config import (
    ISLAND_ORDER, N_CLUSTERS, PERMUTATIONS, SECTOR_SHORT, SPATIAL_K,
)

PERIOD = "Triwulan II"   # cerita selalu memakai triwulan terbaru
PREV = "Triwulan I"
TOP_N = 10               # "sepuluh daerah teratas"
PAPUA = ("91", "94")     # kode provinsi Papua Barat dan Papua (batas 2019)
DKI = "31"
SMALL_RANK = 100        # "tidak masuk 100 besar PDRB"

_WORDS = ["nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan",
          "sembilan", "sepuluh", "sebelas", "dua belas"]


def word(n: int) -> str:
    """Bilangan kecil ditulis dengan huruf, sesuai kaidah bahasa Indonesia."""
    return _WORDS[n] if 0 <= n < len(_WORDS) else str(n)


def region_label(reg: pd.DataFrame, kode: str) -> str:
    """Nama tampilan. Tabel BPS menulis kabupaten tanpa awalan, sehingga
    'Bekasi' dan 'Bogor' mudah tertukar dengan kotanya; awalan 'Kab.' mencegahnya."""
    r = reg.loc[kode]
    return r["kabkota"] if r["jenis"] == "Kota" else f"Kab. {r['kabkota']}"


def join_id(items: list[str]) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return f"{items[0]} dan {items[1]}"
    return ", ".join(items[:-1]) + f", dan {items[-1]}"


def _by_name(summary: pd.DataFrame, name: str) -> pd.Series:
    row = summary[summary["klaster"] == name]
    if row.empty:
        raise ValueError(f"Klaster '{name}' tidak terbentuk; teks cerita perlu ditinjau ulang.")
    return row.iloc[0]


@st.cache_data(show_spinner="Menyiapkan cerita…")
def figures() -> dict:
    reg = data.regions()
    long = data.long_df()
    v2, v1 = data.values(PERIOD), data.values(PREV)
    tot2, tot1 = v2.sum(axis=1), v1.sum(axis=1)
    nat2, nat1 = float(tot2.sum()), float(tot1.sum())
    island = reg.loc[tot2.index, "pulau"]
    f: dict = {
        "n_regions": int(len(tot2)),
        "n_sectors": int(v2.shape[1]),
        "national": nat2,
        "national_prev": nat1,
        "growth": (nat2 / nat1 - 1) * 100,
        "spatial_k": SPATIAL_K,
        "permutations": PERMUTATIONS,
        "year": int(long["tahun"].max()),
        "period": PERIOD, "prev": PREV,
    }

    # --- Babak I: konsentrasi -------------------------------------------------
    conc = pp.concentration(tot2)
    f["conc_y"] = conc["kumulatif_pct"].round(3).tolist()
    f["conc_names"] = [region_label(reg, k) for k in conc["kode"]]
    f["n_half"] = int((conc["kumulatif_pct"] < 50).sum() + 1)
    # Sensitivitas: penyebut jumlah 17 sektor vs baris PDRB resmi BPS.
    row = long[(long["periode"] == PERIOD) & (long["kode_sektor"] == "TOTAL")].set_index("kode")["nilai"]
    f["n_half_bps_row"] = int((pp.concentration(row)["kumulatif_pct"] < 50).sum() + 1)
    top = list(conc["kode"][:TOP_N])
    f["top_n"] = TOP_N
    f["top_share"] = float(conc["kumulatif_pct"].iloc[TOP_N - 1])
    dki_top = [k for k in top if reg.loc[k, "kode_prov"] == DKI]
    rest = [region_label(reg, k) for k in top if k not in dki_top]
    head = [f"{word(len(dki_top))} kota di Jakarta"] if len(dki_top) > 1 else [region_label(reg, k) for k in dki_top]
    f["top_text"] = join_id(head + rest)

    share2 = tot2.groupby(island).sum() / nat2 * 100
    share1 = tot1.groupby(island).sum() / nat1 * 100
    f["island_share"] = {k: float(share2[k]) for k in ISLAND_ORDER}
    f["jawa_share"], f["jawa_share_prev"] = float(share2["Jawa"]), float(share1["Jawa"])
    f["jawa_provinces"] = int(reg.loc[reg["pulau"] == "Jawa", "kode_prov"].nunique())
    dki = reg.index[reg["kode_prov"] == DKI]
    f["dki_n"], f["dki_share"] = int(len(dki)), float(tot2[dki].sum() / nat2 * 100)

    # --- Babak II: struktur (klaster) ----------------------------------------
    mv = data.multivariate(PERIOD)
    colors = data.cluster_colors(mv)
    summary = pd.DataFrame({"klaster": mv.cluster, "pdrb": tot2, "pulau": island})
    rows = []
    for name in colors:
        m = summary[summary["klaster"] == name]
        if m.empty:
            continue
        isl = m["pulau"].value_counts()
        rows.append({
            "klaster": name, "color": colors[name], "n": int(len(m)),
            "pct_regions": len(m) / len(summary) * 100,
            "pct_pdrb": m["pdrb"].sum() / nat2 * 100,
            "top_island": isl.index[0], "top_island_n": int(isl.iloc[0]),
        })
    clusters = pd.DataFrame(rows)
    f["clusters"] = clusters.to_dict("records")
    f["cluster_of"] = mv.cluster.to_dict()
    f["n_clusters"] = int(len(clusters))

    agr = _by_name(clusters, "Agraris")
    f["agr"] = {"n": int(agr["n"]), "pct_regions": float(agr["pct_regions"]), "pct_pdrb": float(agr["pct_pdrb"])}

    korp_name = "Pusat jasa korporat"
    k = _by_name(clusters, korp_name)
    members = mv.cluster.index[mv.cluster == korp_name]
    in_dki = [c for c in members if reg.loc[c, "kode_prov"] == DKI]
    shares = data.shares(PERIOD)
    outside = [c for c in members if c not in in_dki]
    # Anggota di luar 100 besar PDRB: masuk karena PORSI jasa perusahaannya,
    # bukan karena ekonominya besar. Ini konsekuensi standardisasi z-score
    # (sektor yang variasinya kecil antardaerah ikut diperbesar), jadi perlu
    # dikatakan terang-terangan agar label klaster tidak menyesatkan.
    rank = tot2.rank(ascending=False).astype(int)
    small = [c for c in outside if rank[c] > SMALL_RANK]
    f["korp"] = {
        "n": int(k["n"]), "pct_pdrb": float(k["pct_pdrb"]), "n_dki": len(in_dki),
        "others": [region_label(reg, c) for c in outside if c not in small],
        "small": [region_label(reg, c) for c in small],
        "small_rank": [int(rank[c]) for c in small],
        "small_mn": [float(shares.loc[c, "M,N"]) for c in small],
        "median_mn": float(shares["M,N"].median()),
        "small_rank_cut": SMALL_RANK,
    }

    gov_name = "Ditopang belanja pemerintah"
    g = _by_name(clusters, gov_name)
    gm = mv.cluster.index[mv.cluster == gov_name]
    non_papua = []
    for c in gm:
        if reg.loc[c, "kode_prov"] in PAPUA:
            continue
        top_sector = shares.loc[c].idxmax()
        non_papua.append({
            "kode": c, "label": region_label(reg, c), "name": reg.loc[c, "kabkota"],
            "sector": SECTOR_SHORT[top_sector].lower(), "share": float(shares.loc[c, top_sector]),
            "is_national_max": bool(shares[top_sector].idxmax() == c),
        })
    f["gov"] = {"n": int(g["n"]), "pct_pdrb": float(g["pct_pdrb"]),
                "top_sectors": [SECTOR_SHORT[c].lower() for c in mv.cluster_profile.loc[gov_name].nlargest(2).index],
                "n_papua": int(reg.loc[gm, "kode_prov"].isin(PAPUA).sum()), "non_papua": non_papua}

    # Sensitivitas jumlah klaster: apakah "Agraris" tetap sebesar ini?
    agr_by_k = {}
    for kk in (N_CLUSTERS - 1, N_CLUSTERS, N_CLUSTERS + 1):
        cl = data.multivariate(PERIOD, kk).cluster
        agr_by_k[kk] = int((cl == "Agraris").sum())
    f["agr_by_k"] = agr_by_k

    # --- Babak III: pertumbuhan ----------------------------------------------
    s1, s2 = tot1.groupby(island).sum(), tot2.groupby(island).sum()
    ig = ((s2 / s1 - 1) * 100).sort_values(ascending=False)
    f["island_growth"] = [{"label": k, "value": float(v)} for k, v in ig.items()]
    f["jawa_growth"] = float(ig["Jawa"])
    sg = ((v2.sum() / v1.sum() - 1) * 100).sort_values(ascending=False)
    size = (v2.sum() / nat2 * 100)
    f["sector_growth"] = [{"label": SECTOR_SHORT[c], "value": float(v), "share": float(size[c])}
                          for c, v in sg.items()]
    f["largest_sectors"] = [SECTOR_SHORT[c].lower() for c in size.nlargest(2).index]
    f["fast_sectors_are_small"] = not set(sg.index[:3]) & set(size.nlargest(2).index)

    # --- Babak IV: pola yang mengakar ----------------------------------------
    mo = data.moran("Pangsa sektor", "A", PERIOD)
    quad = pd.Series(mo["quadrant"], index=mo["kode"])
    prov = reg.loc[quad.index, "provinsi"]
    f["moran"] = {"I": float(mo["I"]), "p": float(mo["p"]), "p_floor": 1 / (PERMUTATIONS + 1)}
    f["lisa"] = quad.to_dict()
    f["lisa_counts"] = quad.value_counts().to_dict()
    f["hh_prov"] = prov[quad == "Tinggi-Tinggi"].value_counts().head(3).index.tolist()
    f["ll_prov"] = prov[quad == "Rendah-Rendah"].value_counts().head(3).index.tolist()
    f["agri_share"] = shares["A"].to_dict()
    lq = data.lq(PERIOD)["B"].sort_values(ascending=False).head(3)
    f["mining"] = [{"label": region_label(reg, c), "lq": float(v)} for c, v in lq.items()]

    # Sensitivitas Moran's I terhadap jumlah tetangga.
    lat, lon = reg.loc[shares.index, "lat"].to_numpy(), reg.loc[shares.index, "lon"].to_numpy()
    x = shares["A"].to_numpy()
    f["moran_by_k"] = {kk: float(an.moran(x, an.knn_weights(lat, lon, kk), permutations=99)["I"])
                       for kk in (4, 5, 6, 7, 8)}

    # --- Hero ---------------------------------------------------------------
    f["names"] = {c: region_label(reg, c) for c in tot2.index}
    f["provinces"] = reg.loc[tot2.index, "provinsi"].to_dict()
    f["pdrb"] = tot2.to_dict()
    f["lat"] = reg.loc[tot2.index, "lat"].to_dict()
    f["lon"] = reg.loc[tot2.index, "lon"].to_dict()
    f["area"] = reg.loc[tot2.index, "luas_km2"].to_dict()
    return f
