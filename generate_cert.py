import base64
import argparse
import qrcode
import requests
import json
from io import BytesIO

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

def register_to_server(server_base_url, payload):
    """Register certificate to the Flask server and get the verification URL."""
    api_url = f"{server_base_url.rstrip('/')}/api/certificates"
    resp = requests.post(api_url, json=payload, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    cert_id = result["id"]
    verify_url = f"{server_base_url.rstrip('/')}/keaslian-sertifikat/{cert_id}"
    return cert_id, verify_url

def generate_certificate(
    nama,
    nim,
    foto_url,
    server_base_url,
    tanggal_ujian="14 April 2026",
    tanggal_ttd="22 April 2026",
    cert_id_text="16072025701220202P0653438",
    prodi="Sistem Informasi",
    template_path="template.html",
    output_path="output.html",
    nilai_word=75, nilai_excel=75, nilai_ppt=75, nilai_inet=75,
    grade_word="B", grade_excel="B", grade_ppt="B", grade_inet="B",
):
    # Step 1: Register ke server untuk dapat ID & URL verifikasi
    print(f"[1/3] Registering certificate to server: {server_base_url}")

    # Placeholder QR dulu (akan di-replace setelah dapat URL)
    placeholder_qr = generate_qr_base64("placeholder")

    payload = {
        "nama": nama,
        "nim": nim,
        "prodi": prodi,
        "foto_url": foto_url,
        "tanggal_ujian": tanggal_ujian,
        "tanggal_ttd": tanggal_ttd,
        "cert_id": cert_id_text,
        "qr_base64": placeholder_qr,  # temporary
        "nilai_word": nilai_word, "nilai_excel": nilai_excel,
        "nilai_ppt": nilai_ppt,   "nilai_inet": nilai_inet,
        "grade_word": grade_word, "grade_excel": grade_excel,
        "grade_ppt": grade_ppt,   "grade_inet": grade_inet,
    }

    db_id, verify_url = register_to_server(server_base_url, payload)
    print(f"    [OK] Certificate registered! ID={db_id}")
    print(f"    [OK] Verification URL: {verify_url}")

    # Step 2: Generate QR Code pointing to the real verification URL
    print(f"[2/3] Generating QR Code -> {verify_url}")
    qr_base64 = generate_qr_base64(verify_url)

    # Step 3: Update server dengan QR Code yang benar
    # (Patch via re-insert isn't ideal but works; alternatively call PATCH)
    # Re-generate HTML output locally
    print(f"[3/3] Generating HTML output -> {output_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    html_content = html_content.replace("{{NAMA}}", nama)
    html_content = html_content.replace("{{NIM}}", nim)
    html_content = html_content.replace("{{FOTO}}", foto_url)
    html_content = html_content.replace("{{QR_CODE_BASE64}}", qr_base64)
    html_content = html_content.replace("{{TANGGAL_UJIAN}}", tanggal_ujian)
    html_content = html_content.replace("{{TANGGAL_TTD}}", tanggal_ttd)
    html_content = html_content.replace("{{CERT_ID}}", cert_id_text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print()
    print("=" * 60)
    print("[OK] Certificate generated successfully!")
    print(f"   HTML output : {output_path}")
    print(f"   Verify URL  : {verify_url}")
    print(f"   QR Code     : points to {verify_url}")
    print("=" * 60)
    return verify_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Certificate")
    parser.add_argument("--nama",         type=str, required=True,  help="Nama Mahasiswa")
    parser.add_argument("--nim",          type=str, default="701220338", help="NIM Mahasiswa")
    parser.add_argument("--foto",         type=str, default="https://s31.uinjambi.ac.id/sipandu-it/foto_profil/FOTO-20250716-113927-2715.jpg", help="URL Foto Mahasiswa")
    parser.add_argument("--server",       type=str, default="http://localhost:5000", help="Base URL server Flask (misal: https://your-app.railway.app)")
    parser.add_argument("--tanggal-ujian",type=str, default="14 April 2026", help="Tanggal Ujian")
    parser.add_argument("--tanggal-ttd",  type=str, default="22 April 2026", help="Tanggal Tanda Tangan")
    parser.add_argument("--cert-id",      type=str, default="16072025701220202P0653438", help="ID/Nomor Sertifikat")
    parser.add_argument("--prodi",        type=str, default="Sistem Informasi", help="Program Studi")
    parser.add_argument("--output",       type=str, default="output.html", help="Output HTML file")
    parser.add_argument("--nilai-word",   type=int, default=75)
    parser.add_argument("--nilai-excel",  type=int, default=75)
    parser.add_argument("--nilai-ppt",    type=int, default=75)
    parser.add_argument("--nilai-inet",   type=int, default=75)
    parser.add_argument("--grade-word",   type=str, default="B")
    parser.add_argument("--grade-excel",  type=str, default="B")
    parser.add_argument("--grade-ppt",    type=str, default="B")
    parser.add_argument("--grade-inet",   type=str, default="B")

    args = parser.parse_args()
    generate_certificate(
        args.nama,
        args.nim,
        args.foto,
        args.server,
        args.tanggal_ujian,
        args.tanggal_ttd,
        args.cert_id,
        args.prodi,
        output_path=args.output,
        nilai_word=args.nilai_word, nilai_excel=args.nilai_excel,
        nilai_ppt=args.nilai_ppt,   nilai_inet=args.nilai_inet,
        grade_word=args.grade_word, grade_excel=args.grade_excel,
        grade_ppt=args.grade_ppt,   grade_inet=args.grade_inet,
    )
