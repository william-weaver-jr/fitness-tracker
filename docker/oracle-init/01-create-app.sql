-- Oracle Free 23ai initialisation script.
-- This file is executed automatically by gvenzl/oracle-free on first start
-- when placed in /container-entrypoint-initdb.d/.
--
-- The APP_USER and APP_USER_PASSWORD env vars already create the user and
-- grant CONNECT + RESOURCE. This script adds the additional grants needed
-- for JSON Duality Views and the application schema.

-- Run as the automatically-created app user (already connected via APP_USER env)
ALTER SESSION SET CURRENT_SCHEMA = FITTRACK_APP;

-- Allow unlimited tablespace usage in dev (not for production)
GRANT UNLIMITED TABLESPACE TO fittrack_app;

-- Grants needed for JSON Duality Views
GRANT CREATE VIEW TO fittrack_app;
GRANT CREATE TABLE TO fittrack_app;
GRANT CREATE SEQUENCE TO fittrack_app;
GRANT CREATE PROCEDURE TO fittrack_app;
GRANT CREATE TRIGGER TO fittrack_app;
GRANT CREATE TYPE TO fittrack_app;
GRANT CREATE INDEX TO fittrack_app;
GRANT EXECUTE ON DBMS_CRYPTO TO fittrack_app;
