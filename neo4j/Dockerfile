FROM neo4j:neo4j:5.23-enterprise

# APOC-Plugin aktivieren
ENV NEO4J_PLUGINS='[ "apoc" ]'
ENV NEO4J_dbms_security_procedures_unrestricted apoc.*
ENV NEO4J_dbms_mode=CORE

# APOC-Plugin kopieren
COPY ./apoc-5.22.0-core.jar /var/lib/neo4j/plugins

# Ressourcenhinweise für den Container
ENV NEO4J_dbms_memory_heap_initial__size=2G
ENV NEO4J_dbms_memory_heap_max__size=2G
ENV NEO4J_dbms_memory_pagecache__size=6G

EXPOSE 7474 7687
