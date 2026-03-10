import requests
import os
import json

# ================= CONFIG =================
ACCESS_TOKEN = "seu_token_aqui"
ACCOUNT_ID = "seu_account_id"  # Obtenha via GET /v4/me ou /v4/accounts
FOLDER_ID = "seu_folder_id"    # ID da pasta onde vai subir o vídeo
VIDEO_PATH = r"C:\frameio_test\teste.mp4"
# ==========================================

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

video_name = os.path.basename(VIDEO_PATH)
file_size = os.path.getsize(VIDEO_PATH)

print(f"Arquivo: {video_name} ({file_size} bytes)")

# 1️⃣ CRIAR O ARQUIVO (NÃO É MAIS /UPLOADS)
print("\n1. Criando registro do arquivo...")

create_url = f"https://api.frame.io/v4/accounts/{ACCOUNT_ID}/folders/{FOLDER_ID}/files"

payload = {
    "name": video_name,
    "file_size": file_size,
    "media_type": "video/mp4"  # Ajuste conforme seu tipo de arquivo
}

r = requests.post(create_url, headers=headers, json=payload)

if r.status_code != 201:  # V4 retorna 201 Created
    print(f"ERRO: {r.status_code}")
    print(r.text)
    exit(1)

data = r.json()["data"]  # Na V4, resposta vem dentro de "data" [citation:5]
file_id = data["id"]
upload_urls = data["upload_urls"]  # Array de URLs para upload multipart

print(f"✓ Arquivo criado. ID: {file_id}")
print(f"  URLs de upload: {len(upload_urls)} parte(s)")

# 2️⃣ FAZER UPLOAD DAS PARTES (S3)
print("\n2. Enviando arquivo para S3...")

with open(VIDEO_PATH, "rb") as f:
    for i, part_info in enumerate(upload_urls):
        part_size = part_info["size"]
        part_url = part_info["url"]
        
        # Lê apenas o chunk correspondente
        chunk = f.read(part_size)
        
        # Upload direto para S3 com headers específicos [citation:2]
        s3_headers = {
            "Content-Type": "video/mp4",
            "x-amz-acl": "private"
        }
        
        r_s3 = requests.put(part_url, data=chunk, headers=s3_headers)
        
        if r_s3.status_code != 200:
            print(f"  Erro na parte {i+1}: {r_s3.status_code}")
            print(r_s3.text)  # AWS retorna XML
            exit(1)
        
        print(f"  Parte {i+1}/{len(upload_urls)} OK")

print("✓ Upload concluído")

# 3️⃣ FINALIZAR (opcional - o sistema detecta automaticamente quando todas as partes chegaram)
# O endpoint /complete não é mais necessário na V4 [citation:2]

# 4️⃣ SALVAR ID PARA CONSULTAR COMENTÁRIOS DEPOIS
with open("asset_id.json", "w") as f:
    json.dump({
        "account_id": ACCOUNT_ID,
        "folder_id": FOLDER_ID,
        "file_id": file_id,
        "file_name": video_name
    }, f, indent=2)

print(f"\n✓ ID do arquivo salvo em asset_id.json")
print(f"  Use este file_id para consultar comentários")