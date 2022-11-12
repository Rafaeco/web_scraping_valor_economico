import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import pandas as pd
import boto3
import os
from botocore.exceptions import NoCredentialsError 
import logging 

# criando as listas com os datas desejadas
hoje = date.today()
data_link = []
data_data = []
for menos in range(1, 8):
    data = hoje - timedelta(days=menos)
    data_data.append(data.strftime("%d/%m/%Y"))
    number = int(data.strftime("%Y%m%d"))
    data_link.append(number)
    
lista_links = []
lista_titulo = []
lista_subtitulo = []
lista_publicacao = []
lista_categoria = []
for data in data_link:
    # alterando a url para a data desejada
    url = f'https://valor.globo.com/impresso/{data}'
    site = requests.get(url)
    soup = BeautifulSoup(site.content, 'html.parser')
    n_noticias = len(soup.find_all('div', attrs={'class': 'newsfeed-post__title'}))
    # iterando através de cada notícia
    for n in range(n_noticias):
        # capturando o link da notícia
        for href in soup.find_all('div', attrs={'class': 'newsfeed-post__title'})[n].find_all('a'):
            link_noticia = href.get('href')
        # capturando as informações adicionais da notícia
        # aqui, encontram-se informações sobre a data de publicação e a categoria da notícia
        info_adicionais  = soup.find_all('div', attrs={'class': 'newsfeed-post__meta'})[n].get_text()
        # verificando se a data de publicação está disponível
        if info_adicionais == ' ':
            # se não estiver, o script entrará na notícia para capturar a data de publicação
            site_noticia = requests.get(link_noticia)
            soup_noticia = BeautifulSoup(site_noticia.content, 'html.parser')
            data_publicacao = soup_noticia.find('p', attrs={'class': 'content-publication-data__updated'}).get_text()[:12].strip()
            categoria = 'Outros'
        else:
            # se a data estiver disponível, será capturada diretamente
            data_publicacao = info_adicionais[:12].strip()
            categoria = info_adicionais[24:].strip()
        # CHECKPOINT DE VERICAÇÃO: 
        # caso a data de publicação da matéria esteja dentro do período desejado, as informações sobre essa matéria serão armazenadas
        if data_publicacao in data_data:
            lista_categoria.append(categoria)
            lista_publicacao.append(data_publicacao)
            lista_links.append(link_noticia)
            lista_titulo.append(soup.find_all('div', attrs={'class': 'newsfeed-post__title'})[n].get_text().strip())
            # verificação da existência do subtitulo
            try:
                lista_subtitulo.append(soup.find_all('div', attrs={'class': 'newsfeed-post__subtitle'})[n].get_text().strip())
            except:
                lista_subtitulo.append('não possui')

# criação de um dataframe com as informações coletadas
tabela = pd.DataFrame({'titulo': lista_titulo, 'subtitulo': lista_subtitulo, 'publicacao': lista_publicacao, 'categoria': lista_categoria, 'link': lista_links})
tabela.sort_values(by='publicacao', inplace=True)
nome_arquivo = f'Tabela_noticias_{data_link[0]}-{data_link[-1]}.csv'
# criando um csv com as informações coletadas
tabela.to_csv(nome_arquivo, sep=';', escapechar='\\', header=False, index=False)


#UPLOAD DO ARQUIVO PARA O S3
#habilite o código caso deseje que o csv seja exportado para um bucket do S3
#ACCESS_KEY = '<sua_chave_de_acesso' 
#SECRET_KEY = '<sua_chave_de_segurança>' 
#def upload_to_aws(local_file, bucket, s3_file):
#    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
#                      aws_secret_access_key=SECRET_KEY)
#    try:
#        s3.upload_file(local_file, bucket, s3_file)
#        print("Upload Successful")
#        return True
#    except FileNotFoundError:
#        print("The file was not found")
#        return False
#    except NoCredentialsError:
#        print("Credentials not available")
#        return False
#uploaded = upload_to_aws(nome_arquivo, '<bucket_destinatário>', nome_arquivo)