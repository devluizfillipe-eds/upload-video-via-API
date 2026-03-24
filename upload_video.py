import requests
import os
import json
import sys
from datetime import datetime

# ============ CONFIGURAÇÕES (EDITAR AQUI) ============
ACCESS_TOKEN = "Acesstoken"  # ← COLE SEU TOKEN ENTRE AS ASPAS
ACCOUNT_ID = "id acount"  # ← COLE SEU ACCOUNT_ID
FOLDER_ID = "folder id"  # ← COLE O ROOT_FOLDER_ID
# =====================================================

# Arquivo de mapeamento (único arquivo de controle)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPEAMENTO_FILE = os.path.join(SCRIPT_DIR, "mapeamento_videos.json")

def carregar_mapeamento():
    """Carrega o mapeamento de vídeos locais para file_ids do Frame.io"""
    if os.path.exists(MAPEAMENTO_FILE):
        with open(MAPEAMENTO_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_mapeamento(mapeamento):
    """Salva o mapeamento de vídeos locais para file_ids"""
    with open(MAPEAMENTO_FILE, 'w') as f:
        json.dump(mapeamento, f, indent=2)

def upload_video(caminho_video):
    """Faz o upload do vídeo para o Frame.io e registra no mapeamento"""
    
    if not os.path.exists(caminho_video):
        print(f"❌ Arquivo não encontrado: {caminho_video}")
        return None

    # Converte para caminho absoluto
    caminho_video = os.path.abspath(caminho_video)
    nome_video = os.path.basename(caminho_video)
    tamanho = os.path.getsize(caminho_video)
    
    print(f"\n📹 Vídeo: {nome_video}")
    print(f"📦 Tamanho: {tamanho:,} bytes")
    print(f"📁 Caminho: {caminho_video}")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 1. Criar arquivo no Frame.io
    print("\n📝 Criando registro...")
    url = f"https://api.frame.io/v4/accounts/{ACCOUNT_ID}/folders/{FOLDER_ID}/files"

    payload = {
        "data": {
            "name": nome_video,
            "file_size": tamanho,
            "media_type": "video/mp4"
        }
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
    
    # 3. Salvar no mapeamento
    mapeamento = carregar_mapeamento()
    mapeamento[caminho_video] = file_id
    salvar_mapeamento(mapeamento)
    
    print(f"\n📌 File ID: {file_id}")
    print(f"✅ Mapeamento salvo: {caminho_video} -> {file_id}")
    
    return file_id

def listar_mapeamento():
    """Mostra todos os vídeos mapeados"""
    mapeamento = carregar_mapeamento()
    
    if not mapeamento:
        print("\n📭 Nenhum vídeo mapeado.")
        return
    
    print("\n📋 VÍDEOS MAPEADOS:")
    print("-" * 70)
    for caminho, file_id in mapeamento.items():
        nome = os.path.basename(caminho)
        print(f"🎬 {nome}")
        print(f"   ID: {file_id}")
        print(f"   Caminho: {caminho}")
        print("-" * 70)

# ============ EXECUÇÃO PRINCIPAL ============
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload de vídeo para Frame.io')
    parser.add_argument('video', nargs='?', help='Caminho do arquivo de vídeo')
    parser.add_argument('--listar', '-l', action='store_true', help='Listar vídeos mapeados')
    
    args = parser.parse_args()
    
    if args.listar:
        listar_mapeamento()
        sys.exit(0)
    
    if not args.video:
        print("❌ Informe o caminho do vídeo")
        print("\nUso:")
        print("  python upload_video.py C:\\caminho\\para\\video.mp4")
        print("  python upload_video.py --listar")
        sys.exit(1)
    
    upload_video(args.video)