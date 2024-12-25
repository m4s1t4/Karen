from flask import Flask, jsonify
from flask_cors import CORS
from routes.assistant_routes import assistant_bp
from config import config

def create_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # Habilitar CORS
    CORS(app)
    
    # Registrar rutas
    app.register_blueprint(assistant_bp, url_prefix='/api/assistant')
    
    # Ruta de prueba
    @app.route('/')
    def index():
        return jsonify({
            "status": "success",
            "message": "API de Karen funcionando correctamente"
        })
    
    # Ruta de estado
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "version": "1.0.0"
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
