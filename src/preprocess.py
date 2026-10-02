"""Membaca tabel BPS dan membentuk tabel turunan yang dipakai aplikasi.

Alur:
    Excel BPS (lebar, 17 sektor x 5 periode)  ->  to_long()
    long + kode wilayah                       ->  attach_regions()
    long                                      ->  wide_values() / shares() / lq()
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from config import PERIODS, SECTOR_CODES, TOTAL_LABEL

# Kode KBLI di depan nama kategori: "A", "M,N", "R,S,T,U".
# Harus diikuti spasi; tanpa syarat ini "Produk Domestik..." ikut terbaca
# sebagai kode "P" dan bertabrakan dengan Jasa Pendidikan.
_CODE_RE = re.compile(r"^([A-Z](?:,[A-Z])*)\s+(.+)$")


def split_category(label: str) -> tuple[str, str]:
    """'R,S,T,U Jasa Lainnya' -> ('R,S,T,U', 'Jasa Lainnya'); PDRB -> ('TOTAL', ...)."""
    label = str(label).strip()
    if label == TOTAL_LABEL:
        return "TOTAL", label
    match = _CODE_RE.match(label)
    if not match:
        raise ValueError(f"Kategori tidak dikenali: {label!r}")
    return match.group(1), match.group(2)


def to_long(path: str | Path) -> pd.DataFrame:
    """Ubah tabel lebar BPS menjadi format panjang (tidy).

    Tata letak berkas unduhan BPS:
        baris 2 : nama kategori (setiap 5 kolom)
        baris 3 : tahun
        baris 4 : Triwulan I .. IV, Tahunan
        baris 5+: satu baris per kabupaten/kota; '-' berarti belum tersedia
    """
    raw = pd.read_excel(path, header=None, dtype=object)

    blocks = []
    for col in range(1, raw.shape[1]):
        name = raw.iat[2, col]
        if pd.notna(name) and str(name).strip():
            blocks.append((col, str(name).strip()))

    records = []
    body = raw.iloc[5:].reset_index(drop=True)
    for start, label in blocks:
        code, name = split_category(label)
        year = int(str(raw.iat[3, start]).strip())
        for offset in range(5):
            period = str(raw.iat[4, start + offset]).strip()
            values = pd.to_numeric(body[start + offset], errors="coerce")
            records.append(pd.DataFrame({
                "kabkota": body[0].astype(str).str.strip(),
                "kode_sektor": code,
                "sektor": name,
                "tahun": year,
                "periode": period,
                "nilai": values,
            }))

    long = pd.concat(records, ignore_index=True)
    long = long[long["kabkota"].ne("") & long["kabkota"].ne("nan")]

    found = set(long["kode_sektor"]) - {"TOTAL"}
    if found != set(SECTOR_CODES):
        raise ValueError(f"Kode sektor tidak lengkap: {sorted(found)}")
    return long


def validate(long: pd.DataFrame) -> dict:
    """Pemeriksaan kualitas yang dicatat di README/makalah."""
    usable = long[long["periode"].isin(PERIODS)]
    sectors = usable[usable["kode_sektor"] != "TOTAL"]
    total = usable[usable["kode_sektor"] == "TOTAL"].set_index(["kabkota", "periode"])["nilai"]
    summed = sectors.groupby(["kabkota", "periode"])["nilai"].sum()
    gap = (summed - total).abs()
    return {
        "wilayah": usable["kabkota"].nunique(),
        "nilai_kosong_tw1_tw2": int(usable["nilai"].isna().sum()),
        "nilai_nol": int((sectors["nilai"] == 0).sum()),
        "selisih_maks_jumlah17_vs_total": float(gap.max()),
        "selisih_relatif_maks": float((gap / total).max()),
    }


def attach_regions(long: pd.DataFrame, regions: pd.DataFrame) -> pd.DataFrame:
    """Gabungkan kode wilayah. Nama kab/kota di tabel BPS unik, jadi aman sebagai kunci."""
    out = long.merge(
        regions[["kabkota", "kode", "provinsi", "pulau"]],
        on="kabkota", how="left", validate="many_to_one",
    )
    missing = out.loc[out["kode"].isna(), "kabkota"].unique()
    if len(missing):
        raise ValueError(f"Wilayah tanpa kode: {missing[:10]}")
    return out


# ---------------------------------------------------------------------------
# Tabel turunan
# ---------------------------------------------------------------------------

def wide_values(long: pd.DataFrame, period: str) -> pd.DataFrame:
    """Matriks wilayah (kode) x 17 sektor, miliar rupiah."""
    sub = long[(long["periode"] == period) & (long["kode_sektor"] != "TOTAL")]
    wide = sub.pivot(index="kode", columns="kode_sektor", values="nilai")
    return wide[SECTOR_CODES]


def shares(values: pd.DataFrame) -> pd.DataFrame:
    """Pangsa sektor (%) terhadap jumlah 17 sektor di wilayah yang sama.

    Penyebutnya jumlah 17 sektor, bukan baris PDRB, supaya setiap baris tepat
    berjumlah 100. Selisih keduanya karena pembulatan BPS, maksimal 0,02%.
    """
    return values.div(values.sum(axis=1), axis=0) * 100


def location_quotient(values: pd.DataFrame) -> pd.DataFrame:
    """LQ_ij = (x_ij / x_i.) / (X_.j / X_..).

    LQ > 1: sektor j lebih terkonsentrasi di wilayah i dibanding nasional
    (indikasi sektor basis). Rasio, sehingga sah untuk choropleth.
    """
    regional = values.div(values.sum(axis=1), axis=0)
    national = values.sum(axis=0) / values.to_numpy().sum()
    return regional.div(national, axis=1)


def growth_qtq(long: pd.DataFrame) -> pd.DataFrame:
    """Pertumbuhan TW II terhadap TW I (%), per wilayah x sektor (+ TOTAL).

    Catatan: q-to-q masih memuat pola musiman (mis. panen raya di TW I).
    """
    sub = long[long["periode"].isin(PERIODS)]
    wide = sub.pivot_table(index=["kode", "kode_sektor"], columns="periode", values="nilai")
    q1, q2 = wide["Triwulan I"], wide["Triwulan II"]
    rate = (q2 / q1.where(q1 > 0) - 1) * 100
    return rate.unstack("kode_sektor")


def concentration(values: pd.Series) -> pd.DataFrame:
    """Kurva Lorenz sederhana: wilayah diurutkan dari PDRB terbesar."""
    s = values.sort_values(ascending=False)
    return pd.DataFrame({
        "kode": s.index,
        "urutan": np.arange(1, len(s) + 1),
        "kumulatif_pct": s.cumsum().to_numpy() / s.sum() * 100,
    })
