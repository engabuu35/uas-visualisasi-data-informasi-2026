"""Halaman Cerita: scrollytelling empat babak (tangkai 'martini glass').

    I   Konsentrasi PDRB ekonomi besar yang bertumpu pada sedikit tempat
    II  Pola Ekonomi   banyak daerahnya, kecil porsinya
    III Pertumbuhan     yang tumbuh paling cepat ada di luar pusat
    IV  Pergeseran  pertumbuhan lebih cepat belum menutup jarak

Setiap angka di teks diambil dari story.figures(); halaman ini hanya
merangkai kalimat. Kalimat yang bergantung pada peringkat (siapa tercepat,
siapa paling lambat) dibentuk dari data, bukan dari asumsi penulis.
"""

import json
import re
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st

import data
import story
import theme
import story_svg as sv
from charts import idn, signed
from config import (
    ACCESS_DATE, ACTS, BPS_SOURCE_URL, GEO_SOURCE, GEO_SOURCE_URL, N_CLUSTERS, SOURCE_CITE,
)
from story import join_id, word

ASSETS = Path(__file__).resolve().parents[1] / "assets"
f = story.figures()
reg = data.regions()
TK = theme.tokens()
# Babak ke-i memakai --tk-act{i}/--tk-tint{i} di CSS (berganti seketika saat tema
# berubah) dan hex aksennya untuk atribut SVG (digambar ulang lewat rerun).
A = {a["key"]: dict(a, i=i + 1, accent=TK.acts[i][0]) for i, a in enumerate(ACTS)}
# Warna klaster bergantung pada tema & palet, jadi ditempel di sini, bukan di cache.
_cmap = data.cluster_colors(data.multivariate(story.PERIOD))
f["clusters"] = [dict(r, color=_cmap[r["klaster"]]) for r in f["clusters"]]


# Sanitizer HTML Streamlit membuang semua elemen <svg>, tetapi skrip tetap
# berjalan. Maka markup SVG dikirim sebagai data di dalam skrip dan disisipkan
# ke slot-slotnya di sisi klien (lihat awal story.js).
SLOTS: dict[str, str] = {}


def slot(markup: str, cls: str = "ws-svg") -> str:
    key = f"s{len(SLOTS)}"
    SLOTS[key] = markup
    return f'<div class="{cls}" data-slot="{key}"></div>'


def pct(v, nd=1):
    return f"{idn(v, nd)}%"


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def rate(r):
    """'konstruksi (+5,4%)'"""
    return f"{r['label'].lower()} ({signed(r['value'])}%)"


def trillion(v):
    return f"Rp{idn(v / 1000, 0)} triliun"


def source(extra=""):
    tail = f" {extra[:1].upper()}{extra[1:]}." if extra else ""
    # Versi pendek untuk ponsel: grafik yang tersemat tidak boleh habis dimakan
    # catatan sumber. Rincian lengkapnya tetap ada di bagian metode.
    return (f'<p class="ws-src ws-only-desk">Sumber: BPS (<a href="{BPS_SOURCE_URL}" target="_blank" '
            f'rel="noopener">{SOURCE_CITE}</a>), diolah {ACCESS_DATE}.{tail}</p>'
            f'<p class="ws-src ws-only-mob">Sumber: BPS, PDRB Triwulanan ADHK 2010 kab/kota {f["year"]}, '
            f'diolah {ACCESS_DATE}.</p>')


def card(title, *paras, icon=None, stat=None, stat_label=None, caveat=False):
    """Pita kepala (ikon + judul), angka utama opsional, lalu paragraf.
    `stat` hanya untuk kartu yang judulnya memang memuat SATU angka utama;
    judulnya lalu dipendekkan menjadi label dan angkanya tampil besar."""
    ico = slot(sv.ICONS[icon], "ws-ico") if icon else ""
    num = ""
    if stat is not None:
        lab = f'<span class="ws-card-stat-l">{stat_label}</span>' if stat_label else ""
        num = f'<div class="ws-card-stat"><span class="ws-card-stat-v">{stat}</span>{lab}</div>'
    body = "".join(f"<p>{p}</p>" for p in paras)
    cls = "ws-card ws-caveat" if caveat else "ws-card"
    return (f'<article class="{cls}"><header class="ws-card-h">{ico}<h3>{title}</h3></header>'
            f'{num}{body}</article>')


def chart(title, sub, svg, src_extra="", after="", svg_mobile=None):
    svgs = (slot(svg, "ws-svg ws-only-desk") + slot(svg_mobile, "ws-svg ws-only-mob")
            if svg_mobile else slot(svg))
    return (f'<figure class="ws-chart"><p class="ws-chart-t" title="{escape(title)}">{title}</p>'
            f'<p class="ws-chart-s">{sub}</p>'
            f'{svgs}{after}{source(src_extra)}</figure>')


def scene(cards, fig, half_rem, tall=False, nudge=0):
    # Kotak sticky diletakkan di tengah layar: top = max(ruang header, 50svh - setengah tinggi konten).
    # tall=True: grafik terlalu tinggi untuk disematkan di ponsel; di sana ia ikut mengalir.
    top = f"max(4.75rem, calc(50svh - {half_rem}rem))"
    cls = "ws-scene ws-scene-tall" if tall else "ws-scene"
    return (f'<div class="{cls}" data-nudge="{nudge}"><div class="ws-cards">{"".join(cards)}</div>'
            f'<div class="ws-stage" style="--stick-top:{top}">{fig}</div></div>')


def act(key, title, dek, *scenes):
    a = A[key]
    return (f'<section class="ws-act" id="ws-{key}" '
            f'style="--accent:var(--tk-act{a["i"]});--tint:var(--tk-tint{a["i"]})" aria-labelledby="ws-h-{key}">'
            f'<header class="ws-act-head"><p class="ws-kicker">Babak {a["roman"]} · {a["label"]}</p>'
            f'<h2 class="ws-h2" id="ws-h-{key}">{title}</h2><p class="ws-act-dek">{dek}</p></header>'
            f'{"".join(scenes)}</section>')


n = f["n_regions"]
T = trillion(f["national"])

# =============================================================================
# Hero
# =============================================================================
latlon = {k: (f["lat"][k], f["lon"][k]) for k in f["pdrb"]}
stats = [
    (pct(f["jawa_share"]), "PDRB berasal dari Pulau Jawa"),
    (f"{f['n_half']} dari {n}", "daerah menghasilkan separuh PDRB"),
    (pct(f["dki_share"]), f"disumbang {word(f['dki_n'])} wilayah DKI Jakarta"),
    (f"{signed(f['growth'])}%", f"PDRB {f['period']} dibanding {f['prev']}"),
]
stats_html = "".join(f'<div class="ws-stat"><b>{v}</b><span>{escape(k)}</span></div>' for v, k in stats)
hero = f'''
<section class="ws-hero" aria-label="Pembuka">
  {slot(sv.hero_map(f, latlon, A["pusat"]["accent"]), "ws-hero-img")}
  <div class="ws-hero-l1"></div><div class="ws-hero-l2"></div><div class="ws-hero-l3"></div>
  <div class="ws-hero-copy" style="--accent:var(--tk-act1)">
    <p class="ws-kicker">PDRB harga konstan 2010 · {f["period"]} {f["year"]}</p>
    <h1 class="ws-title">Satu negeri, {n} wajah ekonomi</h1>
    <p class="ws-dek">Dalam satu triwulan, kabupaten dan kota di Indonesia menghasilkan nilai tambah sebesar
      <b>{T}</b>. Angka ini terlihat sangat besar jika dilihat secara nasional. Tapi ketika kita melihat
      lebih dekat ke setiap daerah, ceritanya mulai berbeda. Nilai tersebut tidak tersebar merata. Ada daerah
      yang menyumbang dalam jumlah besar, sementara daerah lainnya menggerakkan ekonominya dari sektor yang
      berbeda.</p>
    <div class="ws-stats">{stats_html}</div>
  </div>
</section>'''

jawa_rp = round(f["jawa_share"])
# Kalimat bergantung data: jangan menulis "lebih dari" bila angkanya tidak mendukung.
top_phrase = ("lebih dari seperempat" if f["top_share"] > 25
              else "hampir seperempat" if f["top_share"] > 20 else pct(f["top_share"]))

# =============================================================================
# Babak I · Pusat
# =============================================================================
act1 = act(
    "pusat", f"Separuh ekonomi terkonsentrasi di {f['n_half']} daerah",
    "Angka nasional terlihat kokoh, tetapi bertumpu hanya pada segelintir kabupaten/kota.",
    scene([
        card("Nilai tambah PDRB",
             f"Angka tersebut merupakan total nilai tambah yang dihasilkan {n} kabupaten/kota di Indonesia "
             f"pada {f['period']} {f['year']}, dihitung berdasarkan harga konstan 2010. Selama ini, angka "
             f"seperti ini biasanya dibaca sebagai gambaran satu perekonomian Indonesia.",
             "Tapi, apa yang terjadi kalau angka tersebut dilihat lebih dekat, dari satu daerah ke daerah lainnya?",
             icon="uang", stat=T, stat_label="dalam satu triwulan"),
        card("Penyumbang Separuh PDRB",
             f"Ketika seluruh daerah diurutkan berdasarkan PDRB dari yang terbesar, separuh nilai PDRB "
             f"terkumpul hanya pada {f['n_half']} daerah, sementara {n - f['n_half']} daerah lainnya "
             f"berbagi separuh sisanya.",
             icon="separuh", stat=f["n_half"], stat_label=f"dari {n} daerah"),
        card(f"{cap(word(f['top_n']))} Penyumbang Teratas",
             f"Hanya {word(f['top_n'])} daerah yang menyumbang {top_phrase} total PDRB. "
             f"{cap(word(f['top_dki_n']))} di antaranya merupakan kota administrasi di Jakarta, disusul "
             f"{join_id(f['top_rest'])}.",
             icon="peringkat", stat=pct(f["top_share"]), stat_label="dari total PDRB kabupaten/kota"),
        card("Pulau Jawa",
             f"{cap(word(f['jawa_provinces']))} provinsi di Jawa menyumbang {pct(f['jawa_share'])} "
             f"dari total PDRB kabupaten/kota Indonesia. Artinya, dari setiap Rp100 nilai tambah yang "
             f"dihasilkan {n} kabupaten/kota pada {f['period']} {f['year']}, sekitar Rp{jawa_rp} dihasilkan "
             f"di {word(f['jawa_provinces'])} provinsi di Pulau Jawa. Sisanya, sekitar Rp{100 - jawa_rp}, "
             f"dihasilkan oleh semua daerah di luar Jawa. Konsentrasi ini menunjukkan besarnya peran Jawa "
             f"dalam perekonomian daerah.",
             icon="lokasi", stat=pct(f["jawa_share"]), stat_label="dari total PDRB kabupaten/kota"),
    ], chart("Kurva konsentrasi PDRB",
             "Kurva menunjukkan konsentrasi PDRB ketika daerah diurutkan dari kontribusi terbesar ke "
             "terkecil. Garis putus-putus menunjukkan kondisi ketika setiap daerah menyumbang dengan "
             "nilai yang sama besar.",
             sv.concentration(f, A["pusat"]["accent"]),
             svg_mobile=sv.concentration(f, A["pusat"]["accent"], compact=True)), 17, nudge=36),
)

# =============================================================================
# Babak II · Pola Ekonomi
# =============================================================================
agr, korp, gov = f["agr"], f["korp"], f["gov"]


def kab(label):
    """Nama lengkap untuk teks naratif ('Kab.' hanya untuk label grafik yang sempit)."""
    return escape(label).replace("Kab. ", "Kabupaten ")


# Basis Pertanian
if agr["pct_pdrb"] < agr["pct_regions"] / 2:
    share_lead = ("Hampir separuh" if 45 <= agr["pct_regions"] < 50 else
                  "Lebih dari separuh" if agr["pct_regions"] >= 50 else pct(agr["pct_regions"]))
    agr_text = (f"{share_lead} kabupaten/kota memiliki pola ekonomi yang bertumpu pada pertanian. "
                f"Namun, {agr['n']} daerah tersebut hanya menyumbang {pct(agr['pct_pdrb'])} dari total PDRB.")
else:
    agr_text = (f"{pct(agr['pct_regions'])} kabupaten/kota memiliki pola ekonomi yang bertumpu pada "
                f"pertanian, dan menyumbang {pct(agr['pct_pdrb'])} dari total PDRB.")

# Basis Jasa Perusahaan
korp_lines = [f"Hanya {korp['n']} daerah yang masuk pola ini, tetapi kontribusinya mencapai "
              f"{pct(korp['pct_pdrb'])} dari total PDRB. {cap(word(korp['n_dki']))} di antaranya adalah "
              f"kota administrasi di Jakarta"
              + (f", ditambah {join_id([kab(x) for x in korp['others']])}." if korp["others"] else ".")]
if korp["small"]:
    mn_lo, mn_hi = min(korp["small_mn"]), max(korp["small_mn"])
    ratio = (sum(korp["small_mn"]) / len(korp["small_mn"])) / korp["median_mn"]
    mn_txt = pct(mn_lo) if pct(mn_lo) == pct(mn_hi) else f"{idn(mn_lo)}–{pct(mn_hi)}"
    both = "Keduanya memiliki" if len(korp["small"]) == 2 else "Semuanya memiliki"
    korp_lines[0] += (
        f" Menariknya, {join_id([kab(x) for x in korp['small']])} juga masuk pola ini, meski "
        f"masing-masing berada di peringkat {join_id([str(r) for r in korp['small_rank']])} berdasarkan "
        f"total PDRB. {both} porsi jasa perusahaan sebesar {mn_txt}, sekitar {idn(ratio, 0)} kali median "
        f"seluruh daerah ({pct(korp['median_mn'], 2)}). Yang menentukan bukan seberapa besar PDRB sebuah "
        f"daerah, tetapi seberapa besar peran jasa perusahaan dalam susunan ekonominya.")

# Basis Sektor Publik
gov_lines = [f"Sebanyak {gov['n_papua']} dari {gov['n']} daerah dalam pola ini berada di Papua dan Papua "
             f"Barat. Di daerah-daerah tersebut, {join_id(gov['top_sectors'])} menjadi bagian yang paling "
             f"menonjol dalam susunan ekonominya."]
for r in gov["non_papua"]:
    ikn = ", lokasi pembangunan Ibu Kota Nusantara" if r["name"] == "Penajam Paser Utara" else ""
    top = ", menjadi yang tertinggi di Indonesia" if r["is_national_max"] else ""
    gov_lines[0] += (f" Satu-satunya daerah di luar Papua adalah {kab(r['label'])}{ikn}. Di sana, "
                     f"{pct(r['share'])} ekonominya berasal dari sektor {r['sector']}{top}.")

# Sebaran pola menurut pulau: pola yang puncaknya di pulau sama digabung dalam satu kalimat.
where = [c for c in f["clusters"] if c["klaster"] not in ("Basis Jasa Perusahaan", "Basis Sektor Publik")]
groups = {}
for c in where:
    groups.setdefault(c["top_island"], []).append(c)
sentences = []
for gi, (island, cs) in enumerate(groups.items()):
    names = join_id([c["klaster"].lower().replace("&", "&amp;") for c in cs])
    counts = join_id([f"{c['top_island_n']} dari {c['n']} daerah" for c in cs])
    each = "masing-masing " if len(cs) > 1 else ""
    if gi == 0:
        sentences.append(f"{cap(names)} paling banyak ditemukan di {island}, dengan {each}{counts}.")
    elif gi == len(groups) - 1 and len(cs) == 1:
        sentences.append(f"Untuk {names}, konsentrasi terbesar berada di {island}, dengan {counts}.")
    else:
        sentences.append(f"Sementara itu, {names} paling banyak berada di {island}, {each}{counts}.")
where_text = " ".join(sentences)

act2 = act(
    "jurang", "PDRB sama, sumbernya berbeda",
    "Besarnya PDRB belum menunjukkan bagaimana ekonomi sebuah daerah terbentuk. Dua daerah bisa punya "
    "nilai PDRB yang hampir sama, tetapi sumber utamanya berbeda: satu bertumpu pada pertanian, sementara "
    "yang lain mengandalkan pertambangan, jasa, atau sektor publik. Di babak ini, kita melihat "
    f"&ldquo;apa yang ada di balik angka PDRB&rdquo; melalui {word(f['n_clusters'])} pola ekonomi daerah.",
    scene([
        card(f"{cap(word(f['n_clusters']))} pola ekonomi",
             f"Setiap daerah dibandingkan berdasarkan komposisi {f['n_sectors']} lapangan usahanya, bukan "
             f"besar kecilnya nilai PDRB. Jadi, yang dilihat adalah susunan ekonomi masing-masing daerah. "
             f"Dari kemiripan susunan tersebut, terbentuk {word(f['n_clusters'])} pola ekonomi.",
             icon="pola"),
        card(f"Basis Pertanian: {agr['n']} daerah, {pct(agr['pct_pdrb'])} PDRB", agr_text, icon="tani"),
        card(f"Basis Jasa Perusahaan: {korp['n']} daerah, {pct(korp['pct_pdrb'])} PDRB", *korp_lines,
             icon="gedung"),
    ], chart("Jumlah daerah vs. kontribusi PDRB",
             "Titik kosong menunjukkan persentase jumlah daerah dalam tiap pola, sedangkan titik berwarna "
             "menunjukkan kontribusinya terhadap total PDRB. Dari sini terlihat bahwa pola yang dimiliki "
             "banyak daerah belum tentu memberikan kontribusi PDRB yang besar.",
             sv.dumbbell(f), f"klaster Ward pada pangsa sektor terstandardisasi, k = {N_CLUSTERS}",
             svg_mobile=sv.dumbbell(f, compact=True)), 15, tall=True, nudge=36),
    scene([
        card(f"Basis Sektor Publik: {gov['n']} daerah, {pct(gov['pct_pdrb'])} PDRB", *gov_lines,
             icon="pemerintah"),
        card("Setiap pola punya wilayahnya",
             f"Setiap pola ekonomi cenderung terkumpul di wilayah tertentu. {where_text}", icon="peta"),
    ], chart("Di mana setiap pola berada",
             "Setiap peta menunjukkan daerah yang termasuk ke dalam satu pola ekonomi. Lingkaran menandai "
             "daerah yang terlalu kecil untuk terlihat pada skala peta, sementara angka di samping "
             "menunjukkan jumlah daerah dalam pola tersebut.",
             sv.cluster_maps(f), f"batas wilayah: {GEO_SOURCE}"), 18, tall=True),
)

# =============================================================================
# Babak III · Pertumbuhan
# =============================================================================
ig = f["island_growth"]
fast1, fast2, slowest = ig[0], ig[1], ig[-1]
jawa = f["jawa_growth"]
outside_leads = fast1["label"] != "Jawa"
sg = f["sector_growth"]
s_fast, s_slow = sg[:3], sg[-2:]
largest = [r for r in sg if r["label"].lower() in f["largest_sectors"]]


def sektor(label):
    """Nama sektor untuk kalimat: huruf kecil, '&' ditulis 'dan', singkatan dilengkapi."""
    full = {"keuangan": "jasa keuangan dan asuransi"}
    low = label.lower().replace("&", "dan")
    return full.get(low, low)


v1, v2 = fast1["value"], fast2["value"]
times = ("lebih dari dua kali" if min(v1, v2) / jawa >= 2 else f"sekitar {idn((v1 + v2) / 2 / jawa, 1)} kali")
if slowest["label"] == "Jawa":
    slow_text = f"Jawa tumbuh paling lambat ({pct(jawa)})."
else:
    same = idn(slowest["value"]) == idn(jawa)
    rel = (", sama dengan Jawa" if same else f", di bawah Jawa ({pct(jawa)})" if slowest["value"] < jawa else "")
    slow_text = (f"{slowest['label']} tumbuh {pct(slowest['value'])}{rel}. Di tengah pertumbuhan yang "
                 f"lebih cepat di beberapa wilayah lain, kawasan ini justru bergerak lebih lambat. Jadi, "
                 f"berada di luar Jawa tidak otomatis berarti pertumbuhan ekonomi yang lebih tinggi.")

sector_text = (f"{cap(sektor(s_fast[0]['label']))} tumbuh paling cepat sebesar {pct(s_fast[0]['value'])}, disusul "
               + join_id([f"{sektor(r['label'])} {pct(r['value'])}" for r in s_fast[1:]]) + ".")
if all(r["value"] < f["growth"] for r in largest):
    sector_text += (f" Sementara itu, {join_id([sektor(r['label']) for r in largest])} yang menjadi "
                    f"{word(len(largest))} sektor terbesar justru tumbuh lebih lambat, masing-masing "
                    f"{join_id([pct(r['value']) for r in largest])}, di bawah laju nasional.")

slow_both = max(r["value"] for r in s_slow) < 1
act3 = act(
    "arus", "Pertumbuhan lebih cepat muncul di luar pusat" if outside_leads else "Pusat tetap tumbuh paling cepat",
    f"Dibanding {f['prev']}, total PDRB kabupaten/kota tumbuh {pct(f['growth'])}. Tetapi di balik angka itu, "
    f"laju pertumbuhan antarwilayah cukup berbeda."
    + (" Sejumlah daerah di luar pusat ekonomi justru mencatat kenaikan yang lebih cepat." if outside_leads else ""),
    scene([
        card("Pertumbuhan nasional",
             f"Secara keseluruhan, PDRB {n} kabupaten/kota tumbuh {pct(f['growth'])} dari {f['prev']} ke "
             f"{f['period']} {f['year']}. Angka ini menjadi garis pembanding pada grafik untuk melihat daerah "
             f"mana yang tumbuh lebih cepat atau lebih lambat.",
             icon="grafik", stat=f"{signed(f['growth'])}%", stat_label="dalam satu triwulan"),
        card(f"{fast1['label']} dan {fast2['label']}",
             f"Pertumbuhan paling cepat datang dari {fast1['label']} dan {fast2['label']}. Masing-masing tumbuh "
             f"{pct(v1)} dan {pct(v2)}, {times} laju pertumbuhan Jawa yang berada di {pct(jawa)}.",
             icon="naik"),
        card(f"Paling lambat: {slowest['label']}", slow_text, icon="turun"),
    ], chart("Pertumbuhan per pulau",
             f"{f['period']} dibanding {f['prev']} {f['year']}. Warna menunjukkan pertumbuhan di atas laju "
             f"nasional, sedangkan abu-abu menunjukkan pertumbuhan di bawahnya.",
             sv.growth_bars(ig, f["growth"], A["arus"]["accent"], "nasional", label_w=150, row_h=40),
             "dihitung dari jumlah nilai seluruh kab/kota di pulau tersebut",
             svg_mobile=sv.growth_bars(ig, f["growth"], A["arus"]["accent"], "nasional", compact=True)), 13),
    scene([
        card("Terbesar bukan tercepat" if f["fast_sectors_are_small"] else "Sektor tercepat", sector_text,
             icon="sektor"),
        card("Nyaris tak bergerak" if slow_both else "Paling lambat",
             f"{cap(sektor(s_slow[0]['label']))} hanya tumbuh {pct(s_slow[0]['value'])}, sementara "
             f"{sektor(s_slow[1]['label'])} tumbuh {pct(s_slow[1]['value'])}. Keduanya berada jauh di bawah "
             f"pertumbuhan nasional sebesar {pct(f['growth'])}, menunjukkan bahwa tidak semua sektor ikut "
             f"bergerak dengan kecepatan yang sama.",
             icon="datar"),
        card("Pertumbuhan tidak selalu berarti tren",
             "Angka pertumbuhan dari Triwulan I ke Triwulan II masih bisa dipengaruhi pola musiman, seperti "
             "panen raya atau pencairan anggaran. Karena itu, kenaikan dalam satu triwulan belum tentu "
             "menunjukkan tren pertumbuhan yang berkelanjutan. Untuk melihat perubahan dibanding kondisi "
             "yang lebih setara, biasanya digunakan pertumbuhan year-on-year (y-on-y), yaitu membandingkan "
             "triwulan yang sama dengan tahun sebelumnya. Namun, data dalam tabel ini hanya menyediakan "
             "perbandingan quarter-to-quarter (q-to-q).", icon="peringatan", caveat=True),
    ], chart("Pertumbuhan per lapangan usaha",
             f"Menunjukkan pertumbuhan seluruh kabupaten/kota dari {f['prev']} ke {f['period']} {f['year']}. "
             f"Sektor berwarna tumbuh lebih cepat dari laju nasional.",
             sv.growth_bars(sg, f["growth"], A["arus"]["accent"], "nasional", label_w=196, row_h=27),
             "pertumbuhan dihitung dari jumlah nilai per sektor",
             svg_mobile=sv.growth_bars(sg, f["growth"], A["arus"]["accent"], "nasional", compact=True)),
          18, tall=True),
)

# =============================================================================
# Babak IV · Pergeseran
# =============================================================================
mo = f["moran"]
delta = f["jawa_share_prev"] - f["jawa_share"]
mining = f["mining"]
act4 = act(
    "kini", "Pertumbuhan lebih cepat belum menutup jarak",
    "Selisih pertumbuhan memang terlihat, tetapi pola ekonomi tiap daerah masih kuat.",
    scene([
        card(f"Jawa {'turun' if delta > 0 else 'naik'}: {pct(f['jawa_share_prev'])} → {pct(f['jawa_share'])}",
             "Jawa tumbuh di bawah rata-rata nasional, sehingga kontribusinya terhadap total PDRB turun sedikit "
             "dalam satu triwulan. Namun, perubahan ini masih kecil jika dibandingkan dengan tingginya "
             "konsentrasi PDRB di Jawa yang terlihat pada babak pertama.",
             icon="timbangan"),
        card("Kantong ekonomi terlihat di peta",
             "Daerah dengan porsi pertanian tinggi cenderung berkelompok dengan daerah yang juga tinggi, "
             "sementara daerah dengan porsi rendah cenderung berdampingan dengan daerah yang rendah. "
             "Analisis Local Moran’s I (LISA) digunakan untuk menemukan pola tersebut dan membedakan klaster "
             "tinggi–tinggi, rendah–rendah, serta pencilan spasial.",
             f"Kantong pertanian (tinggi–tinggi) paling banyak ditemukan di {join_id(f['hh_prov'])}. "
             f"Sementara itu, kantong rendah–rendah banyak berkumpul di {join_id(f['ll_prov'])}.",
             icon="jaringan", stat=idn(mo["I"], 2), stat_label="Moran’s I porsi pertanian"),
        card("Spesialisasi pertambangan",
             f"Di {join_id([kab(m['label']) for m in mining])}, porsi pertambangan dalam ekonomi daerah "
             f"mencapai sekitar {idn(min(m['lq'] for m in mining), 0)}–{idn(max(m['lq'] for m in mining), 0)} "
             f"kali rata-rata nasional. Artinya, pertambangan jauh lebih menonjol di {word(len(mining))} "
             f"daerah tersebut dibandingkan secara nasional.",
             "<em>Sektor lainnya dapat ditelusuri melalui halaman Peta.</em>",
             icon="tambang"),
        card("Apa yang perlu dipantau berikutnya",
             f"Pergeseran yang sebenarnya akan terlihat pada tiga hal: porsi Jawa yang terus turun dari "
             f"{pct(f['jawa_share'])}, kantong pertanian tinggi–tinggi ({f['lisa_counts'].get('Tinggi-Tinggi', 0)} daerah) "
             f"yang menyusut atau berpindah, dan daerah luar Jawa yang tetap tumbuh di atas laju nasional pada "
             f"triwulan berikutnya. Kalau ketiganya bergerak searah, barulah laju yang lebih cepat ini bisa "
             f"disebut awal pergeseran.",
             icon="grafik"),
    ], chart("Peta LISA porsi pertanian",
             "Peta ini menunjukkan daerah yang memiliki pola pertanian serupa dengan daerah di "
             "sekitarnya. Hanya daerah dengan hasil analisis yang cukup kuat (p < 0,05) yang diberi "
             f"warna. Perhitungan menggunakan {f['spatial_k']} daerah terdekat sebagai tetangga. "
             "Arahkan kursor ke daerah untuk melihat detailnya.",
             sv.lisa_map(f), f"batas wilayah: {GEO_SOURCE}", after=sv.lisa_legend(f)), 13),
)

# =============================================================================
# Penutup
# =============================================================================
end_growth = (f"Sejumlah wilayah di luar Jawa tumbuh lebih cepat pada triwulan ini, tetapi porsi Jawa baru "
              f"berubah {idn(delta, 2)} poin persentase." if outside_leads else
              f"Porsi Jawa berubah {idn(delta, 2)} poin persentase.")
end = f'''
<section class="ws-end" aria-labelledby="ws-h-end" style="--accent:var(--tk-act4)">
  <p class="ws-kicker">Penutup</p>
  <h2 class="ws-h2" id="ws-h-end">Satu angka, banyak ekonomi</h2>
  <p style="margin-top:1.4rem">{T} terdengar seperti satu gambaran besar tentang ekonomi {n} kabupaten/kota.
    Namun, ketika angka itu dipecah, ceritanya menjadi jauh lebih beragam. Separuh PDRB dihasilkan oleh hanya
    {f["n_half"]} daerah, sementara {word(f["top_n"])} daerah teratas menyumbang {pct(f["top_share"])}.</p>
  <p>Perbedaannya bukan hanya soal besar-kecilnya ekonomi. {agr["n"]} daerah berbasis pertanian menyumbang
    {pct(agr["pct_pdrb"])} PDRB, sementara hanya {word(korp["n"])} daerah berbasis jasa perusahaan menyumbang
    {pct(korp["pct_pdrb"])}. Ada pola yang dimiliki banyak daerah, tetapi kontribusinya tidak sebesar jumlah
    daerahnya. Sebaliknya, ada pola yang hanya muncul di sedikit daerah, tetapi menghasilkan bagian ekonomi
    yang jauh lebih besar.</p>
  <p>Pertumbuhan juga tidak bergerak dengan kecepatan yang sama. {end_growth} Dengan data yang baru mencakup dua
    triwulan, perubahan tersebut belum cukup untuk menunjukkan bahwa pola ekonomi antardaerah sedang berubah.
    Bisa jadi ini hanya pergerakan dalam jangka pendek.</p>
  <p>Pada akhirnya, tidak ada satu cerita untuk seluruh daerah. Ada yang bertumpu pada pertanian, ada yang
    ditopang industri, perdagangan, pertambangan, atau jasa. Dari sini, tiap daerah punya ceritanya sendiri:
    apa yang menjadi penopang ekonominya, seberapa besar kontribusinya, dan bagaimana pertumbuhannya?</p>
</section>'''

rail = "".join(
    f'<button type="button" style="--c:var(--tk-act{a["i"]})" aria-label="Ke babak {a["roman"]}: {a["label"]}"></button>'
    for a in A.values())

css = (ASSETS / "story.css").read_text(encoding="utf-8")
js = (ASSETS / "story.js").read_text(encoding="utf-8")
# DOMPurify (st.html) membuang SELURUH blok style/script yang teksnya memuat pola
# mirip tag, tanpa pesan apa pun; halaman lalu tampil tanpa gaya. Gagal keras saja.
for _name, _text in (("story.css", css), ("story.js", js)):
    if re.search(r"<[/\w]", _text):
        raise ValueError(f"{_name} memuat pola mirip tag (kurung sudut); st.html akan membuangnya.")
# Ikon kartu Jelajah (st.page_link) dipasang sebagai mask CSS; warnanya dari var(--accent).
EXPLORE_ICONS = ["pola", "peta", "hierarki", "tabel"]
for _i, _k in enumerate(EXPLORE_ICONS, 1):
    _svg = sv.ICONS[_k].replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    css += (f'.st-key-ws-explore [data-testid="stColumn"]:nth-child({_i}) '
            f"{{--ico:url(\"data:image/svg+xml,{quote(_svg)}\")}}\n")
body = ('<div class="ws">'
        f'{slot(sv.map_defs(), "ws-defs-slot")}{hero}{act1}{act2}{act3}{act4}{end}'
        f'<nav class="ws-rail" aria-label="Babak cerita">{rail}</nav></div>')
# "<" ditulis sebagai <: DOMPurify (dipakai st.html) membuang skrip yang teksnya
# memuat pola mirip tag. Ini sekaligus mencegah "</script>" menutup skrip lebih awal.
payload = json.dumps(SLOTS).replace("<", "\\u003c")
st.html(
    f"<style>{css}</style>{body}<script>window.__WS_SVG = {payload};\n"
    f"window.__WS_STILL = {'true' if st.session_state.get('a11y_still') else 'false'};\n{js}</script>",
    unsafe_allow_javascript=True,
)

# =============================================================================
# Jelajah (dasbor penutup) + metode
# =============================================================================
with st.container(key="ws-explore"):
    st.markdown("#### Jelajahi sendiri")
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        st.page_link("views/struktur.py", label="Pola ekonomi →")
        st.caption("Pilih daerah pada biplot PCA; profil, parallel coordinates, dan heatmap ikut berubah.")
    with c2:
        st.page_link("views/peta.py", label="Peta →")
        st.caption("Pangsa, LQ, atau pertumbuhan untuk sektor apa pun; simbol proporsional; LISA.")
    with c3:
        st.page_link("views/hierarki.py", label="Wilayah & sektor →")
        st.caption("Treemap dan icicle dari pulau sampai sektor, dengan breadcrumb.")
    with c4:
        st.page_link("views/tentang.py", label="Data & metode →")
        st.caption("Sumber, pra-pemrosesan, rumus, dan unduhan data olahan.")

sil = data.silhouettes(story.PERIOD)
agr_k = f["agr_by_k"]
k_best = max(sil, key=sil.get)
agr_k_text = (f"{agr_k[N_CLUSTERS]} daerah pada k = {join_id([str(k) for k in agr_k])}"
              if len(set(agr_k.values())) == 1 else
              "; ".join(f"k = {k}: {v} daerah" for k, v in agr_k.items()))
sil_text = "menunjukkan pemisahan antarpola masih lemah" if max(sil.values()) < 0.25 else            "menunjukkan pemisahan antarpola cukup jelas"
mk = f["moran_by_k"]
half_text = (f"Separuh total PDRB tetap tercapai pada {f['n_half']} daerah, baik berdasarkan penjumlahan "
             f"{f['n_sectors']} lapangan usaha maupun nilai total PDRB BPS."
             if f["n_half"] == f["n_half_bps_row"] else
             f"Separuh total PDRB tercapai pada {f['n_half']} daerah (penjumlahan {f['n_sectors']} lapangan "
             f"usaha) atau {f['n_half_bps_row']} daerah (nilai total PDRB BPS).")
geo = escape(GEO_SOURCE)
geo = geo[:1].lower() + geo[1:]
geo = geo.replace("Sistem Informasi Geografis", "<em>Sistem Informasi Geografis</em>")
geo += (f' (<a href="{GEO_SOURCE_URL}" target="_blank" rel="noopener">tautan</a>)' if GEO_SOURCE_URL else "")
# Judul "Metode singkat" memakai gaya yang sama dengan "Jelajahi sendiri" (rata tengah, 1 rem, tebal).
st.html(f'''
<div class="ws ws-method" style="--ws-bg:var(--tk-tint4)">
  <section class="ws-end" style="padding-top:5svh;padding-bottom:10svh">
    <p class="ws-kicker ws-method-h" style="--accent:var(--tk-soft)">Metode singkat</p>
    <p><b>Data.</b> Data PDRB bersumber dari BPS, <a href="{BPS_SOURCE_URL}" target="_blank" rel="noopener"
      style="color:inherit"><em>PDRB Triwulanan Atas Dasar Harga Konstan (2010=100) Menurut 17 Kategori
      Lapangan Usaha di Kabupaten/Kota</em></a>, {f["year"]}, diakses {ACCESS_DATE}. Batas wilayah
      menggunakan {geo}.</p>
    <p><b>Perhitungan.</b> Seluruh angka pada halaman ini dihasilkan dari pengolahan data, bukan ditulis satu per
      satu secara manual.</p>
    <p><b>Konsistensi dan uji kepekaan.</b> {half_text} Klaster Basis Pertanian tetap mencakup {agr_k_text}.
      Nilai silhouette tertinggi diperoleh pada k = {k_best} ({idn(max(sil.values()), 2)}), {sil_text}.
      Nilai Moran’s I porsi pertanian berada pada {idn(min(mk.values()), 2)}–{idn(max(mk.values()), 2)}
      saat jumlah tetangga terdekat diubah dari {min(mk)} menjadi {max(mk)}.</p>
    <p><b>Keterbatasan.</b> Data yang digunakan baru mencakup Triwulan I dan II {f["year"]}. Tabel BPS
      terakhir diperbarui pada 7 September 2026, sehingga belum tersedia triwulan berikutnya untuk melihat
      pola yang lebih panjang. Karena itu, pertumbuhan q-to-q masih dapat dipengaruhi pola musiman. PDRB
      menggunakan harga konstan 2010, sedangkan batas wilayah menggunakan kode wilayah 2019,
      sehingga struktur provinsi belum sepenuhnya mengikuti pemekaran Papua setelah 2022, meskipun analisis
      tetap mencakup {n} kabupaten/kota.</p>
  </section>
</div>''')
