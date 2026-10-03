"""Data & metode: sumber, pra-pemrosesan, keputusan rancangan, keterbatasan."""

import numpy as np
import streamlit as st

import data
import preprocess as pp
from charts import idn
from config import (
    ACCESS_DATE, BPS_SOURCE_URL, BPS_TABLE_TITLE, GEO_SOURCE, N_CLUSTERS, PERMUTATIONS,
    SPATIAL_K,
)
from ui import page_kicker

sil = data.silhouettes("Triwulan II")
pc2 = data.multivariate("Triwulan II").explained[:2].sum() * 100
n_reg = len(data.values("Triwulan II"))

# LISA porsi pertanian: signifikan tanpa koreksi vs dengan FDR Benjamini-Hochberg 5%.
lisa_p = np.sort(data.moran("Pangsa sektor", "A", "Triwulan II")["p_local"])
lisa_sig = int((lisa_p < 0.05).sum())
bh_ok = np.nonzero(lisa_p <= 0.05 * np.arange(1, n_reg + 1) / n_reg)[0]
lisa_fdr = int(bh_ok[-1] + 1) if len(bh_ok) else 0

page_kicker("Rujukan · Data & metode")
st.title("Data & metode")
# Paragraf dan butir daftar halaman ini rata kiri-kanan, tanpa pemenggalan kata (sama dengan "Pola ekonomi").
st.html(
    "<style>"
    '[data-testid="stMain"] [data-testid="stMarkdownContainer"] :is(p, li), [data-testid="stMain"] p.lede '
    "{ text-align: justify; text-justify: inter-word; hyphens: none; word-break: normal; "
    "overflow-wrap: normal; }"
    '[data-testid="stMain"] [data-testid="stWidgetLabel"] p, [data-testid="stMain"] [data-testid="stButtonGroup"] p '
    "{ text-align: left; }"
    '[data-testid="stMain"] p.lede { max-width: none; }'
    # Rumus di tabel indikator tidak dipotong ke beberapa baris; kolom Keterangan yang membungkus.
    '[data-testid="stMain"] td:nth-child(2), [data-testid="stMain"] td:nth-child(2) .katex { white-space: nowrap; }'
    # Di ponsel tabel 4 kolom lebih lebar dari layar: gulir di dalam tabel, bukan seluruh halaman.
    '[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(> table) { overflow-x: auto; }'
    "</style>"
)

st.header("Sumber")
st.markdown(
    f"""
**Data utama.** Badan Pusat Statistik, *{BPS_TABLE_TITLE}*. Hingga data diambil, yang tersedia baru
Triwulan I dan II 2026. Diakses {ACCESS_DATE}. [Tabel BPS]({BPS_SOURCE_URL}).

**Data pendukung.** {GEO_SOURCE}. Data wilayah digunakan untuk pemetaan, penentuan titik pusat daerah,
dan analisis tetangga terdekat, bukan untuk menghitung nilai PDRB. Penggabungan dengan data BPS
dilakukan menggunakan kode wilayah BPS 4 digit.
"""
)

st.header("Pra-pemrosesan data")
check = pp.validate(data.long_df())
st.markdown(
    f"""
1. **Membaca dan menata tabel BPS.**
   Tabel BPS berbentuk tabel lebar, dengan 17 kategori lapangan usaha ditambah total PDRB. Masing-masing
   memiliki lima kolom, yaitu Triwulan I, Triwulan II, Triwulan III, Triwulan IV, dan tahunan. Tanda “−”
   pada tabel menunjukkan nilai yang belum tersedia dan diperlakukan sebagai kosong dalam proses
   pengolahan. Karena data tahun 2026 yang tersedia baru sampai Triwulan II, analisis dalam webstory ini
   hanya menggunakan Triwulan I dan II 2026.

2. **Memisahkan kode dan nama lapangan usaha.**
   Nama kategori pada tabel BPS tidak selalu hanya berupa nama sektor, tetapi dapat diawali dengan kode
   kategori. Kode dan nama dipisahkan agar setiap lapangan usaha dapat dikenali secara konsisten dalam
   pengolahan dan visualisasi. Misalnya, “R,S,T,U Jasa Lainnya” dipisahkan menjadi kode “R,S,T,U” dan nama
   “Jasa Lainnya”. Baris total PDRB diberi kode khusus “TOTAL” agar tidak tertukar dengan kategori P, yaitu
   Jasa Pendidikan.

3. **Menggabungkan data dengan wilayah.**
   Data PDRB kemudian dicocokkan dengan data batas wilayah kabupaten/kota. Pencocokan dilakukan
   berdasarkan nama kabupaten/kota, dan seluruh {check['wilayah']} daerah berhasil dipasangkan satu lawan
   satu tanpa ditemukan nama yang ganda. Hasil penggabungan ini menjadi dasar untuk menghubungkan nilai
   PDRB dengan lokasi geografis masing-masing daerah.

4. **Memeriksa kelengkapan dan konsistensi data.**
   Sebelum digunakan untuk analisis, data diperiksa untuk memastikan tidak ada nilai yang hilang pada
   Triwulan I dan II. Hasil pemeriksaan menunjukkan {check['nilai_kosong_tw1_tw2']} nilai kosong pada dua
   triwulan tersebut. Terdapat {check['nilai_nol']} sel bernilai nol, yang umumnya muncul pada sektor
   pertambangan di wilayah perkotaan. Selain itu, jumlah dari 17 lapangan usaha dibandingkan kembali
   dengan baris total PDRB BPS. Selisih maksimum hanya Rp{idn(check['selisih_maks_jumlah17_vs_total'], 2)}
   miliar atau sekitar {idn(check['selisih_relatif_maks'] * 100, 2)}%, sehingga perbedaan tersebut
   dianggap berasal dari pembulatan angka pada tabel BPS.

5. **Menyiapkan data untuk analisis dan visualisasi.**
   Setelah data bersih dan konsisten, formatnya diubah agar dapat digunakan untuk berbagai kebutuhan di
   webstory, mulai dari perhitungan kontribusi dan pertumbuhan, pengelompokan daerah berdasarkan struktur
   ekonomi, hingga analisis spasial. Dengan satu basis data yang sama, angka yang muncul pada narasi,
   grafik, peta, dan halaman eksplorasi dihitung dari sumber yang konsisten.

6. **Meringankan data peta.**
   Batas wilayah asli memiliki jumlah titik geometri yang cukup besar sehingga ukuran berkas mencapai
   sekitar 42 MB. Agar peta dapat dibuka lebih cepat dan tetap nyaman digunakan, terutama pada perangkat
   dengan koneksi atau kemampuan terbatas, geometri disederhanakan menggunakan metode Douglas–Peucker
   dengan toleransi 0,01° atau sekitar 1 km. Setelah penyederhanaan, ukuran berkas turun menjadi sekitar
   1 MB tanpa mengubah bentuk wilayah secara berarti pada skala tampilan webstory.

7. **Menjaga konsistensi seluruh tampilan.**
   Angka yang ditampilkan pada setiap bagian halaman dihitung dari data olahan yang sama. Dengan
   demikian, nilai total PDRB, kontribusi sektor, pertumbuhan antarkuartal, hasil pengelompokan, maupun
   informasi pada peta tidak berasal dari angka yang dimasukkan satu per satu, tetapi dihasilkan dari
   proses pengolahan data yang sama.
"""
)

st.header("Indikator turunan")
# Tabel ditulis sebagai string mentah (kurung kurawal LaTeX); angka yang bergantung
# pada data/konfigurasi disisipkan lewat penanda __X__, bukan f-string.
st.markdown(
    r"""
Notasi: $x_{ij}$ adalah PDRB ADHK (miliar rupiah) kabupaten/kota $i$ pada lapangan usaha $j$,
dengan $i = 1, \dots, n$ ($n$ = __N__) dan $j = 1, \dots, 17$.

| Indikator | Rumus | Keterangan | Dipakai di |
|---|---|---|---|
| Pangsa sektor | $s_{ij} = \dfrac{x_{ij}}{\sum_j x_{ij}} \times 100$ | Penyebutnya jumlah 17 lapangan usaha (bukan baris PDRB BPS), sehingga pangsa setiap daerah tepat berjumlah 100%. | Potret PDRB, PCA, klaster, peta |
| Location quotient | $LQ_{ij} = \dfrac{x_{ij}/\sum_j x_{ij}}{\sum_i x_{ij}/\sum_{i,j} x_{ij}}$ | $LQ_{ij} > 1$: sektor $j$ lebih terkonsentrasi di daerah $i$ dibanding gabungan __N__ kabupaten/kota (indikasi sektor basis). | Potret PDRB, peta |
| Pertumbuhan q-to-q | $g = \left(\dfrac{\sum x^{(\mathrm{TW\,II})}}{\sum x^{(\mathrm{TW\,I})}} - 1\right) \times 100$ | Penjumlahan atas semua sel (daerah × sektor) di bawah daerah, pulau, atau simpul hierarki; untuk satu sektor di satu daerah hanya satu sel. Tidak dihitung bila $\sum x^{(\mathrm{TW\,I})} = 0$. | Potret PDRB, peta, hierarki |
| Jarak Mahalanobis | $D_i^2 = \sum_{k=1}^{m} \dfrac{t_{ik}^2}{\lambda_k}$ | $t_{ik}$: skor PC ke-$k$ daerah $i$ dari z-score pangsa; $\lambda_k$: varians PC ke-$k$; $m$: jumlah PC terkecil yang varians kumulatifnya ≥ 80% (saat ini $m$ = __M__). Pencilan bila $D_i^2 > \chi^2_{m;\,0{,}99}$. | pencilan |
| Moran's I | $I = \dfrac{1}{n} \sum_i z_i \sum_j w_{ij} z_j$ | $z_i = (x_i - \bar{x})/\sigma$ dengan $\sigma$ simpangan baku populasi; $w_{ij} = 1/k_i$ untuk $k_i$ tetangga terdekat ($k$ = __K__), sehingga baris terstandardisasi dan $\sum_{i,j} w_{ij} = n$. Nilai harapan bila acak $E[I] = -1/(n-1)$. Signifikansi global dan lokal (LISA) dari __P__ permutasi. | Potret PDRB, peta LISA |
""".replace("__N__", str(n_reg)).replace("__M__", str(data.multivariate("Triwulan II").n_pc_outlier))
    .replace("__K__", str(SPATIAL_K)).replace("__P__", str(PERMUTATIONS))
)

st.header("Keputusan rancangan")
st.markdown(
    f"""
- **Pangsa, bukan nilai rupiah, untuk analisis multivariat.** Nilai rupiah terutama menangkap
  perbedaan ukuran ekonomi antardaerah. Akibatnya, komponen utama dapat lebih banyak memisahkan daerah
  besar dan kecil. Dengan menggunakan pangsa sektor, yang dibandingkan adalah komposisi ekonomi
  masing-masing daerah.
- **Ward + PCA pada ruang z-score yang sama.** Seluruh analisis multivariat menggunakan variabel pangsa
  sektor yang telah distandardisasi menjadi z‑score. Dengan demikian, hasil PCA, klaster Ward, biplot,
  dan heatmap tetap berada pada dasar data yang konsisten. Jumlah klaster k = {N_CLUSTERS} dipilih
  karena memberikan nilai silhouette tertinggi pada rentang k = {min(sil)}–{max(sil)}
  ({idn(sil[N_CLUSTERS], 2)}), sekaligus menghasilkan kelompok yang masih dapat diberi interpretasi
  ekonomi yang jelas.
- **Tema terang dan gelap.** Tema mengikuti pengaturan perangkat secara default dan dapat diubah melalui
  menu ⋮ → System / Light / Dark. Perubahan tema diterapkan secara konsisten pada grafik, peta dasar
  (*Carto Positron* / *Carto Darkmatter*), dan halaman Cerita. Teks utama dijaga dengan rasio kontras
  minimal 4,5:1 terhadap latar.
- **Palet warna dirancang untuk aksesibilitas.** Pilihan palet tersedia melalui tombol Aksesibilitas di tepi kiri layar.
  Untuk data berurutan digunakan Viridis atau Cividis, sedangkan untuk kategori digunakan Okabe–Ito.
  Data yang menunjukkan posisi di bawah atau di atas suatu acuan menggunakan skema biru–jingga atau
  merah–biru. Tidak digunakan kombinasi merah–hijau sebagai satu-satunya pembeda.
- **Warna tidak menjadi satu-satunya penanda.** Karena perbedaan warna dapat sulit dikenali oleh sebagian
  pembaca, setiap informasi penting diberi penanda tambahan. Klaster pada biplot menggunakan bentuk
  titik, dumbbell menggunakan label langsung, parallel coordinates dan heatmap menggunakan legenda
  bernama, sedangkan peta pada halaman Cerita menggunakan small multiples dengan satu warna untuk setiap
  pola. Palet diuji menggunakan simulasi defisiensi penglihatan warna dan emulasi DevTools untuk
  protanopia, deuteranopia, dan tritanopia.
- **Grafik pada halaman Cerita dibuat sebagai SVG.** Pendekatan ini menjaga ketajaman grafik pada
  berbagai ukuran layar sekaligus memungkinkan setiap visual diberi deskripsi nilai yang dapat dibaca
  oleh pembaca layar. Peta menggunakan definisi geometri yang sama agar ukuran dan bentuk wilayah tetap
  konsisten. Halaman Jelajah tetap menggunakan Plotly untuk mendukung interaksi seperti seleksi dan
  penyaringan.
- **Choropleth digunakan untuk rasio, bukan nilai rupiah.** Warna peta menunjukkan ukuran relatif seperti
  pangsa, LQ, atau laju pertumbuhan. Nilai rupiah ditampilkan terpisah menggunakan simbol proporsional,
  dengan luas lingkaran yang sebanding dengan nilai PDRB.
- **Tetangga terdekat (k = {SPATIAL_K}), bukan queen contiguity.** Bobot spasial menggunakan {idn(SPATIAL_K, 0)}
  wilayah terdekat karena tidak semua kabupaten/kota berbagi batas darat. Pendekatan ini juga
  memungkinkan wilayah kepulauan tetap memiliki tetangga dalam analisis spasial.
"""
)

st.header("Keterbatasan")
st.markdown(
    f"""
- **Baru dua triwulan.** Data 2026 yang tersedia baru Triwulan I dan II, sehingga pertumbuhan *q-to-q*
  masih dapat dipengaruhi pola musiman. Karena data 2025 tidak tersedia dalam tabel yang digunakan,
  pertumbuhan *y-on-y* belum dapat dihitung.
- **Harga konstan 2010.** Penggunaan harga konstan membantu membandingkan perubahan volume ekonomi dari
  waktu ke waktu. Namun, tahun dasar 2010 sudah cukup lama, sehingga struktur harga yang digunakan belum
  mencerminkan kondisi harga terbaru. Akibatnya, komposisi berdasarkan harga berlaku dapat sedikit
  berbeda.
- **Batas wilayah menggunakan kode 2019.** Analisis tetap mencakup {n_reg} kabupaten/kota, tetapi
  pembagian provinsi belum mengikuti pemekaran Papua pada 2022. Karena itu, beberapa wilayah Papua
  masih mengikuti pengelompokan provinsi pada struktur wilayah lama.
- **PC1–PC2 hanya menjelaskan sekitar {idn(pc2, 0)}% variasi.** Posisi dan jarak antardaerah pada biplot
  hanya menggambarkan sebagian struktur data. Karena itu, pola pada dua sumbu tersebut sebaiknya dibaca
  bersama heatmap dan hasil analisis lainnya.
- **Klaster bersifat deskriptif.** Nilai *silhouette* yang rendah menunjukkan bahwa pemisahan
  antarklaster masih lemah. Artinya, batas antar pola ekonomi tidak selalu tegas dan sebagian daerah
  memiliki karakteristik yang berada di antara beberapa pola.
- **LISA belum dikoreksi untuk uji berganda.** Setiap daerah diuji sendiri pada α = 5%, sehingga dari
  {n_reg} daerah sekitar {idn(0.05 * n_reg, 0)} dapat tampak signifikan hanya karena kebetulan. Pada peta
  porsi pertanian, {lisa_sig} daerah signifikan tanpa koreksi; dengan koreksi FDR (Benjamini–Hochberg)
  tinggal {lisa_fdr}. Karena itu, peta LISA dibaca sebagai petunjuk letak kantong yang mengelompok, bukan
  bukti untuk setiap daerah satu per satu. Nilai p terkecil yang mungkin dengan {PERMUTATIONS} permutasi
  adalah {idn(1 / (PERMUTATIONS + 1), 3)}.
"""
)

st.header("Deklarasi penggunaan AI")
st.markdown(
    """
Dalam pengerjaan proyek ini digunakan Claude (Anthropic) dan ChatGPT (OpenAI) sebagai alat bantu pada
tahap pengembangan dan penyuntingan.

- **Penggunaan AI.** AI digunakan untuk membantu penulisan dan perapian kode aplikasi (Streamlit,
  Plotly, dan grafik SVG), penyusunan tampilan halaman, serta penyuntingan dan perapian redaksi.
- **Sumber data dan hasil analisis.** Data yang digunakan berasal dari BPS dan bahan praktikum Sistem
  Informasi Geografis (lihat bagian Sumber). Seluruh angka, grafik, dan peta dihasilkan melalui proses
  pengolahan data dan perhitungan dalam kode.
- **Keputusan analisis.** Pemilihan data, metode, parameter, serta interpretasi hasil ditetapkan oleh
  penulis. AI digunakan sebagai alat bantu dalam implementasi teknis, bukan sebagai pengganti
  pertimbangan penulis.
- **Pemeriksaan.** Kode dan keluaran yang dibantu AI dijalankan, ditinjau, dan diperiksa kembali oleh
  penulis sebelum digunakan. Tanggung jawab atas data, metode, hasil, dan isi proyek tetap berada pada
  penulis.
"""
)

st.header("Unduh data olahan")
long_df = data.long_df()
reg_df = data.regions().reset_index()
# utf-8-sig: BOM agar Excel membaca UTF-8 (tanpa itu "–" tampil sebagai "â€"")
long_csv = long_df.to_csv(index=False).encode("utf-8-sig")
reg_csv = reg_df.to_csv(index=False).encode("utf-8-sig")


def ukuran(b):
    return f"{idn(b / 1024 / 1024, 1)} MB" if b >= 1024 * 1024 else f"{idn(b / 1024, 0)} KB"


with st.container(key="dl-cards"):
    d1, d2 = st.columns(2, gap="medium")
    with d1:
        with st.container(key="dl-h1"):
            st.markdown(":material/database: Data PDRB\n\n**pdrb_long.csv**")
        st.markdown("Nilai PDRB menurut kabupaten/kota, lapangan usaha, dan triwulan, dalam miliar rupiah atas "
                    "dasar harga konstan 2010.")
        st.html(f'<p class="dl-meta">{idn(len(long_df), 0)} baris · TOTAL PDRB BPS tersedia · '
                f'±{ukuran(len(long_csv))}</p>')
        st.download_button("Unduh data PDRB", long_csv, file_name="pdrb_long.csv", mime="text/csv",
                           icon=":material/download:", use_container_width=True)
    with d2:
        with st.container(key="dl-h2"):
            st.markdown(":material/map: Data wilayah\n\n**wilayah.csv**")
        st.markdown("Data kabupaten/kota dengan kode wilayah, provinsi, pulau, jenis daerah, koordinat, dan luas "
                    "wilayah. Digabungkan dengan data PDRB menggunakan kode wilayah.")
        st.html(f'<p class="dl-meta">{idn(len(reg_df), 0)} daerah · ±{ukuran(len(reg_csv))}</p>')
        st.download_button("Unduh data wilayah", reg_csv, file_name="wilayah.csv", mime="text/csv",
                           icon=":material/download:", use_container_width=True)
# Kredit pembuat ada di footer global (ui.footer), yang tampil di semua halaman.
