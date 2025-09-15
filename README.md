# Tiendita - Proyecto de Inventario (Flask + PostgreSQL)

## Contenido
Proyecto listo para ejecutar. Incluye:
- `sql/create_roles_and_db.sql` : crea roles y base de datos (ejecutar como postgres)
- `sql/schema_tiendita.sql` : esquema (tablas, procedure, function, trigger, grants)
- `app.py` : aplicación Flask principal
- `config.py` : configuración (lee DATABASE_URL y SECRET_KEY)
- `requirements.txt` : dependencias Python
- `templates/` : vistas HTML (Bootstrap)
- `static/css/styles.css`
- `run_local.ps1` : script PowerShell de ejemplo para levantar localmente

## Instrucciones rápidas (Windows)
1. Asegúrate de tener PostgreSQL instalado y `psql` accesible.
2. Ejecuta como usuario `postgres` el SQL para crear roles/DB:
   ```
   psql -U postgres -f sql/create_roles_and_db.sql
   ```
3. Luego, conecta a la DB y ejecuta el esquema:
   ```
   psql -U tiendita_admin -d tiendita_db -f sql/schema_tiendita.sql
   ```
4. En el sistema, entra a esta carpeta y crea entorno virtual:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
5. Ajusta variables de entorno (ejemplo PowerShell):
   ```powershell
   $env:DATABASE_URL = 'postgresql://tiendita_app:AppPass123@localhost:5432/tiendita_db'
   $env:SECRET_KEY = 'cambia-esto'
   python app.py
   ```
6. Abre: http://127.0.0.1:5000

## Notas
- Las contraseñas en `create_roles_and_db.sql` son de ejemplo. Cámbialas en producción.
- Si tienes problemas de permisos, revisa GRANTs en `sql/schema_tiendita.sql`.
