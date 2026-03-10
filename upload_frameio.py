import requests
import json

ACCESS_TOKEN = "SEU_ACCESS_TOKEN"
PARENT_ASSET_ID = "SEU_PARENT_ASSET_ID"

VIDEO_PATH = r"C:\frameio_test\teste.mp4"
VIDEO_NAME = "teste.mp4"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# criar asset
r = requests.post(
    "https://api.frame.io/v4/assets",
    headers=headers,
    json={
        "name": VIDEO_NAME,
        "parent_id": PARENT_ASSET_ID,
        "type": "file"
    }
)

asset = r.json()

asset_id = asset["id"]
upload_url = asset["upload_url"]

print("ASSET ID:", asset_id)

# upload do video
with open(VIDEO_PATH, "rb") as f:
    requests.put(upload_url, data=f)

# finalizar upload
requests.post(
    f"https://api.frame.io/v4/assets/{asset_id}/complete",
    headers=headers
)

# salvar asset_id para o script do DaVinci
with open(r"C:\frameio_test\asset_id.json", "w") as f:
    json.dump({"asset_id": asset_id}, f)

print("UPLOAD FINALIZADO")