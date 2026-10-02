"""Grafik SVG buatan tangan untuk halaman Cerita.

Mengapa bukan Plotly di sini: SVG inline terbaca pembaca layar, tajam di
kerapatan piksel berapa pun, bisa dianimasikan dengan CSS saja, dan peta
kecil-kecil (small multiples) cukup memakai <use> ke satu definisi geometri.
Enam peta Plotly berarti enam salinan GeoJSON 1 MB di halaman yang sama.
Halaman Jelajah tetap memakai Plotly karena di sana interaksinya lebih kaya.

Semua fungsi menerima angka yang sudah dihitung di story.py; tidak ada
perhitungan statistik di sini.
"""

from __future__ import annotations

import math
from html import escape

import numpy as np
import streamlit as st
from shapely.geometry import shape

import data
from charts import idn, signed
from config import CONTEXT_GRAY, INK, INK_MUTED, INK_SOFT, LAND, LAND_EDGE, LISA_COLORS, RULE

# Bingkai peta: kotak batas Indonesia (derajat) diproyeksikan equirectangular.
# Di lintang khatulistiwa distorsinya diabaikan untuk peta ikhtisar.
LON0, LON1, LAT0, LAT1 = 94.6, 141.4, -11.2, 6.3
MAP_W = 1000
_SCALE = MAP_W / (LON1 - LON0)
MAP_H = round((LAT1 - LAT0) * _SCALE)
# Toleransi penyederhanaan untuk peta cerita (derajat). Peta kecil dan hero
# tidak butuh detail 1 km; 0,025 derajat memangkas ukuran path lebih dari separuh.
STORY_TOLERANCE = 0.025
SMALL_AREA_KM2 = 1500  # di bawah ini poligon < ~2 px pada peta kecil; diberi penanda titik


def _xy(lon, lat):
    return (lon - LON0) * _SCALE, (LAT1 - lat) * _SCALE


def _ring(coords) -> str:
    pts, last = [], None
    for lon, lat in coords:
        x, y = _xy(lon, lat)
        p = (round(x, 1), round(y, 1))
        if p != last:
            pts.append(p)
            last = p
    if len(pts) < 4:
        return ""
    return "M" + "L".join(f"{x:g} {y:g}" for x, y in pts) + "Z"


@st.cache_data(show_spinner=False)
def region_paths() -> dict[str, str]:
    out = {}
    for feat in data.geojson()["features"]:
        geom = shape(feat["geometry"]).simplify(STORY_TOLERANCE, preserve_topology=True)
        polys = getattr(geom, "geoms", [geom])
        d = "".join(_ring(p.exterior.coords) for p in polys if not p.is_empty)
        if not d:  # pulau sangat kecil hilang saat dibulatkan; pakai bentuk asli
            src = shape(feat["geometry"])
            d = "".join(_ring(p.exterior.coords) for p in getattr(src, "geoms", [src]))
        out[feat["properties"]["kode"]] = d
    return out


def map_defs() -> str:
    """Satu definisi geometri untuk semua peta di halaman (dirujuk via <use>)."""
    paths = region_paths()
    regions = "".join(f'<path id="ws-r{k}" d="{d}"/>' for k, d in paths.items())
    land = "".join(f'<use href="#ws-r{k}"/>' for k in paths)
    return (f'<svg class="ws-defs" aria-hidden="true" focusable="false" width="0" height="0">'
            f'<defs>{regions}<g id="ws-land">{land}</g></defs></svg>')


def _tip(*lines) -> str:
    return escape("\n".join(lines), quote=True)


def _land(fill=LAND, edge=LAND_EDGE, width=0.6) -> str:
    return f'<use href="#ws-land" fill="{fill}" stroke="{edge}" stroke-width="{width}"/>'


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

def hero_map(f: dict, regions_latlon: dict, color: str) -> str:
    """Daratan gelap dengan lingkaran PDRB (luas sebanding nilai). Gambar
    pembuka ini adalah datanya sendiri, bukan foto hiasan."""
    vals = f["pdrb"]
    vmax = max(vals.values())
    r_max = 30
    dots = []
    for k in sorted(vals, key=vals.get, reverse=True):  # kecil di atas besar
        lat, lon = regions_latlon[k]
        x, y = _xy(lon, lat)
        r = r_max * math.sqrt(vals[k] / vmax)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{max(r, 0.9):.2f}"/>')
    return (f'<svg viewBox="0 0 {MAP_W} {MAP_H}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">'
            f'{_land("#1B2128", "#262C33", 0.5)}'
            f'<g fill="{color}" fill-opacity="0.55" stroke="{color}" stroke-opacity="0.9" stroke-width="0.6">'
            f'{"".join(dots)}</g></svg>')


# ---------------------------------------------------------------------------
# Babak I: kurva konsentrasi
# ---------------------------------------------------------------------------

def concentration(f: dict, accent: str, compact: bool = False) -> str:
    """compact=True: varian ponsel. viewBox yang lebih sempit membuat teks
    12 px tetap sekitar 11 px di layar 360 px; versi lebar akan mengecil
    menjadi ~6 px dan tidak terbaca."""
    y = f["conc_y"]
    n = len(y)
    W, H, L, R, T, B = (360, 270, 40, 12, 14, 40) if compact else (640, 400, 52, 18, 18, 46)
    pw, ph = W - L - R, H - T - B
    X = lambda i: L + i / n * pw
    Y = lambda v: T + (1 - v / 100) * ph
    line = "M" + "L".join(f"{X(i + 1):.1f} {Y(v):.1f}" for i, v in enumerate(y))
    nh = f["n_half"]
    grid = "".join(
        f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="ws-grid"/>'
        f'<text x="{L - 8}" y="{Y(v) + 4:.1f}" class="ws-tick" text-anchor="end">{v}%</text>'
        for v in (0, 25, 50, 75, 100))
    xt = "".join(f'<text x="{X(v):.1f}" y="{H - B + 18}" class="ws-tick" text-anchor="middle">{v}</text>'
                 for v in range(0, n + 1, 100))
    aria = (f"Kurva konsentrasi PDRB {f['n_regions']} kabupaten/kota. Diurutkan dari terbesar, "
            f"{nh} daerah pertama sudah menghasilkan separuh PDRB, dan {f['top_n']} daerah teratas "
            f"{idn(f['top_share'])}%.")
    names = escape("|".join(f["conc_names"]), quote=True)
    ys = ",".join(f"{v:.2f}" for v in y)
    # Sudut label garis "merata" mengikuti kemiringan garis di layar.
    ang = -math.degrees(math.atan2(ph, pw))
    lx, ly = X(n * 0.68), Y(68) + (16 if compact else 22)
    fig_dy, note_dy = (24, 40) if compact else (30, 50)
    axis_x = "Kab/kota, urut dari PDRB terbesar" if compact else "Jumlah kab/kota, diurutkan dari PDRB terbesar"
    return f'''
<svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(aria)}" class="ws-xhair"
     data-x0="{L}" data-x1="{W - R}" data-y0="{T}" data-y1="{H - B}" data-ys="{ys}" data-names="{names}">
  {grid}{xt}
  <line x1="{X(0)}" y1="{Y(0)}" x2="{X(n)}" y2="{Y(100)}" stroke="{CONTEXT_GRAY}" stroke-width="1.5" stroke-dasharray="3 5"/>
  <text x="{lx:.1f}" y="{ly:.1f}" class="ws-note" text-anchor="middle" transform="rotate({ang:.1f} {lx:.1f} {ly:.1f})">seandainya merata</text>
  <path d="M{X(0)} {Y(50):.1f}H{X(nh):.1f}V{Y(0)}" fill="none" stroke="{INK_MUTED}" stroke-width="1" stroke-dasharray="4 4"/>
  <path d="{line}" pathLength="1" class="ws-draw" fill="none" stroke="{accent}" stroke-width="2.5" stroke-linejoin="round"/>
  <circle cx="{X(nh):.1f}" cy="{Y(50):.1f}" r="5" fill="{accent}" stroke="#0F1318" stroke-width="2"/>
  <text x="{X(nh) + 12:.1f}" y="{Y(50) + fig_dy:.1f}" class="ws-hero-fig"><tspan class="ws-count" data-to="{nh}">{nh}</tspan> daerah</text>
  <text x="{X(nh) + 12:.1f}" y="{Y(50) + note_dy:.1f}" class="ws-note">= separuh PDRB nasional</text>
  <text x="{L + pw / 2}" y="{H - 6}" class="ws-axis" text-anchor="middle">{axis_x}</text>
  <text x="11" y="{T + ph / 2}" class="ws-axis" text-anchor="middle" transform="rotate(-90 11 {T + ph / 2})">PDRB kumulatif</text>
  <line class="ws-xh-line" x1="0" x2="0" y1="{T}" y2="{H - B}"/>
  <circle class="ws-xh-dot" r="4.5" cx="0" cy="0" fill="{accent}"/>
  <rect x="{L}" y="{T}" width="{pw}" height="{ph}" fill="transparent" class="ws-xh-hit"/>
</svg>'''


# ---------------------------------------------------------------------------
# Babak II: dumbbell porsi daerah vs porsi PDRB
# ---------------------------------------------------------------------------

def dumbbell(f: dict, compact: bool = False) -> str:
    """Lebar: label di kiri. Ringkas (ponsel): label di atas setiap baris,
    supaya sumbu nilai memakai seluruh lebar layar."""
    rows = sorted(f["clusters"], key=lambda r: r["pct_pdrb"])
    if compact:
        W, L, R, T, rh = 360, 12, 16, 40, 54
    else:
        W, L, R, T, rh = 640, 196, 26, 40, 44
    H = T + rh * len(rows) + 40
    xmax = math.ceil(max(max(r["pct_regions"], r["pct_pdrb"]) for r in rows) / 10) * 10
    X = lambda v: L + v / xmax * (W - L - R)
    grid = "".join(
        f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{T - 8}" y2="{H - 34}" class="ws-grid"/>'
        f'<text x="{X(v):.1f}" y="{H - 16}" class="ws-tick" text-anchor="middle">{v}%</text>'
        for v in range(0, xmax + 1, 10))
    body = []
    for i, r in enumerate(rows):
        top = T + rh * i
        cy = top + (rh * 0.68 if compact else rh / 2)
        a, b = X(r["pct_regions"]), X(r["pct_pdrb"])
        tip = _tip(r["klaster"], f"{r['n']} daerah = {idn(r['pct_regions'])}% dari {f['n_regions']}",
                   f"menyumbang {idn(r['pct_pdrb'])}% PDRB")
        name = escape(r["klaster"])
        if compact:
            label = (f'<text x="{L}" y="{top + 15:.1f}" class="ws-label">{name}'
                     f'<tspan class="ws-sub" dx="6">{r["n"]} daerah</tspan></text>')
        else:
            label = (f'<text x="{L - 14}" y="{cy - 2:.1f}" class="ws-label" text-anchor="end">{name}</text>'
                     f'<text x="{L - 14}" y="{cy + 14:.1f}" class="ws-sub" text-anchor="end">{r["n"]} daerah</text>')
        color = r["color"]
        body.append(f"""
  <g class="ws-row" style="--i:{i}" data-tip="{tip}" tabindex="0">
    <rect x="0" y="{top:.1f}" width="{W}" height="{rh}" fill="transparent"/>
    {label}
    <line x1="{a:.1f}" x2="{b:.1f}" y1="{cy:.1f}" y2="{cy:.1f}" stroke="{RULE}" stroke-width="3" stroke-linecap="round"/>
    <circle cx="{b:.1f}" cy="{cy:.1f}" r="7.5" fill="{color}" stroke="#141A21" stroke-width="2"/>
    <circle cx="{a:.1f}" cy="{cy:.1f}" r="7" fill="none" stroke="{INK_SOFT}" stroke-width="2"/>
  </g>""")
    legend = (f'<g class="ws-legend"><circle cx="{L + 6}" cy="14" r="6" fill="#141A21" stroke="{INK_SOFT}" stroke-width="2"/>'
              f'<text x="{L + 18}" y="18" class="ws-sub">porsi jumlah daerah</text>'
              f'<circle cx="{L + 160}" cy="14" r="7" fill="{INK_SOFT}"/>'
              f'<text x="{L + 172}" y="18" class="ws-sub">porsi PDRB nasional</text></g>')
    aria = "Dumbbell per pola ekonomi: " + "; ".join(
        f"{r['klaster']}, {idn(r['pct_regions'])}% daerah dan {idn(r['pct_pdrb'])}% PDRB" for r in reversed(rows))
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(aria)}">'
            f'{legend}{grid}{"".join(body)}</svg>')


# ---------------------------------------------------------------------------
# Babak II: small multiples, satu peta per pola
# ---------------------------------------------------------------------------

def cluster_maps(f: dict) -> str:
    """Satu warna per peta. Enam warna dalam satu peta gagal uji pemisahan
    buta warna untuk semua pasangan; small multiples menghindari masalah itu
    sekaligus membuat sebaran setiap pola terbaca sendiri-sendiri."""
    by = {}
    for k, c in f["cluster_of"].items():
        by.setdefault(c, []).append(k)
    panels = []
    for i, r in enumerate(f["clusters"]):
        members = by.get(r["klaster"], [])
        uses = "".join(
            f'<use href="#ws-r{k}" data-tip="{_tip(f["names"][k], f["provinces"][k], r["klaster"])}"/>'
            for k in members)
        # Kota-kota kecil (mis. lima kota Jakarta) nyaris tak terlihat sebagai
        # poligon pada peta selebar ini; titik membuat keberadaannya terbaca.
        dots = "".join(
            '<circle cx="{:.1f}" cy="{:.1f}" r="7" data-tip="{}"/>'.format(
                *_xy(f["lon"][k], f["lat"][k]), _tip(f["names"][k], f["provinces"][k], r["klaster"]))
            for k in members if f["area"][k] < SMALL_AREA_KM2)
        aria = (f"Peta {r['klaster']}: {r['n']} daerah, terbanyak di {r['top_island']} "
                f"({r['top_island_n']} daerah).")
        panels.append(f'''
<div class="ws-mini" style="--i:{i}">
  <p class="ws-mini-t"><i style="background:{r["color"]}"></i>{escape(r["klaster"])} <span>{r["n"]}</span></p>
  <svg viewBox="0 0 {MAP_W} {MAP_H}" role="img" aria-label="{escape(aria)}">
    {_land()}<g fill="{r["color"]}" stroke="#0F1318" stroke-width="0.6">{uses}</g>
    <g fill="none" stroke="{r["color"]}" stroke-width="2.4">{dots}</g>
  </svg>
</div>''')
    return f'<div class="ws-minis">{"".join(panels)}</div>'


# ---------------------------------------------------------------------------
# Babak III: batang pertumbuhan
# ---------------------------------------------------------------------------

def growth_bars(rows: list[dict], reference: float, accent: str, ref_label: str,
                label_w: int = 150, row_h: int = 34, compact: bool = False) -> str:
    """Batang horizontal dari garis nol. Di atas acuan = aksen babak (makna:
    lebih cepat dari nasional), di bawah = abu konteks. Nilai di dalam batang
    bila batangnya cukup panjang (>= 55 px), di luar bila pendek."""
    if compact:  # label di atas batang, batang memakai seluruh lebar
        label_w, row_h = 12, max(row_h, 36)
    W, R, T = (360, 46, 30) if compact else (640, 54, 30)
    H = T + row_h * len(rows) + 28
    lo = min(0.0, min(r["value"] for r in rows))
    hi = max(r["value"] for r in rows)
    span = math.ceil(hi + 0.5) - math.floor(lo)
    X = lambda v: label_w + (v - math.floor(lo)) / span * (W - label_w - R)
    x0 = X(0)
    body = []
    for i, r in enumerate(rows):
        y = T + row_h * i
        v = r["value"]
        xa, xb = sorted((x0, X(v)))
        w = xb - xa
        fill = accent if v >= reference else CONTEXT_GRAY
        txt = signed(v) + "%"
        inside = w >= 55
        tx = (xb - 6 if inside else xb + 6) if v >= 0 else (xa + 6 if inside else xa - 6)
        anchor = ("end" if inside else "start") if v >= 0 else ("start" if inside else "end")
        tcls = ("ws-val-in" if fill == accent else "ws-val") if inside else "ws-val"
        extra = f" · {idn(r['share'])}% PDRB" if "share" in r else ""
        tip = _tip(r["label"], f"TW II vs TW I: {txt}" + extra)
        sign = "neg" if v < 0 else "pos"
        name = escape(r["label"])
        if compact:
            by, bh = y + 17, row_h - 21
            label = f'<text x="{label_w}" y="{y + 12}" class="ws-label">{name}</text>'
        else:
            by, bh = y + 6, row_h - 12
            label = (f'<text x="{label_w - 10}" y="{y + row_h / 2 + 4:.1f}" class="ws-label" '
                     f'text-anchor="end">{name}</text>')
        body.append(f'''
  <g class="ws-bar {sign}" style="--i:{i}" data-tip="{tip}" tabindex="0">
    {label}
    <rect x="{xa:.1f}" y="{by:.1f}" width="{max(w, 1):.1f}" height="{bh}" rx="4" fill="{fill}"/>
    <text x="{tx:.1f}" y="{by + bh / 2 + 4.5:.1f}" class="{tcls}" text-anchor="{anchor}">{txt}</text>
  </g>''')
    xr = X(reference)
    ref = (f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{T - 6}" y2="{H - 22}" stroke="{INK}" stroke-width="1" stroke-dasharray="3 4"/>'
           f'<text x="{xr:.1f}" y="{T - 12}" class="ws-note" text-anchor="middle">{escape(ref_label)} {signed(reference)}%</text>')
    aria = "Pertumbuhan TW II terhadap TW I: " + "; ".join(f"{r['label']} {signed(r['value'])}%" for r in rows)
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(aria)}">'
            f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="{T - 4}" y2="{H - 22}" stroke="{RULE}"/>'
            f'{"".join(body)}{ref}</svg>')


# ---------------------------------------------------------------------------
# Babak IV: peta LISA
# ---------------------------------------------------------------------------

def lisa_map(f: dict) -> str:
    uses = []
    for k, q in f["lisa"].items():
        tip = _tip(f["names"][k], f["provinces"][k], f"Pertanian: {idn(f['agri_share'][k])}% PDRB", q)
        uses.append(f'<use href="#ws-r{k}" fill="{LISA_COLORS[q]}" data-tip="{tip}"/>')
    c = f["lisa_counts"]
    aria = ("Peta LISA porsi pertanian. " + "; ".join(f"{q}: {c.get(q, 0)} daerah" for q in LISA_COLORS) + ".")
    return (f'<svg viewBox="0 0 {MAP_W} {MAP_H}" role="img" aria-label="{escape(aria)}">'
            f'{_land()}<g stroke="#0F1318" stroke-width="0.6">{"".join(uses)}</g></svg>')


def lisa_legend(f: dict) -> str:
    c = f["lisa_counts"]
    items = "".join(f'<span><i style="background:{col}"></i>{escape(q)} <em>{c.get(q, 0)}</em></span>'
                    for q, col in LISA_COLORS.items())
    return f'<div class="ws-swatches">{items}</div>'
