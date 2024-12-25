from supabase import create_client, Client
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import Config
from datetime import datetime

class SupabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    def create_chat_session(self):
        """Crea una nueva sesión de chat"""
        try:
            result = self.supabase.table('chat_sessions').insert({
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return result.data[0]['id']
        except Exception as e:
            print(f"❌ Error al crear sesión en Supabase: {str(e)}")
            raise e

    def store_message(self, session_id: int, role: str, content: str):
        """Almacena un mensaje en la base de datos"""
        try:
            self.supabase.table('messages').insert({
                'session_id': session_id,
                'role': role,
                'content': content,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"❌ Error al almacenar mensaje en Supabase: {str(e)}")
            raise e

    def get_chat_history(self, session_id: int):
        """Obtiene el historial de mensajes de una sesión"""
        try:
            result = self.supabase.table('messages')\
                .select('role,content,created_at')\
                .eq('session_id', session_id)\
                .order('created_at')\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"❌ Error al obtener historial de Supabase: {str(e)}")
            raise e

    def list_chat_sessions(self):
        """Obtiene la lista de sesiones de chat"""
        try:
            result = self.supabase.table('chat_sessions')\
                .select('id,created_at')\
                .order('created_at', desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"❌ Error al listar sesiones de Supabase: {str(e)}")
            raise e

    def delete_chat_session(self, session_id: int):
        """Elimina una sesión de chat y sus mensajes"""
        try:
            # Primero eliminamos los mensajes asociados
            self.supabase.table('messages')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()
            
            # Luego eliminamos la sesión
            self.supabase.table('chat_sessions')\
                .delete()\
                .eq('id', session_id)\
                .execute()
        except Exception as e:
            print(f"❌ Error al eliminar sesión de Supabase: {str(e)}")
            raise e

# Instancia global del manejador de Supabase
supabase_manager = SupabaseManager() 