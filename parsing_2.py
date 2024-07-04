import os
from openai import OpenAI

# Función para obtener la clave API
def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Por favor, introduce tu clave API de OpenAI: ").strip()
    return api_key

# Inicializar el cliente de OpenAI
def initialize_openai_client():
    api_key = get_api_key()
    if not api_key:
        raise ValueError("No se ha proporcionado una clave API válida.")
    return OpenAI(api_key=api_key)

# Función para analizar texto con la API de OpenAI
def analyze_with_gpt(client, text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en análisis de texto legal. Analiza el siguiente documento y proporciona un resumen ejecutivo, estructura del documento, palabras clave, temas principales y cualquier otra información relevante."},
                {"role": "user", "content": text}
            ],
            temperature=0.7
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"Se produjo un error al analizar el texto: {str(e)}")
        return None

# Ejemplo de texto que podría venir de una página web
sample_text = """
[Aquí iría el texto extraído de la página web. Por ejemplo:]

RESOLUCIÓN CREG-025 DE 1995
(13 de julio)
Diario Oficial No. 41.937, del 24 de julio de 1995
Por la cual se establece el Código de Redes, como parte del Reglamento de Operación del Sistema Interconectado Nacional.

LA COMISIÓN DE REGULACIÓN DE ENERGÍA Y GAS,

en ejercicio de sus atribuciones legales, en especial las conferidas por las Leyes 142 y 143 de 1994, y los decretos 1524 y 2253 de 1994.

CONSIDERANDO:

Que la Ley 143 de 1994 en su artículo 23 señala que para "definir el reglamento de operación se tendrán en cuenta los criterios que establezca la Comisión de Regulación de Energía y Gas";
"""

print("Inicializando el cliente de OpenAI...")
try:
    client = initialize_openai_client()
    print("Analizando el texto...")
    analysis = analyze_with_gpt(client, sample_text)
    if analysis:
        print("\nAnálisis del documento:")
        print(analysis)
except ValueError as e:
    print(f"Error: {str(e)}")
    print("Asegúrate de configurar la variable de entorno OPENAI_API_KEY o proporcionar la clave API cuando se te solicite.")
except Exception as e:
    print(f"Se produjo un error inesperado: {str(e)}")
