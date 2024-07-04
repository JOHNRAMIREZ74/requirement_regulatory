import os
import pandas as pd
import spacy
import json
import xml.etree.ElementTree as ET
import sqlite3
from datetime import datetime

class RequirementsDatabase:
    def __init__(self, db_name='requirements.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Tabla de documentos
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            file_name TEXT,
            processed_date TEXT,
            content TEXT
        )
        ''')

        # Tabla de requisitos
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY,
            document_id INTEGER,
            text TEXT,
            active_subject TEXT,
            reference TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
        ''')

        # Tabla de traducciones INCOSE
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS incose_translations (
            id INTEGER PRIMARY KEY,
            requirement_id INTEGER,
            active_voice TEXT,
            subject TEXT,
            action TEXT,
            description TEXT,
            when_condition TEXT,
            value TEXT,
            FOREIGN KEY (requirement_id) REFERENCES requirements (id)
        )
        ''')

        self.conn.commit()

    def insert_document(self, file_name, content):
        self.cursor.execute('''
        INSERT INTO documents (file_name, processed_date, content)
        VALUES (?, ?, ?)
        ''', (file_name, datetime.now().isoformat(), content))
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_requirement(self, document_id, requirement_json):
        self.cursor.execute('''
        INSERT INTO requirements (document_id, text, active_subject, reference)
        VALUES (?, ?, ?, ?)
        ''', (document_id, requirement_json['text'], requirement_json['active_subject'], requirement_json['reference']))
        requirement_id = self.cursor.lastrowid

        incose = requirement_json['incose_transliteration']
        self.cursor.execute('''
        INSERT INTO incose_translations (requirement_id, active_voice, subject, action, description, when_condition, value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (requirement_id, incose['active_voice'], incose['subject'], incose['action'], incose['description'], incose['when'], incose['value']))

        self.conn.commit()
        return requirement_id

    def get_requirements_by_document(self, document_id):
        self.cursor.execute('''
        SELECT r.id, r.text, r.active_subject, r.reference, 
               i.active_voice, i.subject, i.action, i.description, i.when_condition, i.value
        FROM requirements r
        JOIN incose_translations i ON r.id = i.requirement_id
        WHERE r.document_id = ?
        ''', (document_id,))
        return self.cursor.fetchall()

    def get_all_documents(self):
        self.cursor.execute('SELECT id, file_name, processed_date FROM documents')
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

def process_and_store_requirements(db, file_name, requirements_json):
    file_content = read_file(file_name)
    document_id = db.insert_document(file_name, file_content)

    for requirement in requirements_json:
        db.insert_requirement(document_id, requirement)

# Cargar el modelo de spaCy para inglés
nlp = spacy.load("en_core_web_sm")

def read_file(file_path):
    print(f"Attempting to read the file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f"File read successfully. Content length: {len(content)}")
        return content
    except Exception as e:
        print(f"Error reading the file: {str(e)}")
        return None

def parse_xml(content):
    print("Parsing XML structure")
    try:
        root = ET.fromstring(content)
        return root
    except ET.ParseError as e:
        print(f"Error parsing XML: {str(e)}")
        return None

def extract_structure(element, structure=None, path=""):
    if structure is None:
        structure = {}
    
    for child in element:
        new_path = f"{path}/{child.tag}"
        if child.tag not in structure:
            structure[child.tag] = {"count": 1, "paths": [new_path]}
        else:
            structure[child.tag]["count"] += 1
            if new_path not in structure[child.tag]["paths"]:
                structure[child.tag]["paths"].append(new_path)
        
        extract_structure(child, structure, new_path)
    
    return structure

def print_structure(structure):
    print("XML document structure:")
    for tag, info in sorted(structure.items()):
        print(f"Tag: {tag}")
        print(f"  Count: {info['count']}")
        print(f"  Paths:")
        for path in sorted(info['paths']):
            print(f"    {path}")
        print()

def extract_headers_and_paragraphs(root):
    print("Extracting headers and paragraphs")
    headers = {}
    current_header = "Main Document"
    headers[current_header] = []

    for elem in root.iter():
        if elem.tag.lower() in ['hd', 'subject', 'sectno']:
            current_header = elem.text.strip() if elem.text else "Untitled Header"
            headers[current_header] = []
            print(f"Header found: {current_header}")
        elif elem.tag.lower() in ['p', 'text', 'tnote', 'e']:
            paragraph = elem.text.strip() if elem.text else ""
            if paragraph:
                headers[current_header].append(paragraph)
                print(f"Paragraph added to '{current_header}': {paragraph[:50]}...")

    print(f"Number of headers extracted: {len(headers)}")
    return headers

def extract_requirements(paragraphs):
    requirements = []
    requirement_keywords = ["shall", "must", "required", "will", "should", "may", "can", "is required to", "are required to", "it is necessary", "needs to"]
    for paragraph in paragraphs:
        doc = nlp(paragraph)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in requirement_keywords):
                requirements.append(sentence)
    return requirements
  


def create_dataframe(headers):
    data = []
    unique_id = 1
    
    for header, paragraphs in headers.items():
        requirements = extract_requirements(paragraphs)
        for req in requirements:
            doc = nlp(req)
            subjects = [token.text for token in doc if token.pos_ in ['NOUN', 'PRON']]
            subject = subjects[0] if subjects else "Not found"
            data.append({
                'ID': unique_id,
                'Header': header,
                'Requirement': req,
                'Active Subject': subject
            })
            unique_id += 1
    
    df = pd.DataFrame(data)
    return df

def convert_to_json(df):
    requirements_json = []
    for _, row in df.iterrows():
        requirements_json.append({
            "text": row['Requirement'],
            "active_subject": row['Active Subject'],
            "reference": row['Header'],
            "incose_transliteration": {
                "active_voice": f"{row['Active Subject']} shall",
                "subject": row['Active Subject'],
                "action": "perform the required action",
                "description": row['Requirement'],
                "when": "always",
                "value": None
            }
        })
    
    return requirements_json

def process_document(file_path):
    content = read_file(file_path)
    if content is None:
        return None
    
    root = parse_xml(content)
    if root is None:
        return None
    
    structure = extract_structure(root)
    print_structure(structure)
    
    headers = extract_headers_and_paragraphs(root)
    if not headers:
        print("No headers found in the document")
        return None
    
    df = create_dataframe(headers)
    if df.empty:
        print("No requirements found in the document")
        return None

    requirements_json = convert_to_json(df)
    
    return requirements_json

def main():
    file_path = './2019-20306.xml'
    print(f"Processing the document: {file_path}")
    requirements_json = process_document(file_path)
    
    if requirements_json:
        db = RequirementsDatabase()
        process_and_store_requirements(db, file_path, requirements_json)
        db.close()
        print("Requirements stored in the database.")
    else:
        print("Could not process the document.")

if __name__ == "__main__":
    main()
