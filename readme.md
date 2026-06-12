# 🗺️ WebGIS Monitoring & Prediksi Alih Fungsi Lahan Kabupaten Badung (2015 - 2030)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-blueviolet.svg)](https://tailwindcss.com/)

Platform Sistem Pendukung Keputusan (*Decision Support System*) berbasis **WebGIS** yang mengintegrasikan hasil klasifikasi objek *Machine Learning* **Random Forest** (data historis multitemporal 2015, 2020, 2025) dan proyeksi spasial **Cellular Automata - Markov Chain** (2030) untuk mendeteksi serta memitigasi kerentanan konversi lahan sawah produktif di Kabupaten Badung, Bali.

---

## 🚀 Fitur Utama Aplikasi

1. **Dashboard Beranda Interaktif (`beranda.html`)**: Menyajikan metrik ringkas laju alih fungsi lahan historis, visualisasi statistik krisis wilayah, dan panduan operasional sistem sekuensial.
2. **Kanvas Pemetaan Dinamis (`peta.html`)**:
   * **Temporal Selector**: Mengaktifkan data spasial LULC komposit lima kelas dari tahun 2015 hingga proyeksi 2030 berbasis file GeoJSON.
   * **Interactive Class Filter (*Per Layer Mode*)**: Mengisolasi visualisasi khusus kelas *Lahan Sawah Saja* atau *Lahan Terbangun Saja* guna menganalisis karakteristik fragmentasi dan *urban sprawl*.
   * **Spatial Overlap (*Hotspot Detection*)**: Operasi logika matriks biner untuk memetakan wilayah benturan di mana sawah terkonversi secara agresif.
   * **GeoTIFF Raster Extraction**: Fitur unduh berkas master spasial GeoTIFF asli langsung dari antarmuka web untuk pemrosesan lanjutan pada Desktop GIS.
3. **Analisis Statistik & Mitigasi (`statistik.html`)**: Diagram batang/lingkaran interaktif berbasis area piksel dan tabel penyaringan data tabular sisi klien (client-side) berdasarkan Tahun dan Kecamatan.

---

## 🛠️ Stack Teknologi

* **Backend Framework**: Python (Flask)
* **Frontend UI**: Tailwind CSS, HTML5, Vanilla JavaScript, Jinja2 Template Engine
* **Peta Interaktif Engine**: Leaflet.js Mapping Library
* **Pengolahan & Komputasi Spasial**: Google Earth Engine (GEE) API, QGIS Desktop

---

## 📦 Prasyarat Sistem & Instalasi

Pastikan perangkat Anda telah terpasang **Python 3.9** atau versi di atasnya.

### 1. Kloning Proyek
Buka terminal/command prompt Anda dan jalankan perintah berikut:
```bash
git clone [https://github.com/username/repo-webgis-badung.git](https://github.com/username/repo-webgis-badung.git)
cd repo-webgis-badung