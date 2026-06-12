from flask import Flask, render_template, jsonify, send_from_directory, session, redirect, url_for, request
# from logic import load_geojson # Memanggil fungsi dari logic.py
import pandas as pd # Pastikan sudah install: pip install pandas
import os
from logic import get_detail_from_csv, load_geojson, get_stats_from_csv
import json


app = Flask(__name__)
app.secret_key = 'bappeda_badung_secret_key'

# Tentukan path absolut ke folder file unduhan
DOWNLOAD_FOLDER = os.path.join(app.root_path, 'static', 'lulc')

# ==========================================
# KONFIGURASI NOTIFIKASI EMAIL (SMTP GMAIL)
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-gmail@gmail.com"     # Ganti dengan Gmail Anda (pengirim)
SENDER_PASSWORD = "your-app-password"    # Ganti dengan Gmail App Password Anda
RECEIVER_EMAIL = "your-gmail@gmail.com"  # Ganti dengan Gmail Anda (penerima)


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

@app.route('/api/spatial-query/<year>', methods=['POST'])
def api_spatial_query(year):
    try:
        from flask import request
        req_data = request.get_json()
        if not req_data or 'geometry' not in req_data:
            return jsonify({"error": "Data geometri tidak valid atau kosong"}), 400
        
        from logic import query_spatial_intersection
        result = query_spatial_intersection(year, req_data['geometry'])
        
        if "error" in result:
            return jsonify(result), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dss')
def analisis_dss():
    return render_template('dss.html')

@app.route('/api/conflict/<year>')
def api_conflict(year):
    try:
        from logic import get_conflict_data
        result = get_conflict_data(year)
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/vulnerability')
def api_vulnerability():
    try:
        from logic import get_vulnerability_data
        result = get_vulnerability_data()
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/demography/<year>')
def api_demography(year):
    try:
        from logic import get_demographic_stats
        result = get_demographic_stats(year)
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dss/ews')
def api_dss_ews():
    try:
        from logic import calculate_ews_status
        result = calculate_ews_status()
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dss/report/<kecamatan>')
def dss_report_download(kecamatan):
    try:
        import io
        from flask import send_file
        from logic import generate_pdf_report
        
        pdf_buffer = io.BytesIO()
        result = generate_pdf_report(kecamatan, pdf_buffer)
        
        if "error" in result:
            return jsonify(result), 500
            
        pdf_buffer.seek(0)
        formatted_name = f"Laporan_DSS_{kecamatan.replace(' ', '_')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=formatted_name
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/report-violation', methods=['POST'])
def api_report_violation():
    try:
        from flask import request
        from werkzeug.utils import secure_filename
        import db_helper
        from logic import send_email_notification
        
        # Parse fields
        nama_pelapor = request.form.get('nama_pelapor')
        kontak = request.form.get('kontak')
        kecamatan = request.form.get('kecamatan')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        deskripsi = request.form.get('deskripsi')
        
        if not all([nama_pelapor, kontak, kecamatan, latitude, longitude, deskripsi]):
            return jsonify({"error": "Semua kolom laporan wajib diisi."}), 400
            
        # Handle file upload
        foto_filename = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                # Ensure directory exists
                upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'reports')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Secure and generate unique filename
                import uuid
                ext = os.path.splitext(file.filename)[1]
                foto_filename = f"report_{uuid.uuid4().hex}{ext}"
                file.save(os.path.join(upload_dir, foto_filename))
                
        # Insert into SQLite Database
        db_res = db_helper.insert_report(
            nama_pelapor=nama_pelapor,
            kontak=kontak,
            kecamatan=kecamatan,
            latitude=latitude,
            longitude=longitude,
            deskripsi=deskripsi,
            foto_filename=foto_filename
        )
        
        if "error" in db_res:
            return jsonify({"error": "Gagal menyimpan laporan di database: " + db_res["error"]}), 500
            
        # Send Email Notification in the background
        report_data = {
            "id": db_res["id"],
            "nama_pelapor": nama_pelapor,
            "kontak": kontak,
            "kecamatan": kecamatan,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "deskripsi": deskripsi,
            "foto_filename": foto_filename
        }
        send_email_notification(report_data)
        
        return jsonify({
            "success": True, 
            "message": "Laporan pengaduan berhasil disimpan di database lokal dan sedang dikirim ke email Bappeda."
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/count')
def api_reports_count():
    try:
        import db_helper
        res = db_helper.get_all_reports()
        if "error" in res:
            return jsonify({"count": 0})
        return jsonify({"count": len(res.get("data", []))})
    except Exception:
        return jsonify({"count": 0})

@app.route('/download/<filename>')
def download_file(filename):
    # as_attachment=True memaksa file otomatis terunduh di komputer user
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


# ==========================================
# AUTHENTICATION & ADMIN PORTAL
# ==========================================
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'adminbappeda'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Kredensial salah. Silakan coba lagi.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('beranda'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    import db_helper
    res = db_helper.get_all_reports()
    reports = res.get("data", []) if "error" not in res else []
    return render_template('admin_dashboard.html', reports=reports)

@app.route('/api/reports/update-status', methods=['POST'])
def api_update_report_status():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        data = request.get_json()
        if not data:
            # Handle standard form data
            report_id = request.form.get('id')
            status = request.form.get('status')
        else:
            report_id = data.get('id')
            status = data.get('status')
            
        if not report_id or not status:
            return jsonify({"error": "Missing parameter id atau status"}), 400
            
        import db_helper
        res = db_helper.update_report_status(report_id, status)
        if "error" in res:
            return jsonify(res), 500
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Tambahkan port=5001 di dalam kurung
    app.run(debug=True, port=5001)