"""Halaman Cerita: scrollytelling empat babak (tangkai 'martini glass').

    I   Pusat          ekonomi besar yang bertumpu pada sedikit tempat
    II  Jurang         banyak daerahnya, kecil porsinya
    III Arus balik     yang tumbuh paling cepat ada di luar pusat
    IV  Belum berubah  lebih cepat belum berarti mengejar

Setiap angka di teks diambil dari story.figures(); halaman ini hanya
merangkai kalimat. Kalimat yang bergantung pada peringkat (siapa tercepat,
siapa paling lambat) dibentuk dari data, bukan dari asumsi penulis.
"""

import json
from html import escape
from pathlib import Path

import streamlit as st

import data
import story
import story_svg as sv
from charts import idn, signed
from config import (
    ACCESS_DATE, ACTS, BPS_SOURCE_URL, GEO_SOURCE, GEO_SOURCE_URL, N_CLUSTERS,
)
from story import join_id, word

ASSETS = Path(__file__).resolve().parents[1] / "assets"
f = story.figures()
reg = data.regions()
A = {a["key"]: a for a in ACTS}


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
    tail = f"; {extra}" if extra else ""
    # Versi pendek untuk ponsel: grafik yang tersemat tidak boleh habis dimakan
    # catatan sumber. Rincian lengkapnya tetap ada di bagian metode.
    return (f'<p class="ws-src ws-only-desk">Sumber: BPS, PDRB ADHK 2010 menurut lapangan usaha, kab/kota '
            f'{f["year"]} (<a href="{BPS_SOURCE_URL}" target="_blank" rel="noopener">tabel</a>, '
            f'diakses {ACCESS_DATE}), diolah{tail}.</p>'
            f'<p class="ws-src ws-only-mob">Sumber: BPS, PDRB ADHK 2010 kab/kota {f["year"]}, diolah.</p>')


def card(title, *paras, caveat=False):
    body = "".join(f"<p>{p}</p>" for p in paras)
    return f'<article class="ws-card{" ws-caveat" if caveat else ""}"><h3>{title}</h3>{body}</article>'


def chart(title, sub, svg, src_extra="", after="", svg_mobile=None):
    svgs = (slot(svg, "ws-svg ws-only-desk") + slot(svg_mobile, "ws-svg ws-only-mob")
            if svg_mobile else slot(svg))
    return (f'<figure class="ws-chart"><p class="ws-chart-t">{title}</p><p class="ws-chart-s">{sub}</p>'
            f'{svgs}{after}{source(src_extra)}</figure>')


def scene(cards, fig, half_rem, tall=False):
    # Kotak sticky diletakkan di tengah layar: top = max(ruang header, 50svh - setengah tinggi konten).
    # tall=True: grafik terlalu tinggi untuk disematkan di ponsel; di sana ia ikut mengalir.
    top = f"max(4.75rem, calc(50svh - {half_rem}rem))"
    cls = "ws-scene ws-scene-tall" if tall else "ws-scene"
    return (f'<div class="{cls}"><div class="ws-cards">{"".join(cards)}</div>'
            f'<div class="ws-stage" style="--stick-top:{top}">{fig}</div></div>')


def act(key, title, dek, *scenes):
    a = A[key]
    return (f'<section class="ws-act" id="ws-{key}" data-tint="{a["tint"]}" '
            f'style="--accent:{a["accent"]};--tint:{a["tint"]}" aria-labelledby="ws-h-{key}">'
            f'<header class="ws-act-head"><p class="ws-kicker">Babak {a["roman"]} · {a["label"]}</p>'
            f'<h2 class="ws-h2" id="ws-h-{key}">{title}</h2><p class="ws-act-dek">{dek}</p></header>'
            f'{"".join(scenes)}</section>')


n = f["n_regions"]
T = trillion(f["national"])

# =============================================================================
# Hero
# =============================================================================
t1 = A["pusat"]["tint"]
t1rgb = ",".join(str(int(t1[i:i + 2], 16)) for i in (1, 3, 5))
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
  <div class="ws-hero-copy" style="--accent:{A["pusat"]["accent"]}">
    <p class="ws-kicker">PDRB {n} kabupaten/kota · {f["period"]} {f["year"]}</p>
    <h1 class="ws-title">Satu negeri, {n} wajah ekonomi</h1>
    <p class="ws-dek">Dalam satu triwulan, kabupaten dan kota di Indonesia menghasilkan nilai tambah
      <b>{T}</b>. Dibuka per daerah, angka itu bertumpu pada segelintir tempat, dan sebagian besar
      daerah hidup dari hal yang sama sekali berbeda.</p>
    <div class="ws-stats">{stats_html}</div>
    <p class="ws-cue">Gulir untuk mulai ↓</p>
  </div>
</section>'''

# =============================================================================
# Babak I · Pusat
# =============================================================================
act1 = act(
    "pusat", f"Separuh ekonomi ada di {f['n_half']} daerah",
    "Angka nasional terlihat kokoh, tetapi bertumpu pada sedikit tempat.",
    scene([
        card(f"{T} dalam satu triwulan",
             f"Itu nilai tambah {n} kabupaten/kota pada {f['period']} {f['year']}, dengan harga konstan "
             f"2010. Biasanya angka ini dibaca sebagai satu ekonomi."),
        card(f"{f['n_half']} dari {n}",
             f"Urutkan daerah dari PDRB terbesar, lalu jumlahkan satu per satu. Pada urutan ke-{f['n_half']}, "
             f"separuh PDRB nasional sudah terkumpul. {n - f['n_half']} daerah lainnya berbagi separuh sisanya."),
        card(f"{cap(word(f['top_n']))} teratas: {pct(f['top_share'])}",
             f"Mereka adalah {f['top_text']}."),
        card(f"Jawa: {pct(f['jawa_share'])}",
             f"{cap(word(f['jawa_provinces']))} provinsi di Pulau Jawa menghasilkan {pct(f['jawa_share'])} "
             f"PDRB kabupaten/kota. Angka nasional sangat ditentukan oleh apa yang terjadi di sedikit tempat."),
    ], chart("Kurva konsentrasi PDRB",
             "Garis putus-putus: keadaan seandainya setiap daerah menyumbang sama besar. "
             "Arahkan kursor ke kurva untuk melihat urutannya.",
             sv.concentration(f, A["pusat"]["accent"]), "jumlah 17 lapangan usaha",
             svg_mobile=sv.concentration(f, A["pusat"]["accent"], compact=True)), 17),
)

# =============================================================================
# Babak II · Jurang
# =============================================================================
agr, korp, gov = f["agr"], f["korp"], f["gov"]
korp_lines = [f"{cap(word(korp['n_dki']))} di antaranya kota di Jakarta"
              + (f", ditambah {join_id(korp['others'])}." if korp["others"] else ".")]
if korp["small"]:
    mn_lo, mn_hi = min(korp["small_mn"]), max(korp["small_mn"])
    ratio = (sum(korp["small_mn"]) / len(korp["small_mn"])) / korp["median_mn"]
    ranks = join_id([f"ke-{r}" for r in korp["small_rank"]])
    korp_lines.append(
        f"{join_id(korp['small'])} ikut masuk walau tidak termasuk {korp['small_rank_cut']} besar PDRB "
        f"(peringkat {ranks}). Porsi jasa perusahaannya {idn(mn_lo)}–{pct(mn_hi)}, sekitar "
        f"{idn(ratio, 0)} kali median daerah ({pct(korp['median_mn'], 2)}). Klaster dibentuk dari porsi, "
        f"bukan besaran.")

gov_lines = [f"{gov['n_papua']} di antaranya di Papua dan Papua Barat. Porsi {join_id(gov['top_sectors'])} "
             f"di daerah-daerah ini paling menonjol dibanding pola lain."]
for r in gov["non_papua"]:
    ikn = ", lokasi pembangunan Ibu Kota Nusantara" if r["name"] == "Penajam Paser Utara" else ""
    top = ", tertinggi di Indonesia" if r["is_national_max"] else ""
    gov_lines.append(f"Satu-satunya di luar Papua adalah <b>{escape(r['label'])}</b>{ikn}. "
                     f"Porsi {r['sector']}nya {pct(r['share'])}{top}.")

where = [c for c in f["clusters"] if c["klaster"] not in ("Pusat jasa korporat", "Ditopang belanja pemerintah")]
where_text = "; ".join(f"{c['klaster'].lower()} di {c['top_island']} ({c['top_island_n']} dari {c['n']})"
                       for c in where)

act2 = act(
    "jurang", "Banyak daerahnya, kecil porsinya",
    "Ukuran baru separuh cerita. Dua daerah dengan PDRB sama bisa hidup dari sawah atau dari batu bara.",
    scene([
        card(f"{cap(word(f['n_clusters']))} pola ekonomi",
             f"Daerah dikelompokkan menurut porsi {f['n_sectors']} lapangan usahanya, bukan nilai rupiahnya, "
             f"sehingga yang dibandingkan adalah susunan ekonominya. Hasilnya {word(f['n_clusters'])} pola."),
        card(f"Agraris: {agr['n']} daerah, {pct(agr['pct_pdrb'])} PDRB",
             f"Pola paling umum, {pct(agr['pct_regions'])} dari seluruh kabupaten/kota. Porsinya dalam PDRB "
             f"nasional tidak sampai separuh porsinya dalam jumlah daerah."
             if agr["pct_pdrb"] < agr["pct_regions"] / 2 else
             f"Pola paling umum, {pct(agr['pct_regions'])} dari seluruh kabupaten/kota."),
        card(f"Pusat jasa korporat: {korp['n']} daerah, {pct(korp['pct_pdrb'])} PDRB", *korp_lines),
    ], chart("Porsi jumlah daerah vs porsi PDRB",
             "Titik berongga: porsi dalam jumlah daerah. Titik berwarna: porsi dalam PDRB nasional.",
             sv.dumbbell(f), f"klaster Ward pada pangsa sektor terstandardisasi, k = {N_CLUSTERS}",
             svg_mobile=sv.dumbbell(f, compact=True)), 15, tall=True),
    scene([
        card(f"Ditopang belanja pemerintah: {gov['n']} daerah, {pct(gov['pct_pdrb'])} PDRB", *gov_lines),
        card("Setiap pola punya wilayahnya",
             f"Terbanyak menurut pulau: {where_text}."),
    ], chart("Di mana setiap pola berada",
             "Satu peta per pola, satu warna per peta. Lingkaran menandai daerah yang terlalu kecil "
             "untuk terlihat. Angka di kanan = jumlah daerah.",
             sv.cluster_maps(f), "batas wilayah: data pendukung non-BPS"), 18, tall=True),
)

# =============================================================================
# Babak III · Arus balik
# =============================================================================
ig = f["island_growth"]
fast1, fast2, slowest = ig[0], ig[1], ig[-1]
jawa = f["jawa_growth"]
outside_leads = fast1["label"] != "Jawa"
sg = f["sector_growth"]
s_fast, s_slow = sg[:3], sg[-2:]
largest = [r for r in sg if r["label"].lower() in f["largest_sectors"]]

slow_text = (
    f"{slowest['label']} justru tumbuh paling lambat ({signed(slowest['value'])}%), "
    f"{'sedikit ' if jawa - slowest['value'] < 0.5 else ''}di bawah Jawa ({signed(jawa)}%). "
    f"Di luar Jawa tidak otomatis berarti lebih cepat."
    if slowest["label"] != "Jawa" else
    f"Jawa tumbuh paling lambat ({signed(jawa)}%).")

act3 = act(
    "arus", "Yang tumbuh paling cepat ada di luar pusat" if outside_leads else "Pusat tetap tumbuh paling cepat",
    f"Dibanding {f['prev']}, PDRB naik {signed(f['growth'])}%. Lajunya tidak merata.",
    scene([
        card(f"{signed(f['growth'])}% dalam satu triwulan",
             f"PDRB {n} kabupaten/kota pada {f['period']} naik {pct(f['growth'])} dibanding {f['prev']}. "
             f"Garis putus-putus pada grafik adalah laju nasional ini."),
        card(f"{fast1['label']} dan {fast2['label']}",
             f"{fast1['label']} tumbuh {signed(fast1['value'])}% dan {fast2['label']} {signed(fast2['value'])}%, "
             f"sekitar {idn((fast1['value'] + fast2['value']) / 2 / jawa, 1)} kali laju Jawa ({signed(jawa)}%)."),
        card(f"Paling lambat: {slowest['label']}", slow_text),
    ], chart("Pertumbuhan per pulau",
             "TW II terhadap TW I. Berwarna: di atas laju nasional; abu: di bawahnya.",
             sv.growth_bars(ig, f["growth"], A["arus"]["accent"], "nasional", label_w=150, row_h=40),
             "dihitung dari jumlah nilai seluruh kab/kota di pulau tersebut",
             svg_mobile=sv.growth_bars(ig, f["growth"], A["arus"]["accent"], "nasional", compact=True)), 13),
    scene([
        card("Bukan sektor terbesar" if f["fast_sectors_are_small"] else "Sektor tercepat",
             f"Tercepat: {join_id([rate(r) for r in s_fast])}. "
             + (f"Dua sektor terbesar, {join_id([rate(r) for r in largest])}, "
                f"tumbuh di bawah laju nasional." if all(r["value"] < f["growth"] for r in largest) else "")),
        card(f"{s_slow[0]['label']} dan {s_slow[1]['label'].lower()} "
             + ("nyaris diam" if max(r["value"] for r in s_slow) < 1 else "paling lambat"),
             f"Masing-masing hanya {signed(s_slow[0]['value'])}% dan {signed(s_slow[1]['value'])}%."),
        card("Hati-hati membaca laju triwulanan",
             "Perbandingan antartriwulan (q-to-q) masih memuat pola musiman, misalnya panen raya atau "
             "pencairan anggaran. Untuk membaca tren perlu pembanding triwulan yang sama tahun "
             "sebelumnya (y-on-y), dan data itu tidak ada dalam tabel ini.", caveat=True),
    ], chart("Pertumbuhan per lapangan usaha",
             "TW II terhadap TW I, jumlah seluruh kab/kota. Berwarna: di atas laju nasional.",
             sv.growth_bars(sg, f["growth"], A["arus"]["accent"], "nasional", label_w=196, row_h=27),
             "pertumbuhan dihitung dari jumlah nilai per sektor",
             svg_mobile=sv.growth_bars(sg, f["growth"], A["arus"]["accent"], "nasional", compact=True)),
          18, tall=True),
)

# =============================================================================
# Babak IV · Belum berubah
# =============================================================================
mo = f["moran"]
p_txt = f"p ≤ {idn(mo['p_floor'], 3)}" if mo["p"] <= mo["p_floor"] else f"p = {idn(mo['p'], 3)}"
delta = f["jawa_share_prev"] - f["jawa_share"]
mining = f["mining"]
act4 = act(
    "kini", "Lebih cepat belum berarti mengejar",
    "Selisih laju itu nyata, tetapi pola ekonominya mengakar di peta.",
    scene([
        card(f"Porsi Jawa: {pct(f['jawa_share_prev'])} → {pct(f['jawa_share'])}",
             f"Karena tumbuh di bawah rata-rata, porsi Jawa dalam PDRB berubah {signed(-delta, 2)} poin persen "
             f"dalam satu triwulan. Dibanding jurang di babak I, pergeseran itu kecil."),
        card(f"Moran's I = {idn(mo['I'], 2)}",
             f"Daerah yang bertumpu pada pertanian cenderung bertetangga dengan daerah agraris juga. "
             f"Kalau sebarannya acak, nilainya mendekati nol ({p_txt}, {f['permutations']} permutasi).",
             f"Kantong pertanian (tinggi-tinggi) paling banyak di {join_id(f['hh_prov'])}. Kantong "
             f"nonpertanian (rendah-rendah) berkumpul di {join_id(f['ll_prov'])}."),
        card("Bergantung pada satu sektor",
             f"Di {join_id([m['label'] for m in mining])}, porsi pertambangan "
             f"{idn(min(m['lq'] for m in mining), 0)}–{idn(max(m['lq'] for m in mining), 0)} kali "
             f"rata-rata nasional (location quotient). Telusuri sektor lain di halaman Peta."),
        card("Dua triwulan belum menjadi tren",
             "Laju yang lebih cepat di luar Jawa bisa menjadi awal pergeseran, bisa juga pola musiman. "
             f"Tabel {f['year']} baru terisi dua triwulan, sehingga pertanyaan itu belum bisa dijawab.",
             caveat=True),
    ], chart("Peta LISA porsi pertanian",
             f"Hanya daerah dengan p < 0,05 yang diwarnai; bobot {f['spatial_k']} tetangga terdekat. "
             "Arahkan kursor ke daerah untuk detailnya.",
             sv.lisa_map(f), "batas wilayah: data pendukung non-BPS", after=sv.lisa_legend(f)), 13),
)

# =============================================================================
# Penutup
# =============================================================================
end = f'''
<section class="ws-end" aria-labelledby="ws-h-end" style="--accent:{A["kini"]["accent"]}">
  <p class="ws-kicker">Penutup</p>
  <h2 class="ws-h2" id="ws-h-end">Satu angka, banyak ekonomi</h2>
  <p style="margin-top:1.4rem">{T} terdengar seperti satu ekonomi. Separuhnya dihasilkan
    <b>{f["n_half"]} daerah</b>, dan {word(f["top_n"])} daerah teratas saja sudah {pct(f["top_share"])}.</p>
  <p>Jurangnya bukan hanya soal ukuran. <b>{agr["n"]} daerah agraris</b> menyumbang {pct(agr["pct_pdrb"])}
    PDRB, sementara {word(korp["n"])} pusat jasa korporat menyumbang {pct(korp["pct_pdrb"])}.</p>
  <p>Luar Jawa memang tumbuh lebih cepat triwulan ini, tetapi porsi Jawa baru bergeser
    {idn(delta, 2)} poin. Dengan dua triwulan data, belum bisa dikatakan apakah itu awal pergeseran
    atau sekadar musim.</p>
  <p>Cerita ini hanya satu jalur. Di bawah, Anda bisa mencari daerah sendiri: <b>bagaimana dengan daerah Anda?</b></p>
</section>'''

rail = "".join(
    f'<button type="button" style="--c:{a["accent"]}" aria-label="Ke babak {a["roman"]}: {a["label"]}"></button>'
    for a in ACTS)

css = (ASSETS / "story.css").read_text(encoding="utf-8")
js = (ASSETS / "story.js").read_text(encoding="utf-8")
body = (f'<div class="ws" style="--t1rgb:{t1rgb};--ws-tail:{A["kini"]["tint"]}">'
        f'{slot(sv.map_defs(), "ws-defs-slot")}{hero}{act1}{act2}{act3}{act4}{end}'
        f'<nav class="ws-rail" aria-label="Babak cerita">{rail}</nav></div>')
# "<" ditulis sebagai <: DOMPurify (dipakai st.html) membuang skrip yang teksnya
# memuat pola mirip tag. Ini sekaligus mencegah "</script>" menutup skrip lebih awal.
payload = json.dumps(SLOTS).replace("<", "\\u003c")
st.html(
    f"<style>{css}</style>{body}<script>window.__WS_SVG = {payload};\n{js}</script>",
    unsafe_allow_javascript=True,
)

# =============================================================================
# Jelajah (dasbor penutup) + metode
# =============================================================================
with st.container(key="ws-explore"):
    st.markdown("#### Jelajahi sendiri")
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        st.page_link("views/struktur.py", label="Struktur ekonomi →")
        st.caption("Pilih daerah pada biplot PCA; profil, parallel coordinates, dan heatmap ikut berubah.")
    with c2:
        st.page_link("views/peta.py", label="Peta →")
        st.caption("Pangsa, LQ, atau pertumbuhan untuk sektor apa pun; simbol proporsional; LISA.")
    with c3:
        st.page_link("views/hierarki.py", label="Hierarki →")
        st.caption("Treemap dan icicle dari pulau sampai sektor, dengan breadcrumb.")
    with c4:
        st.page_link("views/tentang.py", label="Data & metode →")
        st.caption("Sumber, pra-pemrosesan, rumus, dan unduhan data olahan.")

sil = data.silhouettes(story.PERIOD)
agr_k = f["agr_by_k"]
agr_k_text = (f"{agr_k[N_CLUSTERS]} daerah pada k = {join_id([str(k) for k in agr_k])}"
              if len(set(agr_k.values())) == 1 else
              "; ".join(f"k = {k}: {v} daerah" for k, v in agr_k.items()))
mk = f["moran_by_k"]
half_text = (f"urutan ke-{f['n_half']} baik dengan penyebut jumlah {f['n_sectors']} sektor maupun baris PDRB resmi BPS"
             if f["n_half"] == f["n_half_bps_row"] else
             f"urutan ke-{f['n_half']} (jumlah {f['n_sectors']} sektor) atau ke-{f['n_half_bps_row']} (baris PDRB BPS)")
geo = escape(GEO_SOURCE) + (f' (<a href="{GEO_SOURCE_URL}" target="_blank" rel="noopener">tautan</a>)'
                            if GEO_SOURCE_URL else "")
st.html(f'''
<div class="ws ws-method" style="--ws-bg:{A["kini"]["tint"]}">
  <section class="ws-end" style="padding-top:5svh;padding-bottom:10svh">
    <p class="ws-kicker" style="--accent:#8A847D">Metode singkat</p>
    <p><b>Data.</b> BPS, PDRB Triwulanan ADHK 2010 menurut 17 kategori lapangan usaha di kabupaten/kota,
      {f["year"]} (<a href="{BPS_SOURCE_URL}" target="_blank" rel="noopener" style="color:inherit">tabel</a>,
      diakses {ACCESS_DATE}). Batas wilayah: {geo}, data pendukung non-BPS.</p>
    <p><b>Angka.</b> Semua angka di halaman ini dihitung dari tabel olahan setiap kali halaman dimuat;
      tidak ada yang diketik manual.</p>
    <p><b>Asumsi dan kepekaan.</b> Separuh PDRB tercapai pada {half_text}. Klaster Agraris berisi
      {agr_k_text}; silhouette Ward tertinggi pada k = {max(sil, key=sil.get)} ({idn(max(sil.values()), 2)}),
      rendah, jadi batas antarpola tidak tajam. Moran's I porsi pertanian berkisar
      {idn(min(mk.values()), 2)}–{idn(max(mk.values()), 2)} untuk {min(mk)}–{max(mk)} tetangga terdekat.</p>
    <p><b>Keterbatasan.</b> Baru dua triwulan, sehingga pertumbuhan q-to-q bercampur pola musiman. Harga
      konstan memakai tahun dasar 2010. Batas wilayah memakai kode 2019, sebelum pemekaran Papua.</p>
  </section>
</div>''')
