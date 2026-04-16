# Usa uma versão oficial e leve do Python
FROM python:3.9-slim

# Define a pasta de trabalho dentro do contêiner
WORKDIR /app

# Copia apenas as dependências primeiro (otimiza o cache do Docker)
COPY requirements.txt .

# Instala as bibliotecas
RUN pip install --no-cache-dir -r requirements.txt

# Copia o seu script para dentro do contêiner
COPY sync_secure_cloud.py .

# Comando que mantém o contêiner de pé rodando o script
CMD ["python", "sync_secure_cloud.py"]