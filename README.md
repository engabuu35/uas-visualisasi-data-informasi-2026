# Satu Negeri, 514 Wajah Ekonomi

Visualisasi interaktif struktur, konsentrasi, pertumbuhan, dan pola spasial PDRB 514 kabupaten/kota di Indonesia berdasarkan data PDRB triwulanan 2026 dari Badan Pusat Statistik (BPS).

Proyek UAS Visualisasi Data dan Informasi, Program Studi Komputasi Statistik, Politeknik Statistika STIS.

- **Aplikasi:** https://514-wajah-ekonomi.streamlit.app/
- **Repositori:** https://github.com/engabuu35/uas-visualisasi-data-informasi-2026

## Isi Aplikasi

Aplikasi mengadopsi pola *martini glass* [1], yaitu alur cerita yang dipandu pada bagian awal kemudian dilanjutkan dengan halaman eksplorasi interaktif.

| Halaman | Topik visualisasi | Teknik |
|---|---|---|
| **Potret PDRB** | Narasi | *Scrollytelling* 4 babak, grafik SVG, kurva konsentrasi, profil klaster, pertumbuhan, peta LISA, tooltip, dan interaksi pendukung |
| **Pola ekonomi** | Multivariat | PCA biplot, *parallel coordinates*, heatmap terklaster (Ward), profil klaster, pencilan Mahalanobis, serta *brushing and linking* |
| **Peta** | Geospasial | Choropleth rasio (pangsa, LQ, pertumbuhan), simbol proporsional, kontrol lapisan, zoom/pan, perbesaran ke provinsi, Moran's I, dan peta LISA |
| **Wilayah & sektor** | Berhierarki | Treemap dan icicle dengan 5 tingkat: Indonesia → pulau → provinsi → kabupaten/kota → sektor; ukuran = PDRB, warna = pertumbuhan; *drill-down* dan *breadcrumb* |
| **Data & metode** | Dokumentasi | Sumber data, pra-pemrosesan, rumus, metode, keterbatasan, dan unduhan data olahan |

## Pemenuhan Ketentuan Minimal

### Multivariat

- 17 variabel numerik berupa pangsa 17 lapangan usaha dan 514 unit observasi.
- Satu teknik reduksi dimensi (PCA) dan dua teknik tambahan, yaitu *parallel coordinates* dan heatmap terklaster.
- Seleksi laso/kotak pada biplot memperbarui profil daerah, *parallel coordinates*, dan heatmap secara bersamaan.
- Klaster dan pencilan ditampilkan dan diinterpretasikan pada aplikasi.

### Geospasial

- Mencakup 514 kabupaten/kota.
- Choropleth digunakan untuk variabel rasio, yaitu pangsa, LQ, dan pertumbuhan.
- Nilai PDRB absolut ditampilkan menggunakan simbol proporsional.
- Tersedia beberapa metode klasifikasi, tooltip, legenda, zoom/pan, kontrol lapisan, dan perbesaran ke provinsi.
- Moran's I, Moran scatterplot, dan peta LISA digunakan sebagai analisis spasial tambahan.

### Hierarki

- Lima tingkat: Indonesia, pulau, provinsi, kabupaten/kota, dan sektor.
- Dua representasi: treemap dan icicle.
- Ukuran mengodekan PDRB dan warna mengodekan pertumbuhan *q-to-q*.
- *Drill-down* dilengkapi dengan *breadcrumb*.

## Data

| Informasi | Keterangan |
|---|---|
| **Tabel** | *PDRB Triwulanan Atas Dasar Harga Konstan (2010=100) Menurut 17 Kategori Lapangan Usaha di Kabupaten/Kota (Milyar Rupiah), 2026* |
| **Penerbit** | Badan Pusat Statistik |
| **URL** | https://www.bps.go.id/id/statistics-table/2/Mjc3NSMy/pdrb-triwulanan-atas-dasar-harga-konstan-2010-100-menurut-17-kategori-lapangan-usaha-di-kabupaten-kota-milyar-rupiah.html |
| **Tanggal akses** | 27 September 2026 |
| **Periode terisi** | Triwulan I dan II 2026 |
| **Data pendukung** | Batas wilayah kabupaten/kota dari bahan praktikum Sistem Informasi Geografis, Dr. Rindang Bangun Prasetyo, Politeknik Statistika STIS; data pendukung non-BPS dengan kode wilayah tahun 2019 |

## Struktur Proyek

```text
app.py                      # navigasi utama aplikasi

views/
  cerita.py                 # alur cerita (scrollytelling 4 babak)
  struktur.py               # visualisasi multivariat
  peta.py                   # visualisasi geospasial
  hierarki.py               # visualisasi berhierarki
  tentang.py                # data dan metode

src/
  config.py                 # konfigurasi sumber, sektor, wilayah, dan tema
  preprocess.py             # pengolahan data dan indikator turunan
  analysis.py               # PCA, Ward, Mahalanobis, klasifikasi, Moran/LISA
  charts.py                 # grafik Plotly
  data.py                   # pemuatan dan cache data
  ui.py                     # elemen antarmuka bersama
  story.py                  # sumber angka halaman cerita
  story_svg.py              # grafik SVG halaman cerita

assets/
  story.css                 # gaya halaman cerita
  story.js                  # perilaku scrollytelling

scripts/
  prepare_data.py           # pra-pemrosesan data

data/
  raw/                      # data mentah BPS
  geo/                      # data batas wilayah
  processed/                # data hasil pra-pemrosesan
```

## Menjalankan Secara Lokal

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/prepare_data.py
streamlit run app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/prepare_data.py
streamlit run app.py
```

Data pada `data/processed/` telah disertakan dalam repositori sehingga aplikasi yang telah dideploy tidak perlu menjalankan proses pra-pemrosesan ulang.

## Deployment

Aplikasi dideploy menggunakan **Streamlit Community Cloud** dan dapat diakses secara publik tanpa instalasi maupun login.

Konfigurasi deployment menggunakan:

- repository publik GitHub
- branch `main`
- entry point `app.py`
- dependensi dari `requirements.txt`

## Pra-pemrosesan

1. Tabel BPS dalam format lebar diubah menjadi format panjang. Tanda `-` yang menunjukkan data belum tersedia diperlakukan sebagai nilai kosong, kemudian hanya Triwulan I dan II yang digunakan.
2. Kode kategori dipisahkan dari nama kategori. Baris PDRB diberi kode `TOTAL` agar tidak tertukar dengan kategori P (Jasa Pendidikan).
3. Data PDRB dicocokkan dengan data batas wilayah dan divalidasi agar seluruh 514 kabupaten/kota dapat dipetakan.
4. Pemeriksaan kualitas menunjukkan tidak terdapat nilai kosong pada Triwulan I–II dan terdapat 112 sel bernilai nol. Selisih antara jumlah 17 sektor dan baris total PDRB BPS paling besar 0,02%, terutama akibat pembulatan.
5. Geometri batas wilayah disederhanakan menggunakan algoritme Douglas–Peucker [2] dengan toleransi 0,01° untuk mengurangi ukuran data geospasial dari 42 MB menjadi sekitar 1,1 MB.

## Metode dan Indikator

- Analisis multivariat menggunakan **pangsa sektor**, bukan nilai rupiah, sehingga yang dibandingkan adalah struktur ekonomi antardaerah. Pangsa kemudian distandardisasi dengan *z-score* sebelum PCA dan pengelompokan Ward.
- Jumlah klaster ditentukan berdasarkan nilai *silhouette* pada rentang \(k=3\)–8 dan dipilih \(k=6\).
- Pencilan multivariat ditandai menggunakan jarak Mahalanobis kuadrat pada komponen utama yang mencakup sedikitnya 80% varians.
- Bobot spasial menggunakan enam tetangga terdekat berdasarkan jarak haversine dan distandardisasi per baris. Moran's I dan LISA dievaluasi menggunakan 999 permutasi.
- Pertumbuhan *q-to-q* dihitung dari perubahan jumlah PDRB antara Triwulan I dan Triwulan II pada setiap simpul, termasuk daerah, pulau, nasional, dan tingkat sektor. Perhitungan tidak dilakukan jika nilai pada Triwulan I sama dengan nol.
- Treemap dan icicle menampilkan PDRB melalui ukuran dan pertumbuhan melalui warna. Porsi dan pertumbuhan juga ditampilkan sebagai label sehingga informasi tidak hanya bergantung pada warna.
- Setiap visualisasi memiliki judul, satuan, dan keterangan **“Sumber: BPS”**.

## Aksesibilitas

Aplikasi mendukung tema terang dan gelap serta menyediakan panel **Aksesibilitas** untuk mengatur ukuran teks, menghentikan animasi, dan memilih palet.

Palet dipilih dengan mempertimbangkan keterbatasan penglihatan warna. Untuk mengurangi ketergantungan pada warna, visualisasi klaster juga menggunakan bentuk, label, atau legenda. Cividis dan Okabe–Ito digunakan sebagai salah satu rujukan pemilihan palet [3], [4].

## Catatan Penting

- Halaman **Potret PDRB** menggunakan *scrollytelling* empat babak: Konsentrasi PDRB → Pola Ekonomi → Pertumbuhan → Perubahan Kontribusi.
- Angka yang digunakan pada halaman cerita berasal dari modul data yang sama sehingga angka pada narasi dan visualisasi konsisten.
- Data utama berasal dari BPS. Batas wilayah merupakan data pendukung non-BPS.
- Untuk analisis struktur ekonomi, pangsa sektor digunakan agar perbandingan tidak didominasi oleh perbedaan ukuran ekonomi antarwilayah.

## Keterbatasan

- Data yang tersedia baru mencakup dua triwulan sehingga pertumbuhan *q-to-q* masih dapat dipengaruhi pola musiman.
- PDRB menggunakan tahun dasar 2010, sedangkan data batas wilayah menggunakan kode tahun 2019 sehingga pemekaran provinsi di Papua belum tercermin.
- PC1 dan PC2 hanya menjelaskan sekitar 39% varians sehingga interpretasi kedekatan antardaerah pada biplot perlu dilengkapi dengan heatmap.
- Hasil LISA belum dikoreksi untuk pengujian berganda pada visualisasi utama. Pada peta porsi pertanian, 167 dari 514 daerah signifikan sebelum koreksi dan 42 setelah koreksi FDR Benjamini–Hochberg.
- Biplot dengan 514 titik masih cukup padat pada layar ponsel sehingga menu **Sorot** disediakan sebagai alternatif seleksi langsung.

## Lisensi dan Sumber

Data utama PDRB bersumber dari **Badan Pusat Statistik (BPS)**.

Data batas wilayah digunakan sebagai data pendukung non-BPS dari bahan praktikum Sistem Informasi Geografis, Politeknik Statistika STIS.

Proyek ini dibuat untuk keperluan UAS Visualisasi Data dan Informasi.