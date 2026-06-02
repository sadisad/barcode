import os
import re
from generate_cert import generate_certificate
import urllib3
urllib3.disable_warnings()

SERVER = "https://barcode-kappa-rust.vercel.app"

# ID -> File path mapping
files = {
    2029: r"C:\Users\NITRO\.gemini\antigravity-ide\brain\1ab86644-c252-4ae4-a24a-8470f79e3de3\.system_generated\steps\89\content.md",
    2524: r"C:\Users\NITRO\.gemini\antigravity-ide\brain\1ab86644-c252-4ae4-a24a-8470f79e3de3\.system_generated\steps\311\content.md",
    7205: r"C:\Users\NITRO\.gemini\antigravity-ide\brain\1ab86644-c252-4ae4-a24a-8470f79e3de3\.system_generated\steps\314\content.md"
}

def extract_field(html, pattern, group=1):
    match = re.search(pattern, html)
    return match.group(group) if match else None

for url_id, path in files.items():
    print(f"Processing {url_id}...")
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
        
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
        
    nama = extract_field(html, r"<tr><td>Nama</td><td>: <b>(.*?)</b></td></tr>")
    nim = extract_field(html, r"<tr><td>NIM</td><td>: <b>(.*?)</b></td></tr>")
    prodi = extract_field(html, r"<tr><td>Program Studi</td><td>: <b>(.*?)</b></td></tr>")
    cert_id = extract_field(html, r'<div class="certificate-id">(.*?)</div>')
    
    # Extract photo base64
    foto_url = extract_field(html, r'<img src="(data:image/.*?;base64,.*?)" alt="Foto Mahasiswa"')
    if not foto_url:
        foto_url = ""
        
    print(f"  Nama: {nama}, NIM: {nim}, Cert: {cert_id}")
    
    try:
        generate_certificate(
            nama=nama,
            nim=nim,
            foto_url=foto_url,
            server_base_url=SERVER,
            tanggal_ujian="14 April 2026",
            tanggal_ttd="22 April 2026",
            cert_id_text=cert_id,
            prodi=prodi,
            output_path=f"output_{url_id}.html",
            url_id=url_id
        )
    except Exception as e:
        print(f"  [ERROR] {e}")

print("Done!")
