import base64
import requests
import urllib3
urllib3.disable_warnings()

try:
    with open("photo.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    foto_url = f"data:image/png;base64,{b64}"

    resp = requests.patch(
        "https://sipandu-it-uinjambi.my.id/api/certificates/4329", 
        json={"foto_url": foto_url}, 
        verify=False
    )
    print(resp.json())
except Exception as e:
    print(f"Error: {e}")
