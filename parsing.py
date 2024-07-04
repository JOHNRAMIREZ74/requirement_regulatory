import requests
from bs4 import BeautifulSoup
import re
import spacy
import pandas as pd
from uuid import uuid4

# Cargar el modelo de spaCy en español
nlp = spacy.load("es_core_news_sm")

# 1. Obtener el contenido del documento
url = "https://gestornormativo.creg.gov.co/Publicac.nsf/1c09d18d2d5ffb5b05256eee00709c02/216d73e5d623a9c40525785a007a6334.html"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# 2. Extraer el texto relevante
text = soup.get_text()

# 3. Preprocesamiento del texto
def preprocess_text(text):
    # Eliminar espacios en blanco múltiples
    text = re.sub(r'\s+', ' ', text)
    # Eliminar caracteres especiales, pero mantener puntuación importante
    text = re.sub(r'[^\w\s.,;:?!]', '', text)
    return text

preprocessed_text = preprocess_text(text)

# 4. Identificar y extraer unidades semánticas (oraciones y párrafos)
def extract_semantic_units(text):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    return sentences, paragraphs

sentences, paragraphs = extract_semantic_units(preprocessed_text)

# 5. Crear dataframes para almacenar las unidades semánticas
df_units = pd.DataFrame(columns=['id', 'tipo', 'texto', 'documento_id', 'posicion_en_documento'])
df_attributes = pd.DataFrame(columns=['unidad_id', 'tipo_atributo', 'valor'])
df_keywords = pd.DataFrame(columns=['unidad_id', 'palabra'])
df_subjects = pd.DataFrame(columns=['unidad_id', 'sujeto', 'tipo_sujeto'])
df_verbs = pd.DataFrame(columns=['unidad_id', 'verbo', 'tipo_verbo'])

# 6. Procesar y almacenar unidades semánticas
documento_id = 1  # Asumimos que este es el ID del documento actual

def process_semantic_unit(text, unit_type, position):
    unit_id = str(uuid4())
    doc = nlp(text)
    
    # Añadir unidad semántica
    df_units.loc[len(df_units)] = [unit_id, unit_type, text, documento_id, position]
    
    # Extraer atributos
    df_attributes.loc[len(df_attributes)] = [unit_id, 'num_tokens', len(doc)]
    df_attributes.loc[len(df_attributes)] = [unit_id, 'num_entidades', len(doc.ents)]
    
    # Extraer palabras clave (sustantivos, verbos, adjetivos)
    keywords = [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ']]
    for keyword in set(keywords):
        df_keywords.loc[len(df_keywords)] = [unit_id, keyword]
    
    # Extraer sujetos y verbos
    for token in doc:
        if token.dep_ == 'nsubj':
            df_subjects.loc[len(df_subjects)] = [unit_id, token.text, token.pos_]
        elif token.pos_ == 'VERB':
            df_verbs.loc[len(df_verbs)] = [unit_id, token.lemma_, token.dep_]

# Procesar oraciones
for i, sentence in enumerate(sentences):
    process_semantic_unit(sentence, 'oracion', i)

# Procesar párrafos
for i, paragraph in enumerate(paragraphs):
    process_semantic_unit(paragraph, 'parrafo', i)

# 7. Imprimir algunos resultados para verificación
print("Muestra de unidades semánticas:")
print(df_units.head())
print("\nMuestra de atributos:")
print(df_attributes.head())
print("\nMuestra de palabras clave:")
print(df_keywords.head())
print("\nMuestra de sujetos:")
print(df_subjects.head())
print("\nMuestra de verbos:")
print(df_verbs.head())

# 8. Guardar los dataframes como CSV para su posterior inserción en la base de datos
df_units.to_csv('unidades_semanticas.csv', index=False)
df_attributes.to_csv('atributos_unidad.csv', index=False)
df_keywords.to_csv('palabras_clave.csv', index=False)
df_subjects.to_csv('sujetos.csv', index=False)
df_verbs.to_csv('verbos.csv', index=False)

print("\nLos archivos CSV han sido generados para su inserción en la base de datos.")
