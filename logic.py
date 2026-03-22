import json
import os
import pandas as pd

def load_geojson(year):
    # Mencari file di folder static/data
    file_path = f'static/data/lulc/lulc_{year}.geojson'
    if os.path.exists(file_path):
        with open(file_path) as f:
            return json.load(f)
    return None

def get_stats_from_csv(year):
    try:
        # Load data CSV Abang
        df = pd.read_csv('static/data/csv/luasan_badung.csv') # Pastikan nama file sesuai
        
        # Filter berdasarkan tahun yang dipilih slider
        df_year = df[df['Tahun'] == int(year)]
        
        # Kelompokkan berdasarkan Kelas_Lahan dan jumlahkan Luas_Ha
        summary = df_year.groupby('Kelas_Lahan')['Luas_Ha'].sum().to_dict()
        
        # Mapping hasil ke ID yang ada di HTML
        return {
            "terbangun": f"{summary.get('Lahan Terbangun', 0):,.2f} Ha",
            "sawah": f"{summary.get('Lahan Sawah', 0):,.2f} Ha",
            "vegetasi": f"{summary.get('Lahan Vegetasi Lainnya', 0):,.2f} Ha",
            "terbuka": f"{summary.get('Lahan Terbuka', 0):,.2f} Ha",
            "air": f"{summary.get('Badan Air', 0):,.2f} Ha"
        }
    except Exception as e:
        return {"error": str(e)}
    

# Tambahkan fungsi ini di bagian paling bawah logic.py

def get_detail_from_csv(year):
    try:
        df = pd.read_csv('static/data/csv/luasan_badung.csv')
        # Ambil data sesuai tahun saja
        df_year = df[df['Tahun'] == int(year)]
        
        # Ubah data tabel menjadi format kamus (dictionary) yang bisa dibaca Javascript
        # Orient 'records' akan membuat format seperti: [{'Kecamatan': 'Kuta', 'Kelas_Lahan': 'Sawah', 'Luas_Ha': 120}, ...]
        records = df_year[['Kecamatan', 'Kelas_Lahan', 'Luas_Ha']].to_dict(orient='records')
        
        return {"data": records}
    except Exception as e:
        return {"error": str(e)}