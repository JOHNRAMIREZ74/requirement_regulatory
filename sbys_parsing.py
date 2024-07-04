import spacy
import sqlite3


# Paso 1: Análisis Léxico: En este paso, dividimos el texto en párrafos, oraciones y palabras. Utilizaremos spaCy para esto.

# Cargar el modelo de spaCy en español
nlp = spacy.load("es_core_news_sm")

# Texto de ejemplo
text = """
CONSIDERANDO
Que la producción normativa ocupa un espacio central en la implementación de políticas públicas, siendo el medio a través del cual se estructuran los instrumentos jurídicos que materializan en gran parte las decisiones del Estado.
Que la racionalización y simplificación del ordenamiento jurídico es una de las principales herramientas para asegurar la eficiencia económica y social del sistema legal y para afianzar la seguridad jurídica.
Que constituye una política pública gubernamental la simplificación y compilación orgánica del sistema nacional regulatorio.
Que la facultad reglamentaria incluye la posibilidad de compilar normas de la misma naturaleza.
"""

# Procesar el texto con spaCy
doc = nlp(text)


# Dividir el texto en párrafos, oraciones y palabras
paragraphs = text.split('\n')
sentences = [sent for sent in doc.sents]
#words = [token.text for token in doc]

print("Párrafos:", paragraphs)
print("Oraciones:", sentences)
#print("Palabras:", words)


# Paso 2: Análisis Sintáctico: El análisis sintáctico involucra el análisis de la estructura gramatical de las oraciones.

for sent in sentences:
    print(f"\nOración: {sent}")
    for token in sent:
        print(f"{token.text} -> {token.dep_} ({token.head.text})")
        
# Paso 3: Análisis Semántico: El análisis semántico implica extraer el significado de las palabras y frases. Podemos utilizar las dependencias sintácticas y las entidades nombradas.

for sent in sentences:
    print(f"\nOración: {sent}")
    for ent in sent.ents:
        print(f"Entidad nombrada: {ent.text} ({ent.label_})")

# Paso 4: Integración de Discurso: Este paso toma en cuenta el contexto del texto.

for sent in sentences:
    print(f"\nOración: {sent}")
    for token in sent:
        if token.dep_ == "nsubj":
            subject = token.text
            print(f"Sujeto: {subject}")

# Paso 5: Análisis Pragmático: El análisis pragmático se enfoca en la interpretación y uso del lenguaje en contextos específicos.

for sent in sentences:
    # Aquí se puede incluir lógica adicional para analizar el contexto y la intención del texto
    print(f"\nOración: {sent}")
    print("Contexto e interpretación pragmática aún por definir.")

# Paso 6: Integración y Almacenamiento de Resultados: Ahora, integramos todos estos pasos y almacenamos los resultados en una base de datos estructurada. Primero, definimos la estructura semántica y luego almacenamos los resultados.

# Definir la Estructura Semántica
import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('requirements.db')
c = conn.cursor()

# Crear la tabla para almacenar los requerimientos
c.execute('''
CREATE TABLE IF NOT EXISTS parsing_output (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT,
    action TEXT,
    object TEXT,
    condition TEXT,
    restriction TEXT,
    raw_text TEXT
)
''')
conn.commit()

# Función para estructurar y almacenar los requerimientos
def store_requirements(sent, subject, action, obj, condition=None, restriction=None):
    c.execute('''
    INSERT INTO parsing_output (subject, action, object, condition, restriction, raw_text)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (subject, action, obj, condition, restriction, sent.text))
    conn.commit()

# Ejemplo de almacenamiento
for sent in sentences:
    subject = "El sistema"  # Esto debe ser extraído dinámicamente
    action = "debe proporcionar"
    obj = "acceso a los usuarios registrados"
    store_requirements(sent, subject, action, obj)

# Cerrar la conexión
conn.close()


