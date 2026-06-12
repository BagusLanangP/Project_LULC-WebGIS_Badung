import json
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape

GDF_CACHE = {}

def get_cached_gdf(year):
    if year not in GDF_CACHE:
        file_path = os.path.join('static', 'data', 'lulc', f'lulc_{year}.geojson')
        if os.path.exists(file_path):
            GDF_CACHE[year] = gpd.read_file(file_path)
        else:
            return None
    return GDF_CACHE[year]


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


def query_spatial_intersection(year, geojson_geom):
    gdf = get_cached_gdf(year)
    if gdf is None:
        return {"error": f"GeoJSON data untuk tahun {year} tidak ditemukan"}
    
    try:
        # Convert GeoJSON geometry to Shapely geometry
        geom = shape(geojson_geom)
        
        # Create a temporary GeoDataFrame for query geometry
        query_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[geom])
        
        # Project both to local metric UTM 50S for accurate area calculation in Bali
        gdf_proj = gdf.to_crs(epsg=32750)
        query_proj = query_gdf.to_crs(epsg=32750)
        
        # Perform overlay intersection
        intersection = gpd.overlay(gdf_proj, query_proj, how='intersection')
        if intersection.empty:
            return {"data": {}}
        
        # Determine correct class column name
        class_col = 'Kelas_Lahan' if 'Kelas_Lahan' in intersection.columns else 'kelas'
        
        # Calculate area of each intersected geometry in Hectares (area in sq meters / 10,000)
        intersection['area_ha'] = intersection.geometry.area / 10000.0
        
        # Group by land cover class and sum areas
        summary = intersection.groupby(class_col)['area_ha'].sum().to_dict()
        
        # Round values for nice display
        formatted_summary = {str(k): round(float(v), 2) for k, v in summary.items()}
        
        return {"data": formatted_summary}
    except Exception as e:
        print(f"Error in spatial query: {e}")
        return {"error": str(e)}


LP2B_GDF = None
CONFLICT_CACHE = {}

def get_lp2b_gdf():
    global LP2B_GDF
    if LP2B_GDF is None:
        file_path = os.path.join('static', 'data', 'lp2b', 'lp2b_badung.geojson')
        if os.path.exists(file_path):
            LP2B_GDF = gpd.read_file(file_path)
    return LP2B_GDF

def get_conflict_data(year):
    if year not in CONFLICT_CACHE:
        lulc = get_cached_gdf(year)
        lp2b = get_lp2b_gdf()
        if lulc is None or lp2b is None:
            return {"error": "Data tutupan lahan (LULC) atau zona LP2B tidak ditemukan"}
        
        try:
            class_col = 'Kelas_Lahan' if 'Kelas_Lahan' in lulc.columns else 'kelas'
            # Filter Lahan Terbangun
            built_up = lulc[lulc[class_col] == 'Lahan Terbangun']
            if built_up.empty or lp2b.empty:
                return {"geojson": {"type": "FeatureCollection", "features": []}, "total_area_ha": 0.0}
            
            # Project to UTM 50S (Bali) for accurate spatial overlay
            built_up_proj = built_up.to_crs(epsg=32750)
            lp2b_proj = lp2b.to_crs(epsg=32750)
            
            # Perform overlay intersection
            conflict_proj = gpd.overlay(built_up_proj, lp2b_proj, how='intersection')
            
            if conflict_proj.empty:
                CONFLICT_CACHE[year] = {"geojson": {"type": "FeatureCollection", "features": []}, "total_area_ha": 0.0}
            else:
                # Calculate area of conflict in Hectares
                conflict_proj['area_ha'] = conflict_proj.geometry.area / 10000.0
                total_area_ha = round(float(conflict_proj['area_ha'].sum()), 2)
                
                # Project back to EPSG:4326 for Leaflet compatibility
                conflict_wgs84 = conflict_proj.to_crs(epsg=4326)
                
                # Convert to GeoJSON dictionary
                geojson_dict = json.loads(conflict_wgs84.to_json())
                
                CONFLICT_CACHE[year] = {
                    "geojson": geojson_dict,
                    "total_area_ha": total_area_ha
                }
        except Exception as e:
            print(f"Error computing spatial conflicts for {year}: {e}")
            return {"error": str(e)}
            
    return CONFLICT_CACHE[year]


VULNERABILITY_CACHE = {}

def get_vulnerability_data():
    if 'vulnerability' not in VULNERABILITY_CACHE:
        lulc_2025 = get_cached_gdf('2025')
        lulc_2030 = get_cached_gdf('2030')
        if lulc_2025 is None or lulc_2030 is None:
            return {"error": "Data tutupan lahan 2025 atau 2030 tidak ditemukan"}
        
        try:
            class_col_25 = 'kelas' if 'kelas' in lulc_2025.columns else 'Kelas_Lahan'
            class_col_30 = 'kelas' if 'kelas' in lulc_2030.columns else 'Kelas_Lahan'
            
            # Filter Lahan Sawah in 2025
            sawah_2025 = lulc_2025[lulc_2025[class_col_25] == 'Lahan Sawah']
            # Filter Lahan Terbangun in 2030
            terbangun_2030 = lulc_2030[lulc_2030[class_col_30] == 'Lahan Terbangun']
            
            if sawah_2025.empty or terbangun_2030.empty:
                VULNERABILITY_CACHE['vulnerability'] = {"geojson": {"type": "FeatureCollection", "features": []}, "total_area_ha": 0.0}
            else:
                # Project to UTM 50S (Bali) for accurate spatial overlay
                sawah_proj = sawah_2025.to_crs(epsg=32750)
                terbangun_proj = terbangun_2030.to_crs(epsg=32750)
                
                # Perform overlay intersection
                vulnerability_proj = gpd.overlay(sawah_proj, terbangun_proj, how='intersection')
                
                if vulnerability_proj.empty:
                    VULNERABILITY_CACHE['vulnerability'] = {"geojson": {"type": "FeatureCollection", "features": []}, "total_area_ha": 0.0}
                else:
                    # Calculate area of vulnerability in Hectares
                    vulnerability_proj['area_ha'] = vulnerability_proj.geometry.area / 10000.0
                    total_area_ha = round(float(vulnerability_proj['area_ha'].sum()), 2)
                    
                    # Project back to EPSG:4326 for Leaflet compatibility
                    vulnerability_wgs84 = vulnerability_proj.to_crs(epsg=4326)
                    
                    # Convert to GeoJSON dictionary
                    geojson_dict = json.loads(vulnerability_wgs84.to_json())
                    
                    VULNERABILITY_CACHE['vulnerability'] = {
                        "geojson": geojson_dict,
                        "total_area_ha": total_area_ha
                    }
        except Exception as e:
            print(f"Error computing spatial vulnerability: {e}")
            return {"error": str(e)}
            
    return VULNERABILITY_CACHE['vulnerability']


def calculate_ews_status():
    try:
        file_path = os.path.join('static', 'data', 'csv', 'luasan_badung.csv')
        df = pd.read_csv(file_path)
        
        # Filter 'Lahan Sawah'
        df_sawah = df[df['Kelas_Lahan'] == 'Lahan Sawah']
        
        # Pivot by Kecamatan and Year
        pivot = df_sawah.pivot(index='Kecamatan', columns='Tahun', values='Luas_Ha').fillna(0)
        
        results = []
        for kec, row in pivot.iterrows():
            sawah_2015 = float(row.get(2015, 0))
            sawah_2020 = float(row.get(2020, 0))
            sawah_2025 = float(row.get(2025, 0))
            sawah_2030 = float(row.get(2030, 0))
            
            if sawah_2015 > 0:
                loss_pct = ((sawah_2015 - sawah_2030) / sawah_2015) * 100
                annual_rate = (sawah_2015 - sawah_2030) / 15.0
            else:
                loss_pct = 0.0
                annual_rate = 0.0
            
            # Determine EWS level and policies
            if loss_pct > 30.0:
                status = "Bahaya"
                color = "red"
                recommendation = "Moratorium perizinan pembangunan non-pertanian (alokasi akomodasi wisata/perumahan), implementasi ketat insentif LP2B, dan penegakan hukum tata ruang."
            elif loss_pct >= 15.0:
                status = "Siaga"
                color = "amber"
                recommendation = "Peningkatan pengawasan daerah greenbelt (jalur hijau), pembatasan konversi, penguatan peraturan desa adat, dan pemberian subsidi input pertanian."
            else:
                status = "Aman"
                color = "green"
                recommendation = "Pemeliharaan luasan sawah, dukungan irigasi subak lestari, pengembangan wisata pertanian ramah lingkungan, serta penghargaan kelompok tani."
            
            results.append({
                "kecamatan": kec,
                "sawah_2015": round(sawah_2015, 2),
                "sawah_2020": round(sawah_2020, 2),
                "sawah_2025": round(sawah_2025, 2),
                "sawah_2030": round(sawah_2030, 2),
                "loss_pct": round(loss_pct, 2),
                "annual_rate": round(annual_rate, 2),
                "status": status,
                "color": color,
                "recommendation": recommendation
            })
            
        results = sorted(results, key=lambda x: x['loss_pct'], reverse=True)
        return {"data": results}
    except Exception as e:
        print(f"Error calculating EWS: {e}")
        return {"error": str(e)}


def generate_pdf_report(kecamatan_name, output_stream):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        
        # 1. Fetch EWS stats to find the status of this kecamatan
        ews_data = calculate_ews_status()
        if "error" in ews_data:
            return ews_data
            
        kec_info = None
        for item in ews_data["data"]:
            if item["kecamatan"].lower() == kecamatan_name.lower():
                kec_info = item
                break
                
        if not kec_info:
            return {"error": f"Kecamatan {kecamatan_name} tidak ditemukan dalam database."}
            
        # 2. Fetch land cover details for all classes in this kecamatan
        file_path = os.path.join('static', 'data', 'csv', 'luasan_badung.csv')
        df = pd.read_csv(file_path)
        
        # Filter data for this kecamatan
        df_kec = df[df['Kecamatan'].str.lower() == kecamatan_name.lower()]
        
        # Pivot by Year and Land Cover Class
        pivot = df_kec.pivot(index='Kelas_Lahan', columns='Tahun', values='Luas_Ha').fillna(0)
        
        # 3. Initialize ReportLab document
        doc = SimpleDocTemplate(
            output_stream,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1e293b'),
            alignment=1, # Center
            spaceAfter=6
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            alignment=1, # Center
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=12,
            spaceAfter=8,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=8
        )
        
        recommendation_style = ParagraphStyle(
            'RecStyle',
            parent=styles['BodyText'],
            fontSize=10,
            leading=15,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=8
        )
        
        # 4. Build Flowables list
        story = []
        
        # Kop / Title Header
        story.append(Paragraph("<b>PEMERINTAH KABUPATEN BADUNG</b>", ParagraphStyle('Gov', parent=title_style, fontSize=11, leading=14, spaceAfter=2)))
        story.append(Paragraph("<b>BADAN PERENCANAAN PEMBANGUNAN DAERAH (BAPPEDA)</b>", ParagraphStyle('Bap', parent=title_style, fontSize=13, leading=16, spaceAfter=15)))
        
        # Horizontal line
        line_data = [['']]
        line_table = Table(line_data, colWidths=[17*cm])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#1e293b')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 15))
        
        # Report Title
        story.append(Paragraph(f"<b>LAPORAN EKSEKUTIF ALIH FUNGSI LAHAN PERTANIAN</b>", title_style))
        story.append(Paragraph(f"Analisis Spasial Temporal & Rekomendasi Kebijakan Kecamatan {kecamatan_name}", subtitle_style))
        
        # Metadata Card (Table)
        status_color_hex = '#ef4444' if kec_info['status'] == 'Bahaya' else ('#f59e0b' if kec_info['status'] == 'Siaga' else '#10b981')
        
        meta_data = [
            [Paragraph("<b>Kecamatan:</b>", body_style), Paragraph(kecamatan_name, body_style),
             Paragraph("<b>Tanggal Cetak:</b>", body_style), Paragraph(pd.Timestamp.now().strftime('%d-%m-%Y'), body_style)],
            [Paragraph("<b>Status EWS:</b>", body_style), 
             Paragraph(f"<font color='{status_color_hex}'><b>{kec_info['status'].upper()}</b></font>", body_style),
             Paragraph("<b>Metode Proyeksi:</b>", body_style), Paragraph("Cellular Automata - Markov", body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[3*cm, 5.5*cm, 3.5*cm, 5*cm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor('#f1f5f9')),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))
        
        # 1. Ringkasan Peringatan Dini (EWS)
        story.append(Paragraph("<b>1. Ringkasan Peringatan Dini (EWS)</b>", heading_style))
        ews_text = (
            f"Berdasarkan analisis alih fungsi sawah historis dari tahun 2015 hingga proyeksi tahun 2030, Kecamatan {kecamatan_name} "
            f"memiliki status kerentanan <b>{kec_info['status']}</b>. Luas sawah pada tahun 2015 tercatat sebesar <b>{kec_info['sawah_2015']:,.2f} Ha</b> "
            f"dan diproyeksikan berkurang menjadi <b>{kec_info['sawah_2030']:,.2f} Ha</b> pada tahun 2030. Sawah mengalami penyusutan/degradasi sebesar "
            f"<b>{kec_info['loss_pct']:.2f}%</b> dengan laju alih fungsi rata-rata mencapai <b>{kec_info['annual_rate']:.2f} Ha/Tahun</b>."
        )
        story.append(Paragraph(ews_text, body_style))
        story.append(Spacer(1, 10))
        
        # 2. Tabel Tutupan Lahan Temporal
        story.append(Paragraph("<b>2. Statistik Perubahan Tutupan Lahan (Ha)</b>", heading_style))
        
        # Prepare table headers
        table_headers = ["Kelas Lahan", "2015 (Hist)", "2020 (Hist)", "2025 (Hist)", "2030 (Proj)"]
        table_rows = [table_headers]
        
        # Populating table rows from pivot DataFrame
        for kelas, row in pivot.iterrows():
            table_rows.append([
                kelas,
                f"{row.get(2015, 0):,.2f}",
                f"{row.get(2020, 0):,.2f}",
                f"{row.get(2025, 0):,.2f}",
                f"{row.get(2030, 0):,.2f}"
            ])
            
        data_table = Table(table_rows, colWidths=[5*cm, 3*cm, 3*cm, 3*cm, 3*cm])
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(data_table)
        story.append(Spacer(1, 15))
        
        # 3. Rekomendasi Kebijakan Mitigasi
        story.append(Paragraph("<b>3. Rekomendasi Kebijakan Mitigasi Tata Ruang</b>", heading_style))
        
        # We wrap the recommendation inside a callout box style table
        rec_data = [[
            Paragraph(f"<b>Rekomendasi Kebijakan Khusus Status {kec_info['status']}:</b><br/>{kec_info['recommendation']}", recommendation_style)
        ]]
        rec_table = Table(rec_data, colWidths=[17*cm])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fffbeb') if kec_info['status'] == 'Siaga' else (colors.HexColor('#fef2f2') if kec_info['status'] == 'Bahaya' else colors.HexColor('#f0fdf4'))),
            ('PADDING', (0,0), (-1,-1), 12),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor(status_color_hex)),
        ]))
        story.append(rec_table)
        story.append(Spacer(1, 15))

        # Catatan & Disklaimer PDF
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=styles['Normal'],
            fontSize=7,
            leading=10,
            textColor=colors.HexColor('#64748b'),
            alignment=4 # Justify
        )
        disclaimer_text = (
            "<i><b>Catatan & Disklaimer:</b> Hasil analisis spasial, EWS, dan rekomendasi kebijakan mitigasi pada dokumen ini "
            "merupakan keluaran dari Sistem Pendukung Keputusan (DSS) berbasis model prediksi spasial komputer (CA-Markov). "
            "Dokumen ini dirancang sebagai instrumen bantu perencanaan. Verifikasi fisik di lapangan (ground-checking/ground-truthing) "
            "tetap menjadi kunci utama sebelum penentuan kebijakan resmi.</i>"
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))
        story.append(Spacer(1, 15))
        
        # Footer / Tanda Tangan
        story.append(Paragraph("Badung, " + pd.Timestamp.now().strftime('%d %B %Y'), ParagraphStyle('Date', parent=body_style, alignment=2)))
        story.append(Paragraph("<b>Kepala BAPPEDA Kabupaten Badung</b>", ParagraphStyle('SignTitle', parent=body_style, alignment=2, spaceAfter=40)))
        story.append(Paragraph("<b>( ______________________________ )</b>", ParagraphStyle('SignLine', parent=body_style, alignment=2)))
        story.append(Paragraph("NIP. 19740812 200112 1 002", ParagraphStyle('Nip', parent=body_style, alignment=2)))
        
        # 5. Build PDF document
        doc.build(story)
        return {"success": True}
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return {"error": str(e)}


def send_email_notification(report_data):
    def worker():
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.image import MIMEImage
            
            from app import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL
            
            if not SENDER_EMAIL or not SENDER_PASSWORD or SENDER_EMAIL == "your-gmail@gmail.com":
                print("[SMTP] Pengiriman email dibatalkan: Kredensial pengirim Gmail belum dikonfigurasi di app.py.")
                return
                
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL or SENDER_EMAIL
            msg['Subject'] = f"🚨 PENGADUAN BARU: Alih Fungsi Lahan di Kecamatan {report_data['kecamatan']}"
            
            maps_link = f"https://www.google.com/maps/search/?api=1&query={report_data['latitude']},{report_data['longitude']}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #334155; line-height: 1.6; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); background-color: #ffffff;">
                    <div style="background-color: #ef4444; padding: 20px; text-align: center; color: white;">
                        <h2 style="margin: 0; font-size: 20px; font-weight: bold;">🚨 LAPORAN PENGADUAN BARU</h2>
                        <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;">Indikasi Pelanggaran Alih Fungsi Lahan LP2B</p>
                    </div>
                    <div style="padding: 24px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <tr style="border-bottom: 1px solid #f1f5f9;">
                                <td style="padding: 10px 0; font-weight: bold; width: 140px; color: #64748b;">Nama Pelapor</td>
                                <td style="padding: 10px 0; color: #1e293b;">{report_data['nama_pelapor']}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;">
                                <td style="padding: 10px 0; font-weight: bold; color: #64748b;">Kontak</td>
                                <td style="padding: 10px 0; color: #1e293b;">{report_data['kontak']}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;">
                                <td style="padding: 10px 0; font-weight: bold; color: #64748b;">Kecamatan</td>
                                <td style="padding: 10px 0; color: #1e293b; font-weight: bold;">{report_data['kecamatan']}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;">
                                <td style="padding: 10px 0; font-weight: bold; color: #64748b;">Koordinat GPS</td>
                                <td style="padding: 10px 0; color: #1e293b;">
                                    {report_data['latitude']:.6f}, {report_data['longitude']:.6f}
                                    <br/>
                                    <a href="{maps_link}" target="_blank" style="color: #2563eb; font-weight: bold; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; margin-top: 4px;">
                                        📍 Buka Lokasi di Google Maps
                                    </a>
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;">
                                <td style="padding: 10px 0; font-weight: bold; color: #64748b;">Tanggal Lapor</td>
                                <td style="padding: 10px 0; color: #1e293b;">{report_data.get('tanggal', 'Baru saja')}</td>
                            </tr>
                        </table>
                        
                        <div style="margin-top: 20px; padding: 15px; background-color: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 6px;">
                            <h4 style="margin: 0 0 6px 0; color: #78350f; font-size: 14px; font-weight: bold;">Deskripsi Kejadian / Pelanggaran:</h4>
                            <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.5;">{report_data['deskripsi']}</p>
                        </div>
            """
            
            if report_data.get('foto_filename'):
                html_body += """
                        <div style="margin-top: 20px; border-top: 1px solid #f1f5f9; padding-top: 15px; text-align: center;">
                            <p style="font-size: 11px; color: #94a3b8; font-style: italic;">Foto bukti terlampir dalam email ini.</p>
                        </div>
                """
                
            html_body += """
                    </div>
                    <div style="background-color: #f8fafc; padding: 16px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                        Sistem Pendukung Keputusan (DSS) LULC Badung
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach photo
            if report_data.get('foto_filename'):
                import os
                photo_path = os.path.join('static', 'uploads', 'reports', report_data['foto_filename'])
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as fp:
                        img = MIMEImage(fp.read())
                        img.add_header('Content-Disposition', 'attachment', filename=report_data['foto_filename'])
                        msg.attach(img)
            
            # Connect to SMTP Server
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL or SENDER_EMAIL, msg.as_string())
            server.quit()
            print(f"[SMTP] Email laporan berhasil terkirim ke {RECEIVER_EMAIL or SENDER_EMAIL}")
            
        except Exception as e:
            print(f"[SMTP] Gagal mengirim email pengaduan: {e}")
            
    import threading
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()


def get_demographic_stats(year):
    try:
        # Load CSVs
        df_lahan = pd.read_csv('static/data/csv/luasan_badung.csv')
        df_penduduk = pd.read_csv('static/data/csv/penduduk_badung.csv')
        
        # Filter by year
        df_lahan_year = df_lahan[df_lahan['Tahun'] == int(year)]
        df_penduduk_year = df_penduduk[df_penduduk['Tahun'] == int(year)]
        
        if df_lahan_year.empty or df_penduduk_year.empty:
            return {"error": f"Data tahun {year} tidak ditemukan."}
            
        # Pivot Lahan so that land cover classes are columns
        pivot_lahan = df_lahan_year.pivot(index='Kecamatan', columns='Kelas_Lahan', values='Luas_Ha').reset_index()
        
        # Clean column names
        pivot_lahan.columns.name = None
        
        # Calculate Total Luas Kecamatan (in Ha) from all classes
        class_cols = [col for col in pivot_lahan.columns if col != 'Kecamatan']
        pivot_lahan['Total_Luas_Ha'] = pivot_lahan[class_cols].sum(axis=1)
        
        # Merge with population
        merged = pd.merge(pivot_lahan, df_penduduk_year, on='Kecamatan')
        
        # Calculate new metrics:
        # 1. Kepadatan Penduduk (Jiwa/km^2) -> 1 km^2 = 100 Ha
        merged['Kepadatan_Penduduk'] = merged['Jumlah_Penduduk'] / (merged['Total_Luas_Ha'] / 100.0)
        
        # 2. Sawah per Kapita (m^2/Jiwa) -> 1 Ha = 10000 m^2
        sawah_col = 'Lahan Sawah' if 'Lahan Sawah' in merged.columns else None
        if sawah_col:
            merged['Sawah_m2_per_Jiwa'] = (merged[sawah_col] * 10000.0) / merged['Jumlah_Penduduk']
        else:
            merged['Sawah_m2_per_Jiwa'] = 0.0
            
        # 3. Terbangun per Kapita (m^2/Jiwa)
        terbangun_col = 'Lahan Terbangun' if 'Lahan Terbangun' in merged.columns else None
        if terbangun_col:
            merged['Terbangun_m2_per_Jiwa'] = (merged[terbangun_col] * 10000.0) / merged['Jumlah_Penduduk']
        else:
            merged['Terbangun_m2_per_Jiwa'] = 0.0

        # Round values for nice presentation
        merged['Kepadatan_Penduduk'] = merged['Kepadatan_Penduduk'].round(2)
        merged['Sawah_m2_per_Jiwa'] = merged['Sawah_m2_per_Jiwa'].round(2)
        merged['Terbangun_m2_per_Jiwa'] = merged['Terbangun_m2_per_Jiwa'].round(2)
        merged['Total_Luas_Ha'] = merged['Total_Luas_Ha'].round(2)
        
        # Convert to dictionary lists
        records = merged.to_dict(orient='records')
        return {"data": records}
    except Exception as e:
        print(f"Error in get_demographic_stats: {e}")
        return {"error": str(e)}