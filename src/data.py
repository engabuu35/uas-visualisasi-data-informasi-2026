"""Pemuatan data ber-cache untuk Streamlit. Semua halaman mengambil data dari sini."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

import analysis as an
import preprocess as pp
import theme
from config import GEOJSON, N_CLUSTERS, PERMUTATIONS, PROCESSED_CSV, REGIONS_CSV, SPATIAL_K


@st.cache_data(show_spinner=False)
def long_df() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_CSV, dtype={"kode": str})


@st.cache_data(show_spinner=False)
def regions() -> pd.DataFrame:
    return pd.read_csv(REGIONS_CSV, dtype={"kode": str, "kode_prov": str}).set_index("kode")


@st.cache_data(show_spinner=False)
def geojson() -> dict:
    with GEOJSON.open(encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(show_spinner=False)
def values(period: str) -> pd.DataFrame:
    return pp.wide_values(long_df(), period)


@st.cache_data(show_spinner=False)
def shares(period: str) -> pd.DataFrame:
    return pp.shares(values(period))


@st.cache_data(show_spinner=False)
def lq(period: str) -> pd.DataFrame:
    return pp.location_quotient(values(period))


@st.cache_data(show_spinner=False)
def growth() -> pd.DataFrame:
    return pp.growth_qtq(long_df())


@st.cache_resource(show_spinner=False)
def multivariate(period: str, k: int = N_CLUSTERS) -> an.MultivariateResult:
    return an.run_multivariate(shares(period), k=k)


def cluster_colors(mv: an.MultivariateResult) -> dict:
    """Warna per NAMA klaster dari palet aktif (tidak di-cache: ikut tema)."""
    return an.cluster_colors(list(mv.cluster_profile.index), theme.tokens().cluster)


@st.cache_resource(show_spinner=False)
def weights(k: int = SPATIAL_K) -> np.ndarray:
    r = regions().loc[values("Triwulan II").index]
    return an.knn_weights(r["lat"].to_numpy(), r["lon"].to_numpy(), k=k)


@st.cache_data(show_spinner=False)
def moran(indicator: str, sector: str, period: str) -> dict:
    """Moran's I + LISA. Wilayah tanpa nilai (mis. pertumbuhan dari basis nol)
    dikeluarkan, lalu bobot tetangganya distandardisasi ulang."""
    v = indicator_values(indicator, sector, period)
    mask = v.notna().to_numpy()
    w = weights()[np.ix_(mask, mask)]
    rs = w.sum(axis=1, keepdims=True)
    w = np.divide(w, rs, out=np.zeros_like(w), where=rs > 0)
    out = an.moran(v[mask].to_numpy(), w, permutations=PERMUTATIONS)
    out["kode"] = list(v.index[mask])
    return out


@st.cache_data(show_spinner=False)
def jenks(indicator: str, sector: str, period: str, k: int) -> list[float]:
    return an.jenks_breaks(indicator_values(indicator, sector, period).to_numpy(), k)


@st.cache_data(show_spinner=False)
def hierarchy(period: str, order: str) -> pd.DataFrame:
    return an.build_hierarchy(long_df(), period, order)


INDICATORS = {
    "Pangsa sektor": "Porsi sektor dalam PDRB daerah (%)",
    "Location quotient": "LQ: konsentrasi sektor relatif terhadap nasional",
    "Pertumbuhan q-to-q": "Perubahan TW II terhadap TW I (%)",
}


def indicator_values(indicator: str, sector: str, period: str) -> pd.Series:
    """Satu nilai per wilayah, selalu berupa rasio (bukan angka absolut)."""
    if indicator == "Pangsa sektor":
        return shares(period)[sector]
    if indicator == "Location quotient":
        return lq(period)[sector]
    g = growth()
    return g[sector].reindex(values(period).index)


def sector_values(sector: str, period: str) -> pd.Series:
    """Nilai absolut (miliar Rp) untuk simbol proporsional."""
    v = values(period)
    return v.sum(axis=1) if sector == "TOTAL" else v[sector]



@st.cache_data(show_spinner=False)
def silhouettes(period: str, ks: tuple = (3, 4, 5, 6, 7, 8)) -> dict:
    """Silhouette Ward per k, dasar pemilihan jumlah klaster."""
    return an.silhouette_by_k(multivariate(period).z, ks)
