"""Pra-pemrosesan: jalankan sekali sebelum `streamlit run app.py`.

    python scripts/prepare_data.py

Masukan
    data/raw/pdrb_2026.xlsx      unduhan tabel BPS (format lebar)
    data/geo/kabkota.geojson     batas kab/kota, kode wilayah BPS 2019
Keluaran (data/processed/)
    pdrb_long.csv                tidy, hanya TW I dan TW II yang terisi
    wilayah.csv                  kode, nama, provinsi, pulau, titik pusat
    kabkota_simplified.geojson   geometri disederhanakan (~1,5 MB) untuk web
"""

from pathlib import Path
import json
import sys

import pandas as pd
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from config import (  # noqa: E402
    GEOJSON, PERIODS, PROCESSED_CSV, PROVINCES, RAW_GEOJSON, RAW_XLSX, REGIONS_CSV,
)
from preprocess import attach_regions, to_long, validate  # noqa: E402

# Toleransi Douglas-Peucker dalam derajat (~0,01 derajat = 1,1 km di ekuator).
# Cukup untuk tampilan nasional dan provinsi; garis pantai tetap terbaca.
SIMPLIFY_TOLERANCE = 0.01
COORD_DECIMALS = 3


def _round_coords(obj, nd=COORD_DECIMALS):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(v, nd) for v in obj]
        return [_round_coords(o, nd) for o in obj]
    return obj


def build_regions_and_geometry():
    with RAW_GEOJSON.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    rows, features = [], []
    for feat in raw["features"]:
        p = feat["properties"]
        kode = str(p["kode_wilayah"])
        prov_name, island = PROVINCES[kode[:2]]
        geom = shape(feat["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        point = geom.representative_point()  # selalu di dalam poligon
        rows.append({
            "kode": kode,
            "kabkota": p["kabupaten_kota"],
            "kode_prov": kode[:2],
            "provinsi": prov_name,
            "pulau": island,
            "jenis": "Kota" if p["kabupaten_kota"].startswith("Kota ") else "Kabupaten",
            "lat": round(point.y, 4),
            "lon": round(point.x, 4),
            "luas_km2": round(_area_km2(geom), 1),
        })
        simple = geom.simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)
        if simple.is_empty:  # pulau kecil bisa hilang; pertahankan aslinya
            simple = geom
        features.append({
            "type": "Feature",
            "id": kode,
            "properties": {"kode": kode, "kabkota": p["kabupaten_kota"]},
            "geometry": {
                "type": simple.geom_type,
                "coordinates": _round_coords(mapping(simple)["coordinates"]),
            },
        })

    regions = pd.DataFrame(rows).sort_values("kode").reset_index(drop=True)
    if regions["kabkota"].duplicated().any():
        raise ValueError("Nama kab/kota ganda di GeoJSON; join berbasis nama tidak aman.")
    return regions, {"type": "FeatureCollection", "features": features}


def _area_km2(geom):
    """Luas pendekatan: proyeksi equal-area sederhana (cos lintang)."""
    from math import cos, radians
    from shapely.ops import transform

    lat0 = geom.representative_point().y
    k = 111.32
    projected = transform(lambda x, y, z=None: (x * k * cos(radians(lat0)), y * k), geom)
    return projected.area


def main():
    long = to_long(RAW_XLSX)
    long = long[long["periode"].isin(PERIODS)]

    regions, geo = build_regions_and_geometry()
    long = attach_regions(long, regions)

    report = validate(long)

    PROCESSED_CSV.parent.mkdir(parents=True, exist_ok=True)
    long.to_csv(PROCESSED_CSV, index=False)
    regions.to_csv(REGIONS_CSV, index=False)
    with GEOJSON.open("w", encoding="utf-8") as fh:
        json.dump(geo, fh, separators=(",", ":"))

    print(f"pdrb_long.csv      : {len(long):,} baris")
    print(f"wilayah.csv        : {len(regions)} kab/kota, {regions['provinsi'].nunique()} provinsi")
    print(f"GeoJSON sederhana  : {GEOJSON.stat().st_size / 1e6:.1f} MB")
    for key, val in report.items():
        print(f"  {key:34s}: {val}")


if __name__ == "__main__":
    main()
