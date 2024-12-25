from flask import Blueprint, request, jsonify
from agents.assistant import assistant
from db.supabase_utils import supabase_manager
import traceback

assistant_bp = Blueprint('assistant', __name__)

@assistant_bp.route('/chat/start', methods=['POST'])
def start_chat():
    """Inicia una nueva sesión de chat"""
    try:
        user_id = request.json.get('user_id') if request.json else None
        chat_session = supabase_manager.create_chat_session(user_id)
        return jsonify({
            "session_id": chat_session['id'],
            "message": "Sesión de chat iniciada"
        })
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print("Error al iniciar sesión:", error_details)
        return jsonify(error_details), 500

@assistant_bp.route('/chat/message', methods=['POST'])
def send_message():
    """Envía un mensaje al asistente"""
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Se requiere un mensaje"}), 400
    
    chat_session_id = data.get('session_id')
    user_message = data['message']
    
    try:
        response = assistant.process_message(user_message, chat_session_id)
        return jsonify({
            "response": response,
            "session_id": chat_session_id
        })
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print("Error al procesar mensaje:", error_details)
        return jsonify(error_details), 500

@assistant_bp.route('/chat/history/<int:session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Obtiene el historial de mensajes de una sesión"""
    try:
        messages = supabase_manager.get_chat_history(session_id)
        return jsonify({
            "session_id": session_id,
            "messages": [{
                "role": msg['role'],
                "content": msg['content'],
                "created_at": msg['created_at']
            } for msg in messages]
        })
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print("Error al obtener historial:", error_details)
        return jsonify(error_details), 500 