from supabase import create_client
from config import Config

# Crear cliente de Supabase
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def create_chat_session():
    """Crea una nueva sesión de chat"""
    try:
        response = supabase.table("chat_sessions").insert({}).execute()
        return response.data[0]["id"]
    except Exception as e:
        print(f"Error al crear sesión: {e}")
        raise

def store_message(session_id, role, content):
    """Almacena un mensaje en la base de datos"""
    try:
        response = supabase.table("messages").insert({
            "chat_session_id": session_id,
            "role": role,
            "content": content
        }).execute()
        return response.data[0]
    except Exception as e:
        print(f"Error al almacenar mensaje: {e}")
        raise

def get_chat_history(session_id):
    """Obtiene el historial de mensajes de un chat"""
    try:
        response = supabase.table("messages") \
            .select("*") \
            .eq("chat_session_id", session_id) \
            .order("created_at") \
            .execute()
        return response.data
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return []

def delete_chat(session_id):
    """Elimina un chat y todos sus mensajes"""
    try:
        response = supabase.table("chat_sessions") \
            .delete() \
            .eq("id", session_id) \
            .execute()
        return True
    except Exception as e:
        print(f"Error al eliminar chat: {e}")
        raise 