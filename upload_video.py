import requests
import os
import json
import sys
from datetime import datetime

# ============ CONFIGURAÇÕES (EDITAR AQUI) ============
ACCESS_TOKEN = "SEU_TOKEN_AQUI"  # ← COLE SEU TOKEN ENTRE AS ASPAS
ACCOUNT_ID = "SEU_ACCOUNT_ID_AQUI"  # ← COLE SEU ACCOUNT_ID
FOLDER_ID = "SEU_FOLDER_ID_AQUI"  # ← COLE O ROOT_FOLDER_ID
# =====================================================

# Arquivos de controle
HISTORICO_FILE = "historico_uploads.json"
ULTIMO_FILE = "ultimo_upload.json"

def carregar_historico():
    """Carrega o histórico de uploads ou cria um novo"""
    if os.path.exists(HISTORICO_FILE):
        with open(HISTORICO_FILE, 'r') as f:
            return json.load(f)
    return {"uploads": [], "ultimo": None}

def salvar_historico(historico):
    """Salva o histórico de uploads"""
    with open(HISTORICO_FILE, 'w') as f:
        json.dump(historico, f, indent=2)

def salvar_ultimo(file_id, nome_video):
    """Salva o último upload em arquivo separado (para compatibilidade)"""
    with open(ULTIMO_FILE, 'w') as f:
        json.dump({
            "file_id": file_id,
            "file_name": nome_video,
            "upload_time": datetime.now().isoformat()
        }, f, indent=2)

def upload_video(caminho_video):
    """Faz o upload do vídeo para o Frame.io"""
    
    if not os.path.exists(caminho_video):
        print(f"❌ Arquivo não encontrado: {caminho_video}")
        return None

    nome_video = os.path.basename(caminho_video)
    tamanho = os.path.getsize(caminho_video)
    
    print(f"\n📹 Vídeo: {nome_video}")
    print(f"📦 Tamanho: {tamanho:,} bytes")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 1. Criar arquivo no Frame.io
    print("\n📝 Criando registro...")
    url = f"https://api.frame.io/v4/accounts/{ACCOUNT_ID}/folders/{FOLDER_ID}/files"
    
    payload = {
        "name": nome_video,
        "file_size": tamanho,
        "media_type": "video/mp4"
    }
    
    r = requests.post(url, headers=headers, json=payload)
    
    if r.status_code != 201:
        print(f"❌ Erro ao criar: {r.status_code}")
        print(r.text)
        return None
    
    data = r.json()["data"]
    file_id = data["id"]
    upload_urls = data["upload_urls"]
    
    print(f"✅ Registro criado. File ID: {file_id}")
    
    # 2. Upload das partes
    print(f"\n📤 Enviando ({len(upload_urls)} parte(s))...")
    
    with open(caminho_video, "rb") as f:
        for i, parte in enumerate(upload_urls):
            print(f"   Parte {i+1}/{len(upload_urls)}...")
            chunk = f.read(parte["size"])
            
            s3_headers = {
                "Content-Type": "video/mp4",
                "x-amz-acl": "private"
            }
            
            r_s3 = requests.put(parte["url"], data=chunk, headers=s3_headers)
            
            if r_s3.status_code not in [200, 204]:
                print(f"❌ Erro na parte {i+1}")
                return None
    
    print("\n✅ Upload concluído!")
    
    # 3. Salvar no histórico
    historico = carregar_historico()
    
    novo_registro = {
        "file_id": file_id,
        "nome": nome_video,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "caminho_original": caminho_video,
        "tamanho": tamanho
    }
    
    historico["uploads"].append(novo_registro)
    historico["ultimo"] = file_id
    salvar_historico(historico)
    
    # 4. Salvar último upload (compatibilidade)
    salvar_ultimo(file_id, nome_video)
    
    print(f"\n📌 File ID: {file_id}")
    print(f"📊 Total de uploads no histórico: {len(historico['uploads'])}")
    
    return file_id

def listar_uploads(historico):
    """Mostra os últimos uploads"""
    if not historico["uploads"]:
        print("\n📭 Nenhum upload encontrado.")
        return
    
    print("\n📋 ÚLTIMOS UPLOADS:")
    print("-" * 60)
    
    # Mostra os 10 últimos
    for i, up in enumerate(historico["uploads"][-10:], 1):
        marcador = "▶️" if up["file_id"] == historico["ultimo"] else "  "
        print(f"{marcador} {i}. {up['nome']}")
        print(f"     ID: {up['file_id']}")
        print(f"     Data: {up['data']}")
    print("-" * 60)

# ============ EXECUÇÃO PRINCIPAL ============
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload de vídeo para Frame.io')
    parser.add_argument('video', nargs='?', help='Caminho do arquivo de vídeo')
    parser.add_argument('--listar', '-l', action='store_true', help='Listar uploads anteriores')
    
    args = parser.parse_args()
    
    if args.listar:
        historico = carregar_historico()
        listar_uploads(historico)
        sys.exit(0)
    
    if not args.video:
        print("❌ Informe o caminho do vídeo")
        print("\nUso:")
        print("  python upload_video.py C:\\caminho\\para\\video.mp4")
        print("  python upload_video.py --listar")
        sys.exit(1)
    
    upload_video(args.video)