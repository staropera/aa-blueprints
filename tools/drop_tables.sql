-- Deletes all blueprint related tables from the database
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS blueprints_blueprint;
DROP TABLE IF EXISTS blueprints_location;
DROP TABLE IF EXISTS blueprints_owner;
DROP TABLE IF EXISTS blueprints_request;
SET FOREIGN_KEY_CHECKS=1;
