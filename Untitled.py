from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import spacy
from bs4 import BeautifulSoup
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar el modelo de spaCy para español
nlp = spacy.load("es_core_news_sm")

def get_html_from_url(url):
    options = webdriver.SafariOptions()
    driver = webdriver.Safari(options=options)
    
    try:
        logging.info(f"Opening URL: {url}")
        driver.get(url)
        # Esperar hasta que el cuerpo de la página esté presente
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        html = driver.page_source
        logging.info("HTML obtained successfully.")
        return html
    except Exception as e:
        logging.error(f"Error al obtener el contenido: {e}")
        return None
    finally:
        driver.quit()
        logging.info("Browser closed.")

def extract_headers_and_paragraphs(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    headers = {}
    current_header = None
    
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        if element.name.startswith('h'):
            current_header = element.text.strip()
            headers[current_header] = []
            logging.info(f"Found header: {current_header}")
        elif element.name == 'p' and current_header:
            paragraph = element.text.strip()
            if paragraph:  # Solo agregar párrafos no vacíos
                headers[current_header].append(paragraph)
                logging.info(f"Found paragraph under {current_header}: {paragraph[:60]}...")
    
    return headers

def create_dataframe(headers):
    data = []
    unique_id = 1
    
    for header, paragraphs in headers.items():
        for paragraph in paragraphs:
            doc = nlp(paragraph)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            data.append({
                'ID': unique_id,
                'Header': header,
                'Paragraph': paragraph,
                'Sentences': sentences
            })
            unique_id += 1
    
    df = pd.DataFrame(data)
    logging.info(f"DataFrame created with {len(df)} rows")
    return df

def process_webpage(url):
    html = get_html_from_url(url)
    if not html:
        logging.error("Failed to obtain HTML.")
        return None
    
    logging.debug("HTML fragment: %s", html[:1000])
    
    headers = extract_headers_and_paragraphs(html)
    if not headers:
        logging.warning("No headers found.")
        return None
    
    df = create_dataframe(headers)
    
    return df

if __name__ == "__main__":
    url = 'https://www.federalregister.gov/documents/full_text/text/2019/10/01/2019-20306.txt'
    df = process_webpage(url)
    if df is not None:
        print(df.head())
        # Opcionalmente, guardar el DataFrame en un archivo CSV
        # df.to_csv('resultado_scraping.csv', index=False)
    else:
        logging.error("No se pudo procesar la página web.")
