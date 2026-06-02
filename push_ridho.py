import requests
import base64
from generate_cert import generate_certificate
import urllib3
urllib3.disable_warnings()

SERVER = "https://sipandu-it-uinjambi.my.id"

# Fetch image
img_url = "https://s31.uinjambi.ac.id/sipandu-it/foto_profil/FOTO-20250716-113927-2715.jpg"
print("Fetching photo...")
try:
    r = requests.get(img_url, verify=False)
    if r.status_code == 200:
        b64 = base64.b64encode(r.content).decode("utf-8")
        foto_b64 = f"data:image/jpeg;base64,{b64}"
    else:
        foto_b64 = img_url
except Exception:
    foto_b64 = img_url

print("Generating certificate for Ridho Oktara...")
try:
    generate_certificate(
        nama="RIDHO OKTARA",
        nim="701220338",
        foto_url=foto_b64,
        server_base_url=SERVER,
        tanggal_ujian="14 April 2026",
        tanggal_ttd="22 April 2026",
        cert_id_text="16072025701220202P0653438",
        prodi="Sistem Informasi",
        output_path="output_ridho.html"
    )
except Exception as e:
    print(f"Error: {e}")

print("Done!")
