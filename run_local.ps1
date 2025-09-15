# PowerShell helper to run locally (Windows)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = 'postgresql://tiendita_app:AppPass123@localhost:5432/tiendita_db'
$env:SECRET_KEY = 'dev-secret'
python app.py
