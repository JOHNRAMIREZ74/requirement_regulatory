#!/bin/bash

# Reiniciar el servidor de PostgreSQL
brew services restart postgresql@14

# Conectar a PostgreSQL y ejecutar comandos SQL
psql -d postgres <<EOF
CREATE DATABASE legal_documents OWNER john;
GRANT ALL PRIVILEGES ON DATABASE legal_documents TO john;
\l
\du
EOF

# Conectar a la nueva base de datos usando el nuevo usuario
psql -U john -d legal_documents

