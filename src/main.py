import os
import sys
import logging
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.database import db

# Configurar logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Database configuration
# Use remote database server or fallback to local
REMOTE_DB_URL = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}")
app.config['SQLALCHEMY_DATABASE_URI'] = REMOTE_DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the shared db instance with the app
db.init_app(app)

# Import routes AFTER db initialization
from src.routes.user import user_bp
from src.routes.sync import sync_bp

# Import models to ensure they are registered
from src.models.user import User
from src.models.kommo_account import KommoAccount, PipelineMapping, StageMapping, CustomFieldMapping, SyncLog

# Habilitar CORS para todas as rotas
CORS(app)

# Register Blueprints
from src.routes.sync import sync_bp
from src.routes.user import user_bp
from src.routes.groups import group_bp

app.register_blueprint(sync_bp, url_prefix='/api/sync')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(group_bp, url_prefix='/api/groups')

# Criar diretório do banco se não existir
os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)

with app.app_context():
    db.create_all()
    
    # Inicializar status global da sincronização
    from src.routes.sync import update_global_status
    update_global_status(
        status='idle',
        progress=0,
        operation='Sistema inicializado',
        is_running=False
    )

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask na porta 5000...")
    print("📡 API disponível em: http://localhost:5000/api/sync")
    app.run(host='0.0.0.0', port=5000, debug=True)