import os
import pandas as pd
import spacy
import json
import xml.etree.ElementTree as ET

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

def extract_action(doc):
    modal_verbs = ["shall", "must", "should", "may", "can", "will"]
    main_verb = None
    modal = None
    
    for token in doc:
        if token.text.lower() in modal_verbs:
            modal = token
            for child in token.children:
                if child.pos_ == "VERB":
                    main_verb = child
                    break
        if main_verb:
            break
    
    if not main_verb and not modal:
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                main_verb = token
                break
    
    if main_verb:
        action_phrase = []
        if modal:
            action_phrase.append(modal.text)
        action_phrase.append(main_verb.text)
        
        # Extract the verb phrase and its complements
        for token in main_verb.subtree:
            if token.dep_ in ["dobj", "pobj", "attr", "prep", "advmod", "acomp", "xcomp", "conj", "agent", "ccomp", "advcl"]:
                # Include the entire subtree of each relevant token
                action_phrase.extend([t.text for t in token.subtree])
        
        # Remove duplicates while preserving order
        action_phrase = list(dict.fromkeys(action_phrase))
        
        return " ".join(action_phrase).strip()
    
    return None



def clean_text(text):
    # Remove enumeration at the beginning of the text
    cleaned = re.sub(r'^\(\d+\)\s*', '', text)
    return cleaned.strip()

def extract_when_condition(doc):
    when_keywords = ['when', 'if', 'while', 'during', 'in case', 'before', 'after', 'prior to']
    for token in doc:
        if token.text.lower() in when_keywords:
            condition = ' '.join([t.text for t in token.subtree])
            return condition
    return "always"  # Default to "always" if no specific condition is found

def extract_value(doc):
    value_pattern = r'\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?(?:\s*[a-zA-Z]+)?'
    matches = re.findall(value_pattern, doc.text)
    if matches:
        return matches
    return None

def create_dataframe(headers):
    data = []
    unique_id = 1
    
    for header, paragraphs in headers.items():
        requirements = extract_requirements(paragraphs)
        for req in requirements:
            cleaned_text = clean_text(text)
            doc = nlp(req.text)
            subject = extract_subject(doc) or "Not found"
            action = extract_action(doc)
            when = extract_when_condition(doc)
            value = extract_value(doc)
            data.append({
                'ID': unique_id,
                'Header': header,
                'Requirement': req.text,
                'Active Subject': subject,
                'Action': action,
                'When': when,
                'Value': value
            })
            unique_id += 1
    
    df = pd.DataFrame(data)
    return df

def convert_to_json(df):
    requirements_json = []
    for _, row in df.iterrows():
        requirements_json.append({
            "raw_requirement": row['Requirement'],
            "active_subject": row['Active Subject'],
            "action": row['Action'],
            "reference": row['Header']
        })
    
    return requirements_json

def main():
    file_path = './2019-20306.xml'  # Path to the loaded file
    print(f"Processing the document: {file_path}")
    requirements_json = process_document(file_path)
    if requirements_json:
        print(json.dumps(requirements_json, ensure_ascii=False, indent=4))
    else:
        print("Could not process the document.")

if __name__ == "__main__":
    main()
