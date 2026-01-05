-- Script para corrigir permissões do PostgreSQL no schema schema_superleme
-- Execute este script no banco de dados superleme para corrigir permissões

-- Criar roles se não existirem
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'zotonic') THEN
        CREATE ROLE zotonic LOGIN PASSWORD 'abensoft';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'superleme') THEN
        CREATE ROLE superleme LOGIN PASSWORD 'abensoft';
    END IF;
END
$$;

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

-- Configurar permissões default para objetos futuros criados POR QUALQUER ROLE no schema
-- Isso garante que INDEPENDENTE de quem criar (postgres, zotonic, superleme), todos terão permissão
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA schema_superleme GRANT ALL ON TABLES TO zotonic, superleme;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA schema_superleme GRANT ALL ON SEQUENCES TO zotonic, superleme;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA schema_superleme GRANT ALL ON FUNCTIONS TO zotonic, superleme;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA schema_superleme GRANT ALL ON TYPES TO zotonic, superleme;

ALTER DEFAULT PRIVILEGES FOR ROLE zotonic IN SCHEMA schema_superleme GRANT ALL ON TABLES TO postgres, superleme;
ALTER DEFAULT PRIVILEGES FOR ROLE zotonic IN SCHEMA schema_superleme GRANT ALL ON SEQUENCES TO postgres, superleme;
ALTER DEFAULT PRIVILEGES FOR ROLE zotonic IN SCHEMA schema_superleme GRANT ALL ON FUNCTIONS TO postgres, superleme;
ALTER DEFAULT PRIVILEGES FOR ROLE zotonic IN SCHEMA schema_superleme GRANT ALL ON TYPES TO postgres, superleme;

ALTER DEFAULT PRIVILEGES FOR ROLE superleme IN SCHEMA schema_superleme GRANT ALL ON TABLES TO postgres, zotonic;
ALTER DEFAULT PRIVILEGES FOR ROLE superleme IN SCHEMA schema_superleme GRANT ALL ON SEQUENCES TO postgres, zotonic;
ALTER DEFAULT PRIVILEGES FOR ROLE superleme IN SCHEMA schema_superleme GRANT ALL ON FUNCTIONS TO postgres, zotonic;
ALTER DEFAULT PRIVILEGES FOR ROLE superleme IN SCHEMA schema_superleme GRANT ALL ON TYPES TO postgres, zotonic;

-- Verificar permissões (opcional)
\dp schema_superleme.*
