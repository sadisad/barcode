"""
Fix QR codes untuk sertifikat yang masih menggunakan placeholder QR.
Script ini akan re-generate QR code yang benar (mengarah ke URL verifikasi live)
dan PATCH ke server.
"""

import qrcode
import base64
import requests
import urllib3
from io import BytesIO

urllib3.disable_warnings()

SERVER = "https://sipandu-it-uinjambi.my.id"

# url_id -> nama (untuk info saja)
CERTS = {
    2029: "Putri Ratna Sari",
    2524: "Upik Tria Junisa",
    7205: "Aulia Meyda Permatasari",
    4329: "Ridho Oktara",
}

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

def fix_qr(url_id, nama):
    verify_url = f"{SERVER}/keaslian-sertifikat/{url_id}"
    print(f"\n[{url_id}] {nama}")
    print(f"  Generating QR -> {verify_url}")
    qr_base64 = generate_qr_base64(verify_url)

    api_url = f"{SERVER}/api/certificates/{url_id}"
    resp = requests.patch(
        api_url,
        json={"qr_base64": qr_base64},
        verify=False,
        timeout=30,
    )
    if resp.status_code == 200:
        print(f"  [OK] QR code updated successfully!")
        print(f"  Cek: {verify_url}")
    else:
        print(f"  [ERROR] Status {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing QR codes for all certificates...")
    print("=" * 60)
    for url_id, nama in CERTS.items():
        fix_qr(url_id, nama)
    print("\nDone!")
