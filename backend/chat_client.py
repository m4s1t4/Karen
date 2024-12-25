import requests
import json
from datetime import datetime

class ChatClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session_id = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def start_session(self):
        """Inicia una nueva sesión de chat"""
        try:
            response = requests.post(
                f"{self.base_url}/api/assistant/chat/start",
                headers=self.headers,
                json={}  # Enviamos un objeto JSON vacío
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data["session_id"]
            print("✨ Nueva sesión iniciada!")
            return True
        except requests.exceptions.RequestException as e:
            print("❌ Error al iniciar sesión:")
            if hasattr(e.response, 'json'):
                error_data = e.response.json()
                print(f"Error: {error_data.get('error', 'Desconocido')}")
                if 'traceback' in error_data:
                    print("\nDetalles del error:")
                    print(error_data['traceback'])
            else:
                print(f"Error de conexión: {str(e)}")
            return False
    
    def send_message(self, message):
        """Envía un mensaje al asistente"""
        if not self.session_id:
            print("❌ Error: No hay una sesión activa")
            return None
        
        try:
            data = {
                "message": message,
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/assistant/chat/message",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            print("❌ Error al enviar mensaje:")
            if hasattr(e.response, 'json'):
                error_data = e.response.json()
                print(f"Error: {error_data.get('error', 'Desconocido')}")
                if 'traceback' in error_data:
                    print("\nDetalles del error:")
                    print(error_data['traceback'])
            else:
                print(f"Error de conexión: {str(e)}")
            return None
    
    def get_history(self):
        """Obtiene el historial de la conversación"""
        if not self.session_id:
            print("❌ Error: No hay una sesión activa")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/api/assistant/chat/history/{self.session_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["messages"]
        except requests.exceptions.RequestException as e:
            print("❌ Error al obtener historial:")
            if hasattr(e.response, 'json'):
                error_data = e.response.json()
                print(f"Error: {error_data.get('error', 'Desconocido')}")
                if 'traceback' in error_data:
                    print("\nDetalles del error:")
                    print(error_data['traceback'])
            else:
                print(f"Error de conexión: {str(e)}")
            return None

def main():
    print("🤖 Bienvenido al chat con Karen!")
    print("--------------------------------")
    
    client = ChatClient()
    if not client.start_session():
        return
    
    print("\n💡 Escribe 'salir' para terminar")
    print("💡 Escribe 'historial' para ver mensajes anteriores")
    print("--------------------------------\n")
    
    while True:
        try:
            message = input("\n👤 Tú: ")
            
            if message.lower() == 'salir':
                print("\n👋 ¡Hasta luego!")
                break
            
            if message.lower() == 'historial':
                history = client.get_history()
                if history:
                    print("\n📜 Historial de mensajes:")
                    for msg in history:
                        role = "👤 Tú:" if msg["role"] == "user" else "🤖 Karen:"
                        time = datetime.fromisoformat(msg["created_at"]).strftime("%H:%M:%S")
                        print(f"[{time}] {role} {msg['content']}")
                continue
            
            response = client.send_message(message)
            if response:
                print(f"\n🤖 Karen: {response}")
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {str(e)}")
            break

if __name__ == "__main__":
    main() 