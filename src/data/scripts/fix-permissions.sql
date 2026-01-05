-- Script para corrigir permissões do PostgreSQL no schema schema_superleme
-- Execute este script no banco de dados superleme para corrigir permissões

-- Garantir que postgres é o owner do schema
ALTER SCHEMA schema_superleme OWNER TO postgres;

-- Aplicar permissões no schema para os usuários postgres, zotonic e superleme
GRANT ALL ON SCHEMA schema_superleme TO postgres;
GRANT ALL ON SCHEMA schema_superleme TO zotonic;
GRANT ALL ON SCHEMA schema_superleme TO superleme;
GRANT USAGE ON SCHEMA schema_superleme TO postgres;
GRANT USAGE ON SCHEMA schema_superleme TO zotonic;
GRANT USAGE ON SCHEMA schema_superleme TO superleme;

-- Aplicar permissões em TODAS as tabelas, sequências e funções EXISTENTES
GRANT ALL ON ALL TABLES IN SCHEMA schema_superleme TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA schema_superleme TO zotonic;
GRANT ALL ON ALL TABLES IN SCHEMA schema_superleme TO superleme;
GRANT ALL ON ALL SEQUENCES IN SCHEMA schema_superleme TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA schema_superleme TO zotonic;
GRANT ALL ON ALL SEQUENCES IN SCHEMA schema_superleme TO superleme;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA schema_superleme TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA schema_superleme TO zotonic;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA schema_superleme TO superleme;

-- Configurar permissões default para objetos futuros no schema
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON TABLES TO zotonic;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON TABLES TO superleme;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON SEQUENCES TO zotonic;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON SEQUENCES TO superleme;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON FUNCTIONS TO zotonic;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON FUNCTIONS TO superleme;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON TYPES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON TYPES TO zotonic;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_superleme GRANT ALL ON TYPES TO superleme;

-- Verificar permissões (opcional)
\dp schema_superleme.*
