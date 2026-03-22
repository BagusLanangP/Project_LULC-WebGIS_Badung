from flask import Flask, render_template, jsonify
# from logic import load_geojson # Memanggil fungsi dari logic.py
import pandas as pd # Pastikan sudah install: pip install pandas
import os
from logic import get_detail_from_csv, load_geojson, get_stats_from_csv
import json

app = Flask(__name__)

@app.route('/')
def beranda():
    return render_template('beranda.html')

@app.route('/peta')
def peta_interaktif():
    return render_template('peta.html')

@app.route('/statistik')
def analisis_statistik():
    return render_template('statistik.html')

@app.route('/api/stats/<year>')
def api_stats(year):
    try:
        # Pastikan file CSV Abang ada di folder static/data/
        file_path = os.path.join('static', 'data', 'csv', 'luasan_badung.csv')
        
        # Baca CSV dengan Pandas
        df = pd.read_csv(file_path)
        
        # Filter hanya tahun yang dipilih slider
        df_year = df[df['Tahun'] == int(year)]
        
        # Jumlahkan Luas_Ha berdasarkan Kelas_Lahan (untuk 1 Kabupaten)
        summary = df_year.groupby('Kelas_Lahan')['Luas_Ha'].sum().to_dict()
        
        # Kirim format JSON ke HTML
        return jsonify({
            "air": f"{summary.get('Badan Air', 0):,.2f} Ha",
            "terbangun": f"{summary.get('Lahan Terbangun', 0):,.2f} Ha",
            "terbuka": f"{summary.get('Lahan Terbuka', 0):,.2f} Ha",
            "sawah": f"{summary.get('Lahan Sawah', 0):,.2f} Ha",
            "vegetasi": f"{summary.get('Lahan Vegetasi Lainnya', 0):,.2f} Ha",
        })
    except Exception as e:
        print(f"Error baca CSV: {e}")
        return jsonify({"error": "Gagal membaca data CSV"}), 500

@app.route('/api/geojson/<year>')
def api_geojson(year):
    try:
        # Flask akan mencari file misal: static/data/lulc_2030.geojson
        file_path = os.path.join('static', 'data', 'lulc', f'lulc_{year}.geojson')
        
        if not os.path.exists(file_path):
            return jsonify({"error": f"File lulc_{year}.geojson tidak ditemukan"}), 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
        
    except Exception as e:
        print(f"Error baca GeoJSON: {e}")
        return jsonify({"error": "Gagal membaca GeoJSON"}), 500
    
@app.route('/api/detail/<year>')
def api_detail(year):
    # Pelayan meminta koki mengambil data detail per kecamatan
    data = get_detail_from_csv(year)
    
    if "error" in data:
        return jsonify(data), 500
        
    return jsonify(data)

if __name__ == '__main__':
    # Tambahkan port=5001 di dalam kurung
    app.run(debug=True, port=5001)