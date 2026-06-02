import requests

LIVE_SERVER_URL = "https://web.sipandu-it-uinjambi.my.id"

# Data sertifikat yang ingin diupdate
CERTIFICATES_TO_UPDATE = [
    2029, # Putri Ratna Sari
    2524, # Upik Tria Junisa
    7205  # Aulia Meyda Permatasari
]

def update_certificate_dates(url_id, tanggal_ujian="14 April 2024", tanggal_ttd="22 April 2024"):
    api_url = f"{LIVE_SERVER_URL}/api/certificates/{url_id}"
    
    payload = {
        "tanggal_ujian": tanggal_ujian,
        "tanggal_ttd": tanggal_ttd
    }
    
    print(f"Updating certificate {url_id}...")
    try:
        # Menggunakan verify=False seperti di script aslinya jika ada isu SSL
        response = requests.patch(api_url, json=payload, verify=False)
        
        if response.status_code == 200:
            print(f"[OK] Certificate {url_id} updated successfully!")
            print(f"URL: {LIVE_SERVER_URL}/keaslian-sertifikat/{url_id}")
        else:
            print(f"[ERROR] Failed to update {url_id}. Status Code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] Exception occurred while updating {url_id}: {e}")

if __name__ == "__main__":
    # Karena tidak ada tahun pada permintaan, saya menggunakan 2024. 
    # Silakan ubah jika tahunnya berbeda (misal 2026 seperti pada generate_cert.py)
    
    # Asumsi dari generate_cert.py menggunakan 2026
    TANGGAL_UJIAN_BARU = "14 April 2026"
    TANGGAL_TTD_BARU = "22 April 2026"
    
    print(f"Target Tanggal Ujian: {TANGGAL_UJIAN_BARU}")
    print(f"Target Tanggal TTD: {TANGGAL_TTD_BARU}")
    print("-" * 50)
    
    for cert_id in CERTIFICATES_TO_UPDATE:
        update_certificate_dates(cert_id, TANGGAL_UJIAN_BARU, TANGGAL_TTD_BARU)
