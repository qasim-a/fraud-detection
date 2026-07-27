-- Local-only database capabilities and least-privilege group roles.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fraud_migrator') THEN
    CREATE ROLE fraud_migrator NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fraud_runtime') THEN
    CREATE ROLE fraud_runtime NOLOGIN;
  END IF;
END
$$;

GRANT CONNECT ON DATABASE fraud_detection TO fraud_migrator, fraud_runtime;
GRANT USAGE ON SCHEMA public TO fraud_migrator, fraud_runtime;
GRANT CREATE ON SCHEMA public TO fraud_migrator;

ALTER DEFAULT PRIVILEGES FOR ROLE fraud_app IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fraud_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE fraud_app IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO fraud_runtime;
