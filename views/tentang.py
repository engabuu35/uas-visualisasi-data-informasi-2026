"""Data & metode: sumber, pra-pemrosesan, keputusan rancangan, keterbatasan."""

import streamlit as st

import data
import preprocess as pp
from charts import idn
from config import (
    ACCESS_DATE, BPS_SOURCE_URL, BPS_TABLE_TITLE, GEO_SOURCE, GEO_SOURCE_URL, N_CLUSTERS, SPATIAL_K,
)

sil = data.silhouettes("Triwulan II")
pc2 = data.multivariate("Triwulan II").explained[:2].sum() * 100

st.title("Data & metode")

st.header("Sumber")
st.markdown(
    f"""
**Data utama:** Badan Pusat Statistik, *{BPS_TABLE_TITLE}*.
Tahun data 2026; yang sudah terisi baru Triwulan I dan II.
URL: {BPS_SOURCE_URL}
Diakses {ACCESS_DATE}.

**Data pendukung (non-BPS):** {GEO_SOURCE}{f" — {GEO_SOURCE_URL}" if GEO_SOURCE_URL else ""}.
Batas wilayah hanya dipakai untuk menggambar peta dan menghitung titik pusat serta tetangga
terdekat. Kunci penggabungannya kode wilayah BPS (4 digit).
"""
)

st.header("Pra-pemrosesan")
check = pp.validate(data.long_df())
st.markdown(
    f"""
1. **Membaca tabel lebar BPS.** Ada 17 kategori ditambah PDRB, masing-masing 5 kolom (TW I–IV dan
   tahunan). Tanda "-" (belum tersedia) diubah menjadi kosong, lalu hanya TW I dan TW II yang dipakai.
2. **Memisahkan kode dan nama kategori.** Contohnya "R,S,T,U Jasa Lainnya" menjadi kode `R,S,T,U`.
   Baris PDRB diberi kode `TOTAL` agar tidak tertukar dengan kategori P (Jasa Pendidikan).
3. **Menggabungkan dengan kode wilayah** melalui nama kab/kota. Ke-{check['wilayah']} nama cocok satu
   lawan satu, tanpa nama ganda.
4. **Pemeriksaan kualitas.** Ada {check['nilai_kosong_tw1_tw2']} nilai kosong pada TW I–II dan
   {check['nilai_nol']} sel bernilai nol (umumnya pertambangan di daerah perkotaan). Selisih maksimum
   antara jumlah 17 sektor dan baris PDRB adalah {check['selisih_maks_jumlah17_vs_total']:.2f} miliar
   ({check['selisih_relatif_maks'] * 100:.2f}%), yang berasal dari pembulatan.
5. **Menyederhanakan geometri** dengan Douglas–Peucker (toleransi 0,01°, sekitar 1 km). Ukuran berkas
   turun dari 42 MB menjadi sekitar 1 MB supaya peta tetap ringan dibuka di ponsel.
"""
)

st.header("Indikator turunan")
st.markdown(
    r"""
| Indikator | Rumus | Dipakai di |
|---|---|---|
| Pangsa sektor | $s_{ij} = x_{ij} / \sum_j x_{ij} \times 100$ | PCA, klaster, peta |
| Location quotient | $LQ_{ij} = \dfrac{x_{ij}/\sum_j x_{ij}}{\sum_i x_{ij}/\sum_{i,j} x_{ij}}$ | peta |
| Pertumbuhan q-to-q | $(x^{TW2} / x^{TW1} - 1)\times 100$, dihitung dari jumlah | peta, hierarki |
| Jarak Mahalanobis | $D^2 = \sum_{k=1}^{m} t_k^2/\lambda_k$, $m$ = PC hingga 80% varians | pencilan |
| Moran's I | $I = \frac{1}{n}\sum_i z_i \sum_j w_{ij} z_j$ (bobot terstandardisasi baris) | peta LISA |
"""
)

st.header("Keputusan rancangan")
st.markdown(
    f"""
- **Pangsa, bukan nilai, untuk analisis multivariat.** Kalau nilai rupiah yang dipakai, PC1 hanya
  akan memisahkan daerah besar dari daerah kecil. Dengan pangsa, yang dibandingkan adalah komposisi
  ekonominya.
- **Ward + PCA pada ruang z-score yang sama.** Dengan begitu klaster, biplot, dan heatmap terklaster
  saling konsisten. Jumlah klaster {N_CLUSTERS} dipilih karena silhouette-nya tertinggi di antara
  k = {min(sil)}–{max(sil)} ({idn(sil[N_CLUSTERS], 2)}), dan setiap klaster bisa diberi nama yang bermakna.
- **Warna.** Tema gelap kebiruan (bukan hitam murni). Setiap babak cerita punya satu warna aksen
  yang membawa makna (amber, jingga, hijau-toska, biru), diambil dari slot palet kategorikal yang
  ramah buta warna; pasangan merah–hijau sengaja dihindari. Klaster memakai 6 slot kategorikal mode
  gelap (lolos uji CVD pasangan bersebelahan, ΔE terburuk 8,4) ditambah encoding kedua: bentuk
  penanda di biplot, label langsung di dumbbell, dan small multiples satu warna per peta di cerita.
  Besaran memakai jingga satu-hue (nilai tinggi = lebih terang), nilai di bawah/atas acuan memakai
  biru↔jingga dengan titik tengah abu-abu. Semua palet diuji dengan simulasi Machado (2009).
- **Grafik cerita dibuat tangan sebagai SVG.** Terbaca pembaca layar (setiap grafik punya
  deskripsi nilai), tajam di layar apa pun, dan peta kecil cukup merujuk satu definisi geometri.
  Halaman Jelajah tetap memakai Plotly untuk interaksi yang lebih kaya.
- **Choropleth hanya untuk rasio.** Nilai rupiah ditampilkan sebagai simbol proporsional yang
  luasnya (bukan jari-jarinya) sebanding dengan nilai.
- **Tetangga terdekat (k = {SPATIAL_K}), bukan queen contiguity.** Banyak kab/kota berupa pulau yang tidak
  bersinggungan dengan wilayah mana pun.
"""
)

st.header("Keterbatasan")
st.markdown(
    f"""
- **Baru dua triwulan.** Pertumbuhan q-to-q masih memuat pola musiman, dan tanpa data 2025 tidak
  bisa dihitung pertumbuhan y-on-y.
- **Harga konstan 2010.** Cocok untuk membandingkan volume, tetapi struktur harganya sudah berumur
  16 tahun. Pangsa berdasarkan harga berlaku bisa sedikit berbeda.
- **Batas 514 kab/kota (kode 2019).** Pemekaran provinsi di Papua pada 2022 belum tercermin;
  daerah di sana masih dikelompokkan ke Papua dan Papua Barat.
- **PC1–PC2 hanya menangkap sekitar {idn(pc2, 0)}% variasi.** Kedekatan di biplot perlu dibaca bersama heatmap.
- **Klaster bersifat deskriptif.** Silhouette yang rendah menunjukkan batas antarkelompok tidak
  tajam; banyak daerah berada di wilayah transisi.
"""
)

st.header("Unduh data olahan")
st.download_button("pdrb_long.csv", data.long_df().to_csv(index=False).encode("utf-8"),
                   file_name="pdrb_long.csv", mime="text/csv")
st.download_button("wilayah.csv", data.regions().reset_index().to_csv(index=False).encode("utf-8"),
                   file_name="wilayah.csv", mime="text/csv")
