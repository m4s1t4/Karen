from supabase import create_client, Client
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import Config
from datetime import datetime

class SupabaseManager:
    def __init__(self):
        self.supabase: Client = None
        self.config = Config()
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa el cliente de Supabase con las credenciales"""
        try:
            if not self.config.SUPABASE_URL or not self.config.SUPABASE_KEY:
                raise ValueError("SUPABASE_URL y SUPABASE_KEY son requeridos")
            
            self.supabase = create_client(
                self.config.SUPABASE_URL,
                self.config.SUPABASE_KEY
            )
            print("✅ Conexión a Supabase establecida")
        except Exception as e:
            print(f"❌ Error al inicializar Supabase: {str(e)}")
            raise

    def create_chat_session(self, user_id=None):
        """Crea una nueva sesión de chat"""
        try:
            data = {
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('chat_sessions').insert(data).execute()
            
            if not result.data:
                raise Exception("No se pudo crear la sesión de chat")
            
            return result.data[0]
        except Exception as e:
            print(f"❌ Error al crear sesión de chat: {str(e)}")
            raise

    def store_message(self, session_id, role, content, user_id=None):
        """Almacena un mensaje en la base de datos"""
        try:
            data = {
                'chat_session_id': session_id,
                'user_id': user_id,
                'role': role,
                'content': content,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('messages').insert(data).execute()
            
            if not result.data:
                raise Exception("No se pudo almacenar el mensaje")
            
            return result.data[0]
        except Exception as e:
            print(f"❌ Error al almacenar mensaje: {str(e)}")
            raise

    def get_chat_history(self, session_id):
        """Obtiene el historial de mensajes de una sesión"""
        try:
            result = self.supabase.table('messages')\
                .select('*')\
                .eq('chat_session_id', session_id)\
                .order('created_at')\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"❌ Error al obtener historial: {str(e)}")
            raise

# Instancia global del manejador de Supabase
supabase_manager = SupabaseManager() 