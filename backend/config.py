import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Configuración básica
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Configuración de Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Configuración de OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Configuración del servidor
    HOST = os.getenv('HOST', 'localhost')
    PORT = int(os.getenv('PORT', 5000))

    def __init__(self):
        # Verificar variables requeridas
        required_vars = [
            'SECRET_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(self, var)]
        
        if missing_vars:
            raise ValueError(
                f"Faltan las siguientes variables de entorno requeridas: {', '.join(missing_vars)}"
            )

# Crear una instancia global de la configuración
config = Config()
