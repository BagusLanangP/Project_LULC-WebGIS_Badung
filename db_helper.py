import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Supaya data bisa dibaca sebagai dict
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_pelapor TEXT NOT NULL,
            kontak TEXT NOT NULL,
            kecamatan TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            deskripsi TEXT NOT NULL,
            foto_filename TEXT,
            tanggal TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Menunggu Verifikasi'
        )
    ''')
    conn.commit()

    # Migrasi jika kolom status belum ada
    try:
        cursor.execute("PRAGMA table_info(reports)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'status' not in cols:
            cursor.execute("ALTER TABLE reports ADD COLUMN status TEXT DEFAULT 'Menunggu Verifikasi'")
            conn.commit()
            print("Database reports berhasil dimigrasi dengan kolom status.")
    except Exception as e:
        print(f"Gagal migrasi database: {e}")

    conn.close()
    print("Database SQLite berhasil diinisialisasi.")

def insert_report(nama_pelapor, kontak, kecamatan, latitude, longitude, deskripsi, foto_filename=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reports (nama_pelapor, kontak, kecamatan, latitude, longitude, deskripsi, foto_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nama_pelapor, kontak, kecamatan, float(latitude), float(longitude), deskripsi, foto_filename))
        conn.commit()
        report_id = cursor.lastrowid
        conn.close()
        return {"success": True, "id": report_id}
    except Exception as e:
        print(f"Error insert SQLite: {e}")
        return {"error": str(e)}

def get_all_reports():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reports ORDER BY tanggal DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to a list of dicts
        reports_list = []
        for row in rows:
            reports_list.append(dict(row))
        return {"data": reports_list}
    except Exception as e:
        return {"error": str(e)}

def update_report_status(report_id, status):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE reports SET status = ? WHERE id = ?', (status, int(report_id)))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        print(f"Error update status SQLite: {e}")
        return {"error": str(e)}

# Jalankan inisialisasi tabel saat db_helper diimpor pertama kali
init_db()
