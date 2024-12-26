from openai import OpenAI
from config import Config
from db.supabase_utils import supabase
from .chat_summarizer import ChatSummarizer
from agents.prompts.main_prompt import orchestrator

class Assistant:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.summarizer = ChatSummarizer()

    def process_message(self, message: str, session_id: int) -> str:
        """Procesa un mensaje del usuario y retorna la respuesta del asistente."""
        try:
            messages = []
            
            # Obtener el historial de mensajes si existe un session_id
            is_new_chat = session_id is None
            
            if not is_new_chat:
                messages = self._get_chat_history(session_id)
            
            # Agregar el prompt del sistema y el mensaje del usuario
            messages = [{"role": "system", "content": orchestrator}] + messages
            messages.append({"role": "user", "content": message})
            
            # Obtener respuesta de OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                temperature=0
            )
            
            assistant_message = response.choices[0].message.content

            # Si es un chat nuevo, crearlo ahora que tenemos la respuesta
            if is_new_chat:
                # Crear el chat con el título y descripción basados en la primera interacción
                all_messages = messages + [{"role": "assistant", "content": assistant_message}]
                title = self.summarizer.generate_title(all_messages)
                description = self.summarizer.generate_description(all_messages)
                
                # Crear el chat
                response = supabase.table("chat_sessions").insert({
                    "title": title,
                    "description": description
                }).execute()
                session_id = response.data[0]["id"]
            
            # Guardar los mensajes
            self._store_message(session_id, "user", message)
            self._store_message(session_id, "assistant", assistant_message)
            
            # Devolver la respuesta y el ID de sesión si es nuevo
            if is_new_chat:
                return {
                    "response": assistant_message,
                    "session_id": session_id
                }
            return {
                "response": assistant_message
            }
            
        except Exception as e:
            print(f"Error al procesar mensaje: {e}")
            raise

    def _get_chat_history(self, session_id: int) -> list:
        """Obtiene el historial de mensajes de un chat."""
        try:
            response = supabase.table("messages") \
                .select("role, content") \
                .eq("chat_session_id", session_id) \
                .order("created_at") \
                .execute()
            return response.data
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []

    def _store_message(self, session_id: int, role: str, content: str):
        """Almacena un mensaje en la base de datos."""
        try:
            supabase.table("messages").insert({
                "chat_session_id": session_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"Error al almacenar mensaje: {e}")
            raise 