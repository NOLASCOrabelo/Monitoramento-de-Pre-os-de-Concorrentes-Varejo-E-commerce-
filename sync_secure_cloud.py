import os
import io
import logging
import hashlib
import boto3
import time
import schedule
from PIL import Image
from cryptography.fernet import Fernet
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

# --- CONFIGURAÇÕES ---
# 1. Google Drive: Caminho para o JSON da sua Service Account
GOOGLE_SERVICE_ACCOUNT_FILE = 'credentials.json'
# 2. Filebase (S3): Suas chaves de acesso
FILEBASE_ACCESS_KEY = 'SUA_KEY_AQUI'
FILEBASE_SECRET_KEY = 'SEU_SECRET_AQUI'
FILEBASE_BUCKET_NAME = 'nome-do-seu-bucket'
# 3. Criptografia: Gere uma com Fernet.generate_key() e cole aqui
ENCRYPTION_KEY = b'SUA_CHAVE_FERNET_GERADA_AQUI='

# Configuração do LOG
logging.basicConfig(
    filename='sync_blockchain.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Inicialização dos Clientes
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive.readonly'])
    return build('drive', 'v3', credentials=creds)

def get_filebase_client():
    return boto3.client(
        's3',
        endpoint_url='https://s3.filebase.com',
        aws_access_key_id=FILEBASE_ACCESS_KEY,
        aws_secret_access_key=FILEBASE_SECRET_KEY
    )

def limpar_metadados(input_stream, filename):
    """Remove EXIF e metadados de imagens."""
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        try:
            img = Image.open(input_stream)
            output = io.BytesIO()
            img_data = list(img.getdata())
            img_nova = Image.new(img.mode, img.size)
            img_nova.putdata(img_data)
            img_nova.save(output, format=img.format)
            return output.getvalue()
        except Exception as e:
            logging.error(f"Erro ao limpar metadados de {filename}: {e}")
    return input_stream.getvalue()

def criptografar_dados(dados):
    """Aplica criptografia Fernet (AES)."""
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(dados)

def arquivo_existe_na_nuvem(s3_client, filename):
    """Verifica se o arquivo (com extensão .crypt) já existe no Filebase."""
    try:
        s3_client.head_object(Bucket=FILEBASE_BUCKET_NAME, Key=f"{filename}.crypt")
        return True
    except:
        return False

def sync():
    logging.info("Iniciando rotina de sincronização...")
    drive_service = get_drive_service()
    s3_client = get_filebase_client()

    try:
        # Lista arquivos do Drive (apenas arquivos, ignora pastas)
        results = drive_service.files().list(
            q="mimeType != 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)"
        ).execute()
        items = results.get('files', [])

        if not items:
            logging.info("Nenhum arquivo encontrado no Google Drive.")
            return

        for item in items:
            file_name = item['name']
            file_id = item['id']

            # 1. Verificar duplicidade
            if arquivo_existe_na_nuvem(s3_client, file_name):
                logging.info(f"Pulando: {file_name} já existe no Filebase.")
                continue

            logging.info(f"Processando: {file_name}")

            # 2. Download em memória (evita rastro no disco local)
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            # 3. Limpeza de Metadados
            dados_limpos = limpar_metadados(fh, file_name)

            # 4. Criptografia
            dados_finais = criptografar_dados(dados_limpos)

            # 5. Upload para Filebase (Blockchain/IPFS)
            s3_client.put_object(
                Bucket=FILEBASE_BUCKET_NAME,
                Key=f"{file_name}.crypt",
                Body=dados_finais
            )
            logging.info(f"Sucesso: {file_name} sincronizado e criptografado.")

    except Exception as e:
        logging.error(f"Erro crítico no script: {e}")

if __name__ == "__main__":
    logging.info("Iniciando o Worker de Sincronização em Docker...")
    
    
    sync() 
    
  
    schedule.every(1).hours.do(sync)
    
    # Mantém o contêiner rodando
    while True:
        schedule.run_pending()
        time.sleep(60)