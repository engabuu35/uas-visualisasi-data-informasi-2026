# Satu Negeri, 514 Wajah Ekonomi

Visualisasi struktur ekonomi 514 kabupaten/kota di Indonesia berdasarkan PDRB triwulanan 2026 dari BPS.
Proyek UAS Visualisasi Data dan Informasi, Politeknik Statistika STIS.

**Aplikasi:** _(isi URL Streamlit Community Cloud)_
**Repositori:** _(isi URL GitHub)_

## Isi aplikasi

Aplikasi disusun dengan pola *martini glass* (Segel & Heer, 2010). Pembaca diajak mengikuti satu alur
cerita lebih dulu, lalu dipersilakan menjelajah sendiri.

| Halaman | Topik ujian | Teknik |
|---|---|---|
| **Potret PDRB** | narasi | scrollytelling 4 babak, SVG buatan tangan: kurva konsentrasi, dumbbell + small multiples klaster, batang pertumbuhan, peta LISA; tooltip dan crosshair |
| **Pola ekonomi** | (a) multivariat | PCA biplot, parallel coordinates, heatmap terklaster (Ward), profil klaster, pencilan Mahalanobis; *brushing & linking* dari biplot ke semua tampilan |
| **Peta** | (e) geospasial | choropleth rasio (pangsa / LQ / pertumbuhan) dengan 3 metode klasifikasi, simbol proporsional, kontrol lapisan, zoom ke provinsi, Moran's I + peta LISA |
| **Wilayah & sektor** | (c) berhierarki | treemap dan icicle 5 tingkat (Indonesia → pulau → provinsi → kab/kota → sektor, atau dibalik); ukuran = PDRB, warna = pertumbuhan; breadcrumb |
| **Data & metode** | – | sumber, pra-pemrosesan, rumus, keterbatasan, unduhan data olahan |

Ketentuan minimal Lampiran A yang dipenuhi:

- **Multivariat.** Ada 17 variabel numerik dan 514 unit observasi. Reduksi dimensinya PCA, ditambah
  parallel coordinates dan heatmap terklaster. Seleksi laso/kotak pada biplot langsung memperbarui
  profil, tabel, parallel coordinates, dan heatmap. Klaster dan pencilan diberi interpretasi.
- **Geospasial.** Mencakup 514 kab/kota. Ada tiga jenis peta: choropleth, simbol proporsional, dan LISA.
  Choropleth hanya memakai rasio. Metode klasifikasi dijelaskan di bawah peta. Tersedia tooltip,
  legenda, zoom/pan, dan kontrol lapisan, ditambah Moran's I.
- **Hierarki.** Ada lima tingkat dan dua representasi (treemap, icicle). Ukuran dan warna mewakili dua
  variabel yang berbeda. Drill-down dilengkapi breadcrumb (pathbar).

## Data

| | |
|---|---|
| Tabel | PDRB Triwulanan Atas Dasar Harga Konstan (2010=100) Menurut 17 Kategori Lapangan Usaha di Kabupaten/Kota (Milyar Rupiah), 2026 |
| Penerbit | Badan Pusat Statistik |
| URL | https://www.bps.go.id/id/statistics-table/2/Mjc3NSMy/pdrb-triwulanan-atas-dasar-harga-konstan-2010-100-menurut-17-kategori-lapangan-usaha-di-kabupaten-kota-milyar-rupiah.html |
| Diakses | 27 September 2026 |
| Cakupan terisi | Triwulan I dan II 2026 |
| Batas wilayah | Bahan praktikum Sistem Informasi Geografis, Dr. Rindang Bangun Prasetyo, Politeknik Statistika STIS (data pendukung non-BPS, kode wilayah BPS 2019). |

## Struktur

```text
app.py                      navigasi halaman
views/
  cerita.py                 alur cerita (scrollytelling 4 babak)
  struktur.py               multivariat
  peta.py                   geospasial
  hierarki.py               hierarki
  tentang.py                data & metode
src/
  config.py                 sumber, sektor, provinsi, palet warna
  preprocess.py             membaca tabel BPS, pangsa, LQ, pertumbuhan
  analysis.py               PCA, Ward, Mahalanobis, Jenks, Moran/LISA, hierarki
  charts.py                 semua figur Plotly
  data.py                   cache Streamlit
  ui.py                     elemen tampilan bersama
  story.py                  satu-satunya sumber angka halaman Cerita
  story_svg.py              grafik dan peta SVG halaman Cerita
assets/story.css, story.js  gaya dan perilaku scrollytelling
scripts/prepare_data.py     pra-pemrosesan (jalankan sekali)
data/raw/pdrb_2026.xlsx     unduhan asli BPS
data/geo/kabkota.geojson    batas wilayah asli (42 MB)
data/processed/             hasil pra-pemrosesan
```

## Menjalankan

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
python scripts/prepare_data.py  # membuat data/processed/*
streamlit run app.py
```

`data/processed/` ikut di-commit sehingga Streamlit Cloud tidak perlu menjalankan skrip pra-pemrosesan.

## Deploy (Streamlit Community Cloud)

1. Push repositori ini ke GitHub (publik).
2. Di [share.streamlit.io](https://share.streamlit.io), pilih **Create app** → repositori ini, cabang
   `main`, berkas utama `app.py`. Dependensi dibaca dari `requirements.txt`.
3. Setelah aplikasi aktif, isi URL aplikasi dan repositori di bagian atas README ini.

## Pra-pemrosesan

1. Tabel lebar BPS (17 kategori + PDRB × 5 periode) diubah ke format panjang. Tanda "-" dijadikan
   kosong, lalu hanya TW I dan TW II yang dipakai.
2. Kode kategori dipisahkan dari namanya (`A`, `M,N`, `R,S,T,U`). Baris PDRB diberi kode `TOTAL`
   agar tidak tertukar dengan kategori P (Jasa Pendidikan).
3. Data digabung dengan kode wilayah melalui nama kab/kota. Ke-514 nama cocok satu lawan satu.
4. Pemeriksaan kualitas: tidak ada nilai kosong dan ada 112 sel bernilai nol. Selisih jumlah 17
   sektor dengan baris PDRB paling besar 0,02%, karena pembulatan.
5. Geometri disederhanakan dengan Douglas–Peucker (0,01°) dari 42 MB menjadi 1,1 MB. Titik pusat
   diambil dengan `representative_point()` dan luas dihitung dengan pendekatan equal-area.

## Catatan metode

- Analisis multivariat memakai **pangsa** sektor (%), bukan nilai rupiah, supaya yang dibandingkan
  adalah struktur ekonomi, bukan ukuran daerah. Pangsa distandardisasi (z-score) sebelum PCA dan Ward.
- Jumlah klaster 6 dipilih karena silhouette Ward-nya tertinggi pada k = 3–8.
- Pencilan ditentukan dengan Mahalanobis D² pada PC yang mencakup ≥ 80% varians, dengan ambang
  χ²(0,99).
- Bobot spasial memakai 6 tetangga terdekat (haversine), distandardisasi baris, karena banyak
  wilayah berupa pulau. LISA diuji dengan 999 permutasi bersyarat. Bila ada daerah yang dikeluarkan
  (pertumbuhan dari basis nol), permutasi menarik sebanyak tetangga yang tersisa pada tiap daerah.
- Pertumbuhan dihitung dari jumlah nilai (ΣTW II/ΣTW I − 1) untuk simpul hierarki, pulau, nasional,
  dan "semua sektor" di peta. Totalnya selalu jumlah 17 sektor (bukan baris PDRB BPS), sama seperti
  penyebut pangsa. Rumus lengkap ada di halaman Data & metode.
- Treemap dan icicle menuliskan porsi dan pertumbuhan di setiap kotak, sehingga pertumbuhan tidak
  hanya dibaca dari warna. Warna teks label dipilih hitam atau putih per kotak (kontras ≥ 4,5:1).
- Setiap grafik punya judul yang menyebut isi dan satuannya, serta baris "Sumber: BPS" berisi judul
  tabel, tautan, dan tanggal akses.
- Halaman Cerita adalah scrollytelling empat babak (Konsentrasi PDRB → Pola Ekonomi → Pertumbuhan → Pergeseran)
  dengan grafik SVG buatan tangan (`src/story_svg.py`). Semua angka di teks berasal dari satu modul
  data (`src/story.py`); tidak ada angka yang diketik di templat. SVG dikirim lewat skrip karena
  sanitizer `st.html` membuang elemen `<svg>`.
- Tema terang & gelap: `.streamlit/config.toml` mendefinisikan `[theme.light]` dan `[theme.dark]`;
  bawaannya mengikuti sistem dan bisa diganti lewat menu ⋮. Semua warna ada di `src/theme.py`.
  Karena Streamlit tidak rerun saat tema diganti, `theme.sync()` memasang komponen kecil yang
  membaca tema yang tampil, mengganti variabel CSS seketika, dan memicu satu rerun agar grafik
  Plotly dan SVG digambar ulang.
- Tombol **Aksesibilitas** di tepi kiri memuat ukuran teks, opsi hentikan animasi, dan pilihan palet.
  Kedua palet ramah buta warna:

  | | Kategorikal (klaster) | Sekuensial (besaran) | Divergen (LQ, pertumbuhan) | LISA |
  |---|---|---|---|---|
  | Viridis (bawaan) | palet rujukan tervalidasi (langkah terang/gelap) | Viridis | biru ↔ jingga | jingga / biru |
  | Okabe-Ito / Cividis | Okabe-Ito (urutan hasil enumerasi) | Cividis | merah ↔ biru (RdBu) | merah / biru |

  Klaster selalu memakai penanda kedua (bentuk, label, legenda bernama, small multiples).

## Keterbatasan

- Datanya baru dua triwulan, sehingga pertumbuhan q-to-q masih bercampur pola musiman.
- Harga konstan memakai tahun dasar 2010. Batas wilayah memakai kode 2019, sebelum pemekaran Papua.
- PC1–PC2 hanya menjelaskan ±39% varians.
- LISA belum dikoreksi untuk uji berganda. Pada peta porsi pertanian, 167 dari 514 daerah signifikan
  tanpa koreksi dan 42 dengan koreksi FDR (Benjamini–Hochberg); peta LISA dibaca sebagai petunjuk
  letak kantong, bukan bukti per daerah.
- Di ponsel, biplot 514 titik menjadi padat; menu "Sorot" disediakan sebagai pengganti laso.
  Kotak treemap yang sangat kecil memakai teks yang diperkecil otomatis; rinciannya ada di tooltip.
