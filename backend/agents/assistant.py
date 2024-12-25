from db.supabase_utils import supabase_manager
from openai import OpenAI
from config import config

class Assistant:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4o"
        
    def _get_context(self, session_id):
        """Obtiene el contexto de la conversación"""
        try:
            messages = supabase_manager.get_chat_history(session_id)
            return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        except Exception:
            return []
    
    def _store_message(self, session_id, role, content):
        """Almacena un mensaje en la base de datos"""
        return supabase_manager.store_message(session_id, role, content)
    
    def process_message(self, message, session_id):
        """Procesa un mensaje del usuario y obtiene una respuesta"""
        try:
            # Obtener historial de mensajes
            conversation = self._get_context(session_id)
            # Prompt del agente
            conversation.append({"role": "system", "content": "You are a helpfull asistant"})
            
            # Almacenar mensaje del usuario
            self._store_message(session_id, "user", message)
            
            # Agregar el nuevo mensaje a la conversación
            conversation.append({"role": "user", "content": message})
            
            # Obtener respuesta de OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation
            )
            
            # Extraer la respuesta
            assistant_message = response.choices[0].message.content
            
            # Almacenar respuesta del asistente
            self._store_message(session_id, "assistant", assistant_message)
            
            return assistant_message
            
        except Exception as e:
            print(f"❌ Error al procesar mensaje: {str(e)}")
            raise

# Instancia global del asistente
assistant = Assistant() 