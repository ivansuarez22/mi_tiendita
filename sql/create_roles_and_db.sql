-- Cambia las contraseñas por contraseñas seguras en producción.
CREATE ROLE tiendita_admin WITH LOGIN PASSWORD 'AdminPass123' SUPERUSER;
CREATE ROLE tiendita_empleado WITH LOGIN PASSWORD 'EmpleadoPass123' NOINHERIT;
CREATE ROLE tiendita_app WITH LOGIN PASSWORD 'AppPass123' NOINHERIT;

CREATE DATABASE tiendita_db OWNER tiendita_admin;
