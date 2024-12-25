from flask import Blueprint, request, jsonify
from db.supabase_utils import supabase_manager
from agents.assistant import assistant

assistant_bp = Blueprint('assistant', __name__)

@assistant_bp.route('/chat/start', methods=['POST'])
def start_chat():
    """Inicia una nueva sesión de chat"""
    try:
        # Crear una nueva sesión en la base de datos
        session_id = supabase_manager.create_chat_session()
        return jsonify({"session_id": session_id})
    except Exception as e:
        print(f"❌ Error al iniciar sesión: {str(e)}")
        return jsonify({"error": str(e), "traceback": str(e.__traceback__)}), 500

@assistant_bp.route('/chat/message', methods=['POST'])
def send_message():
    """Procesa un mensaje del usuario y obtiene una respuesta"""
    try:
        data = request.json
        if not data or 'message' not in data or 'session_id' not in data:
            return jsonify({"error": "Se requiere mensaje y session_id"}), 400

        message = data['message']
        session_id = data['session_id']

        # Procesar el mensaje y obtener respuesta
        response = assistant.process_message(message, session_id)
        return jsonify({"response": response})
    except Exception as e:
        print(f"❌ Error al procesar mensaje: {str(e)}")
        return jsonify({"error": str(e)}), 500

@assistant_bp.route('/chat/history/<int:session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Obtiene el historial de mensajes de una sesión"""
    try:
        messages = supabase_manager.get_chat_history(session_id)
        return jsonify(messages)
    except Exception as e:
        print(f"❌ Error al obtener historial: {str(e)}")
        return jsonify({"error": str(e)}), 500

@assistant_bp.route('/chat/list', methods=['GET'])
def list_chats():
    """Obtiene la lista de sesiones de chat"""
    try:
        chats = supabase_manager.list_chat_sessions()
        return jsonify(chats)
    except Exception as e:
        print(f"❌ Error al listar chats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@assistant_bp.route('/chat/delete/<int:session_id>', methods=['DELETE'])
def delete_chat(session_id):
    """Elimina una sesión de chat"""
    try:
        supabase_manager.delete_chat_session(session_id)
        return jsonify({"message": "Chat eliminado correctamente"})
    except Exception as e:
        print(f"❌ Error al eliminar chat: {str(e)}")
        return jsonify({"error": str(e)}), 500 