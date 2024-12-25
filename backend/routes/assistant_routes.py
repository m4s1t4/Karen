from flask import Blueprint, request, jsonify
from agents.assistant import Assistant
from db.supabase_utils import supabase

assistant_bp = Blueprint("assistant", __name__)
assistant = Assistant()

@assistant_bp.route("/chat/start", methods=["POST"])
def start_chat():
    """Inicia una nueva sesión de chat"""
    try:
        # Ya no creamos la sesión aquí, se creará cuando se envíe el primer mensaje
        return jsonify({"message": "Envía un mensaje para iniciar el chat"})
    except Exception as e:
        print(f"Error al iniciar sesión: {e}")
        return jsonify({"error": str(e)}), 500

@assistant_bp.route("/chat/message", methods=["POST"])
def send_message():
    """Envía un mensaje al asistente"""
    try:
        data = request.json
        message = data.get("message")
        session_id = data.get("session_id")

        if not message:
            return jsonify({"error": "Mensaje no proporcionado"}), 400

        # Procesar el mensaje
        result = assistant.process_message(message, session_id)
        return jsonify(result)
    except Exception as e:
        print(f"Error al procesar mensaje: {e}")
        return jsonify({"error": str(e)}), 500

@assistant_bp.route("/chat/history/<int:session_id>", methods=["GET"])
def get_chat_history(session_id):
    """Obtiene el historial de mensajes de un chat"""
    try:
        response = supabase.table("messages") \
            .select("role,content,created_at") \
            .eq("chat_session_id", session_id) \
            .order("created_at") \
            .execute()
        return jsonify(response.data)
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return jsonify({"error": str(e)}), 500

@assistant_bp.route("/chat/list", methods=["GET"])
def list_chats():
    """Lista todas las sesiones de chat"""
    try:
        response = supabase.table("chat_sessions") \
            .select("id,title,description,created_at") \
            .order("created_at", desc=True) \
            .execute()
        return jsonify(response.data)
    except Exception as e:
        print(f"Error al listar chats: {e}")
        return jsonify({"error": str(e)}), 500

@assistant_bp.route("/chat/delete/<int:session_id>", methods=["DELETE"])
def delete_chat(session_id):
    """Elimina un chat y sus mensajes"""
    try:
        # Los mensajes se eliminarán automáticamente por la restricción ON DELETE CASCADE
        supabase.table("chat_sessions") \
            .delete() \
            .eq("id", session_id) \
            .execute()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error al eliminar chat: {e}")
        return jsonify({"error": str(e)}), 500 