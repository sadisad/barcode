import requests
import re
import json
import argparse

OLD_SERVER = "https://web.sipandu-it-uinjambi.my.id"
NEW_SERVER = "https://barcode-kappa-rust.vercel.app"
CERT_IDS = [2029, 2524, 7205]

def extract_field(html, pattern, group=1):
    match = re.search(pattern, html)
    return match.group(group) if match else None

def migrate_cert(url_id):
    print(f"Fetching {url_id} from {OLD_SERVER}...")
    resp = requests.get(f"{OLD_SERVER}/keaslian-sertifikat/{url_id}", verify=False)
    
    if resp.status_code != 200:
        print(f"Failed to fetch {url_id}")
        return
        
    html = resp.text
    
    # Extract data
    nama = extract_field(html, r"<tr><td>Nama</td><td>: <b>(.*?)</b></td></tr>")
    nim = extract_field(html, r"<tr><td>NIM</td><td>: <b>(.*?)</b></td></tr>")
    prodi = extract_field(html, r"<tr><td>Program Studi</td><td>: <b>(.*?)</b></td></tr>")
    cert_id = extract_field(html, r'<div class="certificate-id">(.*?)</div>')
    
    # Extract photo base64
    foto_url = extract_field(html, r'<img src="(data:image/.*?;base64,.*?)" alt="Foto Mahasiswa"')
    
    # We will let the new server create a new QR code pointing to itself, so we just use a placeholder
    # Or actually the API expects `qr_base64`. `generate_cert.py` normally generates the QR after getting the URL.
    # Wait, in the Vercel app, does it generate the QR?
    # No, `app.py` expects `qr_base64` in the POST payload!
    # So we should use the logic from `generate_cert.py` to generate the QR code first.
    
    # Let's import generate_cert to do the heavy lifting!
    try:
        from generate_cert import generate_certificate
        print(f"Migrating {nama} ({nim}) -> {NEW_SERVER}")
        
        # We want the fixed dates!
        tanggal_ujian = "14 April 2026"
        tanggal_ttd = "22 April 2026"
        
        # Call generate_certificate from the local file
        # generate_certificate(nama, nim, foto_url, server_base_url, tanggal_ujian, tanggal_ttd, cert_id_text, prodi, output_path, url_id)
        # Note: generate_cert.py creates an output HTML which we don't care about here, we just want the API call.
        verify_url = generate_certificate(
            nama=nama,
            nim=nim,
            foto_url=foto_url if foto_url else "",
            server_base_url=NEW_SERVER,
            tanggal_ujian=tanggal_ujian,
            tanggal_ttd=tanggal_ttd,
            cert_id_text=cert_id,
            prodi=prodi,
            output_path=f"output_{url_id}.html",
            url_id=url_id
        )
        print(f"[SUCCESS] {url_id} migrated! Verify URL: {verify_url}")
    except Exception as e:
        print(f"Failed to generate for {url_id}: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    for cert_id in CERT_IDS:
        migrate_cert(cert_id)
        print("-" * 40)
