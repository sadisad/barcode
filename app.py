from flask import Flask, render_template_string, abort, jsonify, request, redirect
import psycopg2
import psycopg2.extras
import os
import random
from dotenv import load_dotenv
import qrcode
from io import BytesIO
import base64

load_dotenv()

app = Flask(__name__)

# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    return conn

def init_db():
    if not os.environ.get("POSTGRES_URL"):
        print("POSTGRES_URL is not set. Skipping DB init.")
        return
        
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS certificates (
                        id          SERIAL PRIMARY KEY,
                        url_id      INTEGER UNIQUE NOT NULL,
                        nama        TEXT    NOT NULL,
                        nim         TEXT    NOT NULL,
                        prodi       TEXT    NOT NULL DEFAULT 'Sistem Informasi',
                        foto_url    TEXT,
                        tanggal_ujian TEXT  NOT NULL,
                        tanggal_ttd   TEXT  NOT NULL,
                        cert_id     TEXT    NOT NULL,
                        qr_base64   TEXT    NOT NULL,
                        nilai_word  INTEGER DEFAULT 75,
                        nilai_excel INTEGER DEFAULT 75,
                        nilai_ppt   INTEGER DEFAULT 75,
                        nilai_inet  INTEGER DEFAULT 75,
                        grade_word  TEXT    DEFAULT 'B',
                        grade_excel TEXT    DEFAULT 'B',
                        grade_ppt   TEXT    DEFAULT 'B',
                        grade_inet  TEXT    DEFAULT 'B'
                    )
                """)
            conn.commit()
    except Exception as e:
        print("Error initializing database:", e)

init_db()

# ─── HTML Template ───────────────────────────────────────────────────────────

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Generator Sertifikat</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Inter', sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px; }
    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h2 { text-align: center; color: #333; margin-bottom: 20px; }
    .form-group { margin-bottom: 15px; }
    label { display: block; margin-bottom: 5px; font-weight: 600; color: #555; }
    input[type="text"], input[type="file"] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-family: 'Inter', sans-serif; }
    button { width: 100%; padding: 12px; background-color: #2B4961; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; font-weight: bold; margin-top: 10px; }
    button:hover { background-color: #1e3344; }
    .section-title { font-size: 14px; font-weight: bold; color: #888; text-transform: uppercase; margin-top: 25px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
</style>
</head>
<body>
<div class="container">
    <h2>Generate Sertifikat Baru</h2>
    <form action="/dashboard" method="POST" enctype="multipart/form-data">
        <div class="section-title">Data Utama</div>
        <div class="form-group">
            <label for="nama">Nama Lengkap</label>
            <input type="text" id="nama" name="nama" required placeholder="Masukkan Nama Lengkap">
        </div>
        <div class="form-group">
            <label for="foto">Foto Profil (Rasio 3:4)</label>
            <input type="file" id="foto" name="foto" accept="image/*" required>
        </div>
        
        <div class="section-title">Data Tambahan (Bisa Dibiarkan Default)</div>
        <div class="form-group">
            <label for="nim">NIM</label>
            <input type="text" id="nim" name="nim" placeholder="Contoh: 701220338" value="701220338">
        </div>
        <div class="form-group">
            <label for="prodi">Program Studi</label>
            <input type="text" id="prodi" name="prodi" value="Sistem Informasi">
        </div>
        <div class="form-group">
            <label for="tanggal_ujian">Tanggal Ujian</label>
            <input type="text" id="tanggal_ujian" name="tanggal_ujian" value="14 April 2026">
        </div>
        <div class="form-group">
            <label for="tanggal_ttd">Tanggal Tanda Tangan</label>
            <input type="text" id="tanggal_ttd" name="tanggal_ttd" value="22 April 2026">
        </div>
        <div class="form-group">
            <label for="cert_id">Nomor Sertifikat (opsional)</label>
            <input type="text" id="cert_id" name="cert_id" placeholder="Biarkan kosong untuk generate otomatis">
        </div>
        <button type="submit">Generate & Lihat Sertifikat</button>
    </form>
</div>
</body>
</html>"""

# ─── HTML Template ───────────────────────────────────────────────────────────

CERT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap" rel="stylesheet">
    <title>SERTIFIKAT</title>
    <style>
        :root {
            --certificate-width: 297mm;
            --certificate-height: 210mm;
            --certificate-padding-y: 10mm;
            --certificate-padding-x: 12mm;
            --certificate-content-offset-top: 28mm;
            --certificate-signature-right: 58mm;
            --certificate-signature-bottom: 20mm;
            --certificate-signature-gap: 8mm;
            --certificate-photo-width: 24mm;
            --certificate-photo-height: 32mm;
            --certificate-qr-size: 16mm;
            --certificate-signature-width: 70mm;
            --certificate-photo-offset-top: 2mm;
            --certificate-text-size: 10pt;
            --certificate-title-size: 14pt;
            --certificate-table-gap-y: 2.4mm;
            --certificate-cell-padding-y: 1.4mm;
            --certificate-cell-padding-x: 1.8mm;
            --certificate-identity-label-width: 34mm;
            --certificate-identity-value-width: 95mm;
            --certificate-details-top-gap: 3mm;
        }
        html, body { width: 100%; min-height: 100%; margin: 0; }
        body {
            font-family: "Inter", sans-serif;
            line-height: 1.09;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 12mm 0;
            background-color: #f3f4f6;
        }
        .container {
            width: var(--certificate-width);
            height: var(--certificate-height);
            margin: 0;
            padding: var(--certificate-padding-y) var(--certificate-padding-x);
            background-image: url('https://sipandu-it.uinjambi.ac.id/images/sertifikat%20ujian%20ti-affdesign3.png');
            background-size: cover;
            background-position: center;
            position: relative;
            box-sizing: border-box;
            overflow: hidden;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
        }
        .content { text-align: center; margin-top: 0; padding-top: var(--certificate-content-offset-top); }
        .content .certificate-title { font-size: var(--certificate-title-size); font-weight: bold; text-decoration: underline; padding-top: 2mm; }
        .content .certificate-id { font-size: var(--certificate-text-size); margin-top: 1.4mm; }
        .content p { font-size: var(--certificate-text-size); }
        .content table { margin: var(--certificate-table-gap-y) auto; width: 80%; text-align: left; font-size: var(--certificate-text-size); table-layout: fixed; overflow-wrap: anywhere; word-break: normal; }
        .content table td { border-radius: 100px; padding: var(--certificate-cell-padding-y) var(--certificate-cell-padding-x); vertical-align: top; }
        .identity-table { width: auto !important; margin: 12px auto; }
        .identity-table td:first-child { width: var(--certificate-identity-label-width); white-space: nowrap; }
        .identity-table td:nth-child(2) { min-width: var(--certificate-identity-value-width); }
        .details table { width: 74%; border-collapse: collapse; margin-top: var(--certificate-details-top-gap); table-layout: fixed; }
        .details th, .details td { border: 1px solid rgb(255,255,255); padding: 2mm; color: white; text-align: center; background-color: #2B4961; overflow-wrap: anywhere; }
        .details th { background-color: #F7B118; }
        .signature-wrapper { position: absolute; right: var(--certificate-signature-right); bottom: var(--certificate-signature-bottom); display: flex; align-items: flex-start; gap: var(--certificate-signature-gap); }
        .photo-box { width: var(--certificate-photo-width); height: var(--certificate-photo-height); border: 1px solid #000; display: flex; justify-content: center; align-items: center; font-size: var(--certificate-text-size); text-align: center; overflow: hidden; margin-top: var(--certificate-photo-offset-top); }
        .signature { text-align: left; width: var(--certificate-signature-width); font-size: var(--certificate-text-size); }
        .signature p { margin: 0; line-height: 1.08; }
        .profile-photo { width: 100%; height: 100%; object-fit: cover; display: block; }
        .qr-code { width: var(--certificate-qr-size); height: var(--certificate-qr-size); display: block; margin: 2mm 0 1mm; }
        .signature-identity { margin-top: 1mm; }
        .qr-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(255,0,0,0.1); display: flex; justify-content: center; align-items: center; text-align: center; z-index: 999; pointer-events: none; }
        .qr-overlay p { font-size: 28px; color: red; font-weight: bold; text-shadow: 1px 1px white; }
        @media print {
            @page { size: A4 landscape; margin: 0; }
            html, body { width: var(--certificate-width); height: var(--certificate-height); margin: 0; min-height: 0; padding: 0; display: block; overflow: hidden; background: transparent; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .container { width: var(--certificate-width); height: var(--certificate-height); margin: 0; overflow: hidden; box-shadow: none; break-inside: avoid; page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <div class="certificate-title">SERTIFIKAT</div>
            <div class="certificate-id">{{ cert.cert_id }}</div>
            <p style="font-size: 10px; color: red;">(Halaman ini dibuka melalui QR Code untuk keaslian sertifikat)</p>
            <p>Unit Teknologi Informasi dan Pangkalan Data (UTIPD) <br>Universitas Islam Negeri Sultan Thaha Saifuddin Jambi menerangkan:</p>
            <table class="identity-table">
                <tr><td>Nama</td><td>: <b>{{ cert.nama }}</b></td></tr>
                <tr><td>NIM</td><td>: <b>{{ cert.nim }}</b></td></tr>
                <tr><td>Program Studi</td><td>: <b>{{ cert.prodi }}</b></td></tr>
            </table>
            <p>Telah mengikuti Ujian Praktek Teknologi Informasi dan Komunikasi (TIK) pada tanggal
                {{ cert.tanggal_ujian }}<br> dan dinyatakan <b>LULUS</b> dengan nilai:
            </p>
            <div class="details">
                <table>
                    <thead>
                        <tr>
                            <th style="color:#000;border-radius:100px;">MATERI</th>
                            <th style="color:#000;border-radius:100px;">NILAI</th>
                            <th style="color:#000;border-radius:100px;">GRADE</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>Microsoft Word</td><td>{{ cert.nilai_word }}</td><td>{{ cert.grade_word }}</td></tr>
                        <tr><td>Microsoft Excel</td><td>{{ cert.nilai_excel }}</td><td>{{ cert.grade_excel }}</td></tr>
                        <tr><td>Microsoft PowerPoint</td><td>{{ cert.nilai_ppt }}</td><td>{{ cert.grade_ppt }}</td></tr>
                        <tr><td>Internet</td><td>{{ cert.nilai_inet }}</td><td>{{ cert.grade_inet }}</td></tr>
                    </tbody>
                </table>
            </div>
            <p style="font-size: 10px;">Sertifikat ini hanya berlaku di Universitas Islam Negeri Sulthan Thaha Saifuddin Jambi</p>
        </div>
        <div class="signature-wrapper">
            <div class="photo-box">
                {% if cert.foto_url %}
                <img src="{{ cert.foto_url }}" alt="Foto Mahasiswa" class="profile-photo">
                {% endif %}
            </div>
            <div class="signature">
                <p>
                    Jambi, {{ cert.tanggal_ttd }}<br>
                    Kepala Unit Teknologi Informasi dan <br>Pangkalan Data <br>
                    <img src="{{ cert.qr_base64 }}" alt="QR Code" class="qr-code">
                    <span class="signature-identity">
                        Titin Agustin Nengsih, S.Si., M.Si., Ph.D<br>
                        NIP. 198208162006042002
                    </span>
                </p>
            </div>
        </div>
        <div class="qr-overlay">
            <p>(Halaman ini dibuka melalui QR Code untuk keaslian sertifikat)</p>
        </div>
        <script>
            window.onload = function() {
                setTimeout(() => { window.print(); }, 500);
            };
        </script>
    </div>
</body>
</html>"""

# ─── Routes ──────────────────────────────────────────────────────────────────

def generate_qr_base64(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "GET":
        return render_template_string(DASHBOARD_TEMPLATE)
    else:
        nama = request.form.get("nama")
        nim = request.form.get("nim", "701220338")
        prodi = request.form.get("prodi", "Sistem Informasi")
        tanggal_ujian = request.form.get("tanggal_ujian", "14 April 2026")
        tanggal_ttd = request.form.get("tanggal_ttd", "22 April 2026")
        cert_id_text = request.form.get("cert_id", "").strip()
        if not cert_id_text:
            cert_id_text = f"160720257012{random.randint(10000, 99999)}P06{random.randint(10000, 99999)}"
        
        foto = request.files.get("foto")
        foto_url = ""
        if foto and foto.filename:
            mime = foto.mimetype or "image/png"
            data = base64.b64encode(foto.read()).decode("utf-8")
            foto_url = f"data:{mime};base64,{data}"

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT url_id FROM certificates")
                used = {row[0] for row in cur.fetchall()}
                available = [i for i in range(1000, 9999) if i not in used]
                url_id = random.choice(available) if available else random.randint(10000, 99999)
                
                # Base URL for verify
                base_url = request.host_url.rstrip("/")
                verify_url = f"{base_url}/keaslian-sertifikat/{url_id}"
                qr_base64 = generate_qr_base64(verify_url)

                cur.execute("""
                    INSERT INTO certificates
                      (url_id, nama, nim, prodi, foto_url, tanggal_ujian, tanggal_ttd, cert_id, qr_base64)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    url_id, nama, nim, prodi, foto_url, tanggal_ujian, tanggal_ttd, cert_id_text, qr_base64
                ))
            conn.commit()

        return redirect(f"/keaslian-sertifikat/{url_id}")

@app.route("/keaslian-sertifikat/<int:url_id>")
def verify_certificate(url_id):
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT * FROM certificates WHERE url_id = %s", (url_id,)
            )
            cert = cur.fetchone()
    if cert is None:
        abort(404)
    return render_template_string(CERT_TEMPLATE, cert=cert)

@app.route("/api/certificates", methods=["POST"])
def add_certificate():
    """API untuk menambah sertifikat baru. Returns the new certificate ID."""
    data = request.get_json(force=True)
    required = ["nama", "nim", "tanggal_ujian", "tanggal_ttd", "cert_id", "qr_base64"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    with get_db() as conn:
        with conn.cursor() as cur:
            if "url_id" in data and data["url_id"]:
                url_id = int(data["url_id"])
                cur.execute("SELECT id FROM certificates WHERE url_id = %s", (url_id,))
                existing = cur.fetchone()
                if existing:
                    return jsonify({"error": f"url_id {url_id} sudah dipakai"}), 409
            else:
                cur.execute("SELECT url_id FROM certificates")
                used = {row[0] for row in cur.fetchall()}
                available = [i for i in range(1000, 9999) if i not in used]
                url_id = random.choice(available) if available else random.randint(10000, 99999)

            cur.execute("""
                INSERT INTO certificates
                  (url_id, nama, nim, prodi, foto_url, tanggal_ujian, tanggal_ttd, cert_id, qr_base64,
                   nilai_word, nilai_excel, nilai_ppt, nilai_inet,
                   grade_word, grade_excel, grade_ppt, grade_inet)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                url_id,
                data["nama"],
                data["nim"],
                data.get("prodi", "Sistem Informasi"),
                data.get("foto_url"),
                data["tanggal_ujian"],
                data["tanggal_ttd"],
                data["cert_id"],
                data["qr_base64"],
                data.get("nilai_word", 75), data.get("nilai_excel", 75),
                data.get("nilai_ppt", 75),  data.get("nilai_inet", 75),
                data.get("grade_word", "B"), data.get("grade_excel", "B"),
                data.get("grade_ppt", "B"),  data.get("grade_inet", "B"),
            ))
        conn.commit()

    return jsonify({"id": url_id, "url": f"/keaslian-sertifikat/{url_id}"}), 201

@app.route("/api/certificates/<int:url_id>", methods=["PATCH"])
def update_certificate(url_id):
    """API untuk update data sertifikat yang sudah ada berdasarkan url_id."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM certificates WHERE url_id = %s", (url_id,)
            )
            existing = cur.fetchone()
            if existing is None:
                return jsonify({"error": f"Certificate with url_id {url_id} not found"}), 404

            data = request.get_json(force=True)

            allowed_fields = [
                "tanggal_ujian", "tanggal_ttd", "cert_id", "qr_base64",
                "nilai_word", "nilai_excel", "nilai_ppt", "nilai_inet",
                "grade_word", "grade_excel", "grade_ppt", "grade_inet",
                "nama", "nim", "prodi", "foto_url"
            ]
            updates = {k: v for k, v in data.items() if k in allowed_fields}
            if not updates:
                return jsonify({"error": "No valid fields to update"}), 400

            set_clause = ", ".join(f"{k} = %s" for k in updates)
            values = list(updates.values()) + [url_id]
            cur.execute(
                f"UPDATE certificates SET {set_clause} WHERE url_id = %s", values
            )
        conn.commit()

    return jsonify({"success": True, "url_id": url_id, "updated": list(updates.keys())}), 200

@app.route("/")
def index():
    return "<h3>Certificate Verification Server</h3><p>Access: /dashboard to generate</p>", 200

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)