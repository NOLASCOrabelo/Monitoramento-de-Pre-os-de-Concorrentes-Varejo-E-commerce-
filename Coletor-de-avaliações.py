import csv 
from google_play_scraper import reviews
import datetime
        
        # --- Configuração ---
        # Troque pelo ID do app que você quer analisar
APP_ID = 'com.spotify.music' 
QUANTIDADE = 100
        # --------------------
        
print(f"Iniciando coleta de {QUANTIDADE} avaliações para o app: {APP_ID}")
        
try:
            # Coleta os dados
            # sort=Sort.NEWEST (pega os mais recentes)
            result, _ = reviews(
                APP_ID,
                lang='pt',
                country='br',
                count=QUANTIDADE
            )
        
            if not result:
                print("Nenhuma avaliação foi encontrada.")
                exit()
        
            print(f"Coleta concluída. Total de avaliações: {len(result)}")
            
            # Gera um nome de arquivo único com a data
            data_hoje = datetime.date.today().strftime('%Y-%m-%d')
            nome_arquivo = f"avaliacoes_{APP_ID}_{data_hoje}.csv"
            
            print(f"Salvando dados em {nome_arquivo}...")
            
            # Abre o arquivo para escrita
            with open(nome_arquivo, 'w', newline='', encoding='utf-8') as f:
                
                # Cria o "escritor" de CSV
                writer = csv.writer(f)
                
                # Escreve o cabeçalho
                # (Nota: Play Store não tem "Título", usamos "Texto")
                writer.writerow(['Data', 'Nota', 'Texto', 'ID_Usuario', 'ID_Avaliacao'])
                
                # Itera sobre cada avaliação na lista 'result'
                for avaliacao in result:
                    # Extrai os dados
                    data = avaliacao['at']
                    nota = avaliacao['score']
                    texto = avaliacao['content']
                    usuario = avaliacao['userName']
                    review_id = avaliacao['reviewId']
                    
                    # Escreve a linha no arquivo CSV
                    writer.writerow([data, nota, texto, usuario, review_id])
            
            print(f"Sucesso! Arquivo '{nome_arquivo}' salvo.")
        
except Exception as e:
            print(f"\nOcorreu um erro inesperado:")
            print(e)
            print("Verifique se o APP_ID está correto e tente novamente.")
        
        