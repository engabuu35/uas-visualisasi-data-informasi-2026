"""Satu-satunya tempat warna didefinisikan: tema terang/gelap x palet standar/alternatif.

Kode lain tidak boleh menulis kode warna sendiri; ambil dari `tokens()`.

Streamlit tidak rerun saat tema diganti lewat menu. `sync()` membaca latar yang
sedang tampil, menulis `data-st-theme` di <html> (CSS berganti seketika), lalu memicu
satu rerun agar grafik Plotly dan SVG digambar ulang.

Palet kategorikal dan LISA diuji dengan simulasi buta warna Machado-Oliveira-Fernandes
(2009), dE OKLab x100 >= 8. Urutan slot bagian dari keamanannya; uji ulang bila diubah.
"""

from __future__ import annotations

from types import SimpleNamespace

import streamlit as st
from plotly.colors import sample_colorscale, sequential

MODES = ("light", "dark")
# Label ini tampil di panel Aksesibilitas; namanya mengikuti palet yang dipakai.
STANDARD, ALTERNATIVE = "Viridis (bawaan)", "Okabe-Ito / Cividis"
VARIANTS = (STANDARD, ALTERNATIVE)

# ---------------------------------------------------------------------------
# Kerangka (teks, latar, garis). Kontras teks diukur terhadap `paper`.
# ---------------------------------------------------------------------------
CHROME = {
    "light": dict(
        paper="#FBF7F0", surface="#FFFFFF", panel="#F3EDE2",
        ink="#1B1E22",      # 16,0:1
        soft="#474C54",     # 8,3:1
        muted="#626870",    # >= 4,7:1 di paper dan di semua tint babak (teks kecil)
        grid="#E7E4DE", rule="#C7C2B9", context="#B4AFA7", na="#D3CEC6",
        land="#E3E0D9", land_edge="#F7F5F0", hover_bg="#FFFFFF",
        on_accent="#FFFFFF",  # teks di atas batang aksen (>= 5:1)
        primary="#BC3E0B",    # oranye bata, >= 4,5:1 di paper dan panel
        accent="#BC3E0B", accent_deep="#7A3E0C",
        basemap="carto-voyager",
        veil_rgb="251,247,240",  # lapisan hero: terang di mode terang
        card_bg="rgba(255,255,255,.82)", chart_bg="rgba(255,255,255,.9)",
        hairline="rgba(27,30,34,.16)",
        seg_active="#F5D7BE",  # isi tombol/segmen terpilih (sama di semua halaman, tak ikut warna latar)
        shadow_pct="16%", shadow_rgb="27,30,34", shadow_a=".08",  # bayangan kartu: warna aksen babak + sedikit netral
    ),
    "dark": dict(
        paper="#0F1318", surface="#141A21", panel="#1A2029",
        ink="#E8E4DE",      # 14,7:1
        soft="#B5AEA6",     # 8,5:1
        muted="#8A847D",    # 5,0:1
        grid="#232A33", rule="#38404A", context="#4A4F57", na="#4A4F57",
        land="#20252A", land_edge="#2D3135", hover_bg="#0F1318",
        on_accent="#0F1318",
        primary="#C98500",
        accent="#C98500", accent_deep="#F4B175",
        basemap="carto-darkmatter",
        veil_rgb="0,0,0",
        card_bg="rgba(20,26,33,.74)", chart_bg="rgba(20,26,33,.78)",
        hairline="rgba(255,255,255,.1)",
        seg_active="#473818",
        shadow_pct="0%", shadow_rgb="0,0,0", shadow_a=".4",
    ),
}

# ---------------------------------------------------------------------------
# Kategorikal (klaster). Warna mengikuti NAMA klaster, bukan peringkatnya.
# ---------------------------------------------------------------------------
CATEGORICAL = {
    # Palet rujukan tervalidasi, langkah terang & gelap dari rona yang sama.
    # Pasangan bersebelahan: CVD terburuk dE 9,1 (terang) / 8,4 (gelap).
    STANDARD: {
        "light": ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300"],
        "dark": ["#3987E5", "#D95926", "#199E70", "#C98500", "#D55181", "#008300"],
    },
    # Okabe-Ito tanpa hitam & kuning; urutan terbaik dari 720 permutasi (dE terburuk 18).
    ALTERNATIVE: {
        "light": ["#009E73", "#0072B2", "#D55E00", "#56B4E9", "#E69F00", "#CC79A7"],
        "dark": ["#009E73", "#0072B2", "#D55E00", "#56B4E9", "#E69F00", "#CC79A7"],
    },
}
# Enam warna tidak semua pasangannya aman, jadi klaster selalu punya encoding kedua.
SYMBOLS = ["circle", "diamond", "square", "triangle-up", "cross", "x"]

# ---------------------------------------------------------------------------
# Sekuensial: Viridis / Cividis. Nilai tinggi selalu paling kontras dengan latar;
# ujung ekstrem dipangkas agar kelas terendah tidak lebur dengan latar.
# ---------------------------------------------------------------------------
_SEQ_SOURCE = {STANDARD: sequential.Viridis, ALTERNATIVE: sequential.Cividis}
_SEQ_RANGE = {"light": (0.92, 0.0), "dark": (0.12, 1.0)}

# Teks label treemap/icicle: hitam atau putih per kotak (menjamin >= 4,58:1).
LABEL_INK = ("#000000", "#FFFFFF")

# ---------------------------------------------------------------------------
# Divergen (LQ, pertumbuhan). neg = [ekstrem, tengah, dekat-tengah],
# pos = [dekat-tengah, tengah, ekstrem]. Tidak pernah merah-hijau.
# ---------------------------------------------------------------------------
DIVERGING = {
    STANDARD: {  # biru <-> jingga
        "light": dict(neg=["#1C5CAB", "#5598E7", "#B7D3F6"], mid="#EFEDE8", pos=["#F7C8A4", "#E8803F", "#A94E12"]),
        "dark": dict(neg=["#9EC5F4", "#3987E5", "#184F95"], mid="#44454A", pos=["#834018", "#D36C1B", "#EFB787"]),
    },
    ALTERNATIVE: {  # ColorBrewer RdBu: merah-biru aman untuk protan/deutan
        "light": dict(neg=["#2166AC", "#67A9CF", "#D1E5F0"], mid="#F7F7F7", pos=["#FDDBC7", "#EF8A62", "#B2182B"]),
        "dark": dict(neg=["#92C5DE", "#4393C3", "#1F4E72"], mid="#44454A", pos=["#7A2E2A", "#D6604D", "#F4A582"]),
    },
}

# ---------------------------------------------------------------------------
# LISA. dE terburuk (CVD) empat kelas bermakna: standar 20,1 / 15,0; alternatif 15,1 / 12,6.
# ---------------------------------------------------------------------------
_LISA_KEYS = ["Tinggi-Tinggi", "Rendah-Rendah", "Tinggi-Rendah", "Rendah-Tinggi", "Tidak signifikan"]
LISA = {
    STANDARD: {
        "light": ["#A94E12", "#1C5CAB", "#F4A05A", "#86B6EF", "#E6E1D9"],
        "dark": ["#D36C1B", "#3987E5", "#EFB787", "#9EC5F4", "#30353C"],
    },
    ALTERNATIVE: {
        "light": ["#B2182B", "#2166AC", "#EF8A62", "#67A9CF", "#E6E1D9"],
        "dark": ["#D6604D", "#4393C3", "#F4A582", "#92C5DE", "#30353C"],
    },
}

# ---------------------------------------------------------------------------
# Aksen babak cerita (tidak ikut varian palet). Kontras >= 4,6:1 (terang) / 4,8:1 (gelap).
# ---------------------------------------------------------------------------
ACT_COLORS = {
    "light": [("#8E5C09", "#FCE9D3"), ("#A84D27", "#FFE6DD"), ("#06775A", "#D9F2E8"), ("#3069B0", "#E3EDFF")],
    "dark": [("#C98500", "#15120D"), ("#D95926", "#17110F"), ("#199E70", "#0E1411"), ("#3987E5", "#0F1317")],
}


def _mix(fg: str, bg: str, p: float) -> str:
    """Campuran hex: p bagian fg di atas bg."""
    a, b = ([int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in (fg, bg))
    return "#" + "".join(f"{round(x * p + y * (1 - p)):02X}" for x, y in zip(a, b))


# Latar halaman Jelajah. Gelap: 8% aksen di atas paper (teks muted tetap >= 4,6:1).
PAGE_BG = {
    "light": [t for _, t in ACT_COLORS["light"]],
    "dark": [_mix(a, CHROME["dark"]["paper"], .08) for a, _ in ACT_COLORS["dark"]],
}


# ---------------------------------------------------------------------------
# Status aktif
# ---------------------------------------------------------------------------

def mode() -> str:
    m = st.session_state.get("_theme_mode")
    if m in MODES:
        return m
    ctx = getattr(getattr(st, "context", None), "theme", None)
    return ctx.type if ctx is not None and ctx.type in MODES else "light"


def variant() -> str:
    v = st.session_state.get("palette")
    return v if v in VARIANTS else STANDARD


def tokens(m: str | None = None, v: str | None = None) -> SimpleNamespace:
    m, v = m or mode(), v or variant()
    d = DIVERGING[v][m]
    lo, hi = _SEQ_RANGE[m]
    seq = sample_colorscale(_SEQ_SOURCE[v], [lo + (hi - lo) * i / 5 for i in range(6)], colortype="rgb")
    return SimpleNamespace(
        mode=m, variant=v, **CHROME[m],
        cluster=CATEGORICAL[v][m], symbols=SYMBOLS,
        seq=[_rgb_to_hex(c) for c in seq],
        div_neg=d["neg"], div_mid=d["mid"], div_pos=d["pos"],
        lisa=dict(zip(_LISA_KEYS, LISA[v][m])),
        acts=ACT_COLORS[m],
    )


def diverging_scale(t: SimpleNamespace | None = None) -> list:
    """Skala kontinu Plotly dengan titik tengah abu di 0,5."""
    t = t or tokens()
    n, p = t.div_neg, t.div_pos
    return [[0.0, n[0]], [0.2, n[1]], [0.4, n[2]], [0.5, t.div_mid],
            [0.6, p[0]], [0.8, p[1]], [1.0, p[2]]]


def _rgb_to_hex(c: str) -> str:
    r, g, b = (int(round(float(x))) for x in c[c.index("(") + 1:c.index(")")].split(","))
    return f"#{r:02X}{g:02X}{b:02X}"


def css_vars() -> str:
    """Token kerangka sebagai variabel CSS untuk kedua mode. Mode yang sedang
    diketahui Python menjadi bawaan; atribut data-st-theme (diisi sync())
    menimpanya seketika saat pengguna berganti tema."""
    def block(m):
        c = CHROME[m]
        acts = ACT_COLORS[m]
        items = {
            "tk-paper": c["paper"], "tk-surface": c["surface"], "tk-panel": c["panel"],
            "tk-ink": c["ink"], "tk-soft": c["soft"], "tk-muted": c["muted"],
            "tk-grid": c["grid"], "tk-rule": c["rule"], "tk-accent": c["accent"], "tk-accent-deep": c["accent_deep"],
            "tk-on-accent": c["on_accent"], "tk-veil-rgb": c["veil_rgb"],
            "tk-card-bg": c["card_bg"], "tk-chart-bg": c["chart_bg"], "tk-hairline": c["hairline"],
            "tk-tip-bg": c["hover_bg"], "tk-seg-active": c["seg_active"],
            "tk-shadow-pct": c["shadow_pct"], "tk-shadow-rgb": c["shadow_rgb"], "tk-shadow-a": c["shadow_a"],
            **{f"tk-act{i + 1}": a for i, (a, _) in enumerate(acts)},
            **{f"tk-tint{i + 1}": t for i, (_, t) in enumerate(acts)},
            **{f"tk-page{i + 1}": p for i, p in enumerate(PAGE_BG[m])},
            "tk-tint1-rgb": ",".join(str(int(acts[0][1][i:i + 2], 16)) for i in (1, 3, 5)),
        }
        return ";".join(f"--{k}:{v}" for k, v in items.items())
    m = mode()
    return (f":root{{{block(m)}}}"
            f':root[data-st-theme="light"]{{{block("light")}}}'
            f':root[data-st-theme="dark"]{{{block("dark")}}}')


# ---------------------------------------------------------------------------
# Sinkronisasi tema (lihat docstring modul)
# ---------------------------------------------------------------------------
_PROBE_JS = """
export default function (component) {
  const { setStateValue, data } = component;
  // Streamlit memasang lang="en"; isi aplikasi berbahasa Indonesia, jadi pembaca layar
  // perlu tahu bahasanya agar pelafalannya benar (WCAG 3.1.1).
  document.documentElement.lang = 'id';
  const read = () => {
    const app = document.querySelector('.stApp');
    if (!app) return null;
    const m = getComputedStyle(app).backgroundColor.match(/[0-9.]+/g);
    if (!m) return null;
    const [r, g, b] = m.map(Number);
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 128 ? 'dark' : 'light';
  };
  // Satu nilai "terakhir dikirim" untuk seluruh halaman. Komponen dipasang
  // ulang di setiap rerun; pembanding per-pemasangan memicu 4-5 rerun
  // berantai untuk satu kali ganti tema.
  if (window.__stThemeSent === undefined) window.__stThemeSent = data;
  const tick = () => {
    const t = read();
    if (!t) return;
    document.documentElement.dataset.stTheme = t;
    if (t !== window.__stThemeSent) { window.__stThemeSent = t; setStateValue('mode', t); }
  };
  tick();
  const id = setInterval(tick, 400);
  return () => clearInterval(id);
}
"""
_probe = st.components.v2.component("theme_probe", js=_PROBE_JS)


def sync() -> str:
    """Pasang pembaca tema. Dipanggil di dalam panel Aksesibilitas yang posisinya tetap (fixed),
    jadi tidak memakan ruang halaman."""
    guess = mode()
    res = _probe(key="theme_probe", data=guess, default={"mode": None}, on_mode_change=lambda: None)
    m = res.mode if res.mode in MODES else guess
    st.session_state["_theme_mode"] = m
    return m
