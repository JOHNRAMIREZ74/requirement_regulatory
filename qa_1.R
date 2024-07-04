library(DBI)
library(RPostgres)

# Función para ejecutar consultas SQL con manejo de errores
execute_query <- function(con, query, message) {
  tryCatch({
    dbExecute(con, query)
    cat(paste(message, "- Éxito\n"))
  }, error = function(e) {
    cat(paste(message, "- Error:", e$message, "\n"))
  })
}

# Establecer conexión con la base de datos
con <- dbConnect(RPostgres::Postgres(),
                 dbname = "legal_documents",
                 host = "localhost",
                 port = 5432,
                 user = "john",
                 password = "ESTEFANIA191986")

# Iniciar transacción
dbBegin(con)

# Crear tablas
execute_query(con, "
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    issuing_authority VARCHAR(100),
    issue_date DATE,
    effective_date DATE,
    expiration_date DATE,
    status VARCHAR(20),
    version VARCHAR(20),
    language VARCHAR(10),
    full_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);", "Crear tabla documents")

execute_query(con, "
CREATE TABLE sections (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    section_number VARCHAR(20),
    title VARCHAR(255),
    content TEXT,
    parent_section_id INTEGER REFERENCES sections(id)
);", "Crear tabla sections")

execute_query(con, "
CREATE TABLE named_entities (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    entity_type VARCHAR(50),
    entity_value VARCHAR(255),
    start_position INTEGER,
    end_position INTEGER
);", "Crear tabla named_entities")

execute_query(con, "
CREATE TABLE document_relations (
    id SERIAL PRIMARY KEY,
    source_document_id INTEGER REFERENCES documents(id),
    target_document_id INTEGER REFERENCES documents(id),
    relation_type VARCHAR(50)
);", "Crear tabla document_relations")

execute_query(con, "
CREATE TABLE terms (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    term VARCHAR(100),
    definition TEXT
);", "Crear tabla terms")

execute_query(con, "
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);", "Crear tabla topics")

execute_query(con, "
CREATE TABLE document_topics (
    document_id INTEGER REFERENCES documents(id),
    topic_id INTEGER REFERENCES topics(id),
    PRIMARY KEY (document_id, topic_id)
);", "Crear tabla document_topics")

execute_query(con, "
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    section_id INTEGER REFERENCES sections(id),
    embedding_type VARCHAR(50),
    embedding VECTOR(384)
);", "Crear tabla embeddings")

# Crear índices
execute_query(con, "CREATE INDEX idx_documents_title ON documents(title);", "Crear índice idx_documents_title")
execute_query(con, "CREATE INDEX idx_documents_type ON documents(document_type);", "Crear índice idx_documents_type")
execute_query(con, "CREATE INDEX idx_documents_date ON documents(issue_date);", "Crear índice idx_documents_date")
execute_query(con, "CREATE INDEX idx_sections_document ON sections(document_id);", "Crear índice idx_sections_document")
execute_query(con, "CREATE INDEX idx_named_entities_document ON named_entities(document_id);", "Crear índice idx_named_entities_document")
execute_query(con, "CREATE INDEX idx_named_entities_type ON named_entities(entity_type);", "Crear índice idx_named_entities_type")
execute_query(con, "CREATE INDEX idx_terms_document ON terms(document_id);", "Crear índice idx_terms_document")
execute_query(con, "CREATE INDEX idx_document_topics_document ON document_topics(document_id);", "Crear índice idx_document_topics_document")
execute_query(con, "CREATE INDEX idx_document_topics_topic ON document_topics(topic_id);", "Crear índice idx_document_topics_topic")
execute_query(con, "CREATE INDEX idx_embeddings_document ON embeddings(document_id);", "Crear índice idx_embeddings_document")

# Confirmar la transacción
dbCommit(con)

# Verificar las tablas creadas
tables <- dbListTables(con)
print(paste("Tablas creadas:", paste(tables, collapse = ", ")))

# Cerrar la conexión
dbDisconnect(con)
