


#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE test_db OWNER postgres;
    GRANT ALL PRIVILEGES ON DATABASE test_db TO postgres;
    GRANT ALL ON SCHEMA public TO postgres;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;
    ALTER SCHEMA public OWNER TO postgres;
EOSQL
