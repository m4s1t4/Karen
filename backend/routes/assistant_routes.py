from flask import Blueprint, request, jsonify
from agents.assistant import Assistant
from db.supabase_utils import supabase
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import logging
from rag.optimized_rag import OptimizedRAG

logger = logging.getLogger(__name__)

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

@assistant_bp.route("/upload", methods=["POST"])
async def upload_file():
    """Maneja la subida de archivos PDF y los procesa con RAG"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No se envió ningún archivo"}), 400
            
        file = request.files["file"]
        chat_id = request.form.get("chat_id")
        
        if file.filename == "":
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
            
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Solo se permiten archivos PDF"}), 400
        
        # Si no hay chat_id, crear una nueva sesión
        if not chat_id:
            response = supabase.table("chat_sessions").insert({
                "title": f"Chat con {file.filename}",
                "description": "Chat iniciado con documento"
            }).execute()
            chat_id = response.data[0]["id"]
        else:
            chat_id = int(chat_id)
        
        # Crear directorio temporal si no existe
        temp_dir = Path(__file__).parent.parent / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo temporalmente
        temp_file = temp_dir / secure_filename(file.filename)
        file.save(str(temp_file))
        
        try:
            # Procesar archivo con RAG
            rag = OptimizedRAG()
            
            # Procesar el archivo directamente sin subirlo a Storage
            logger.info(f"Procesando archivo {file.filename} para el chat {chat_id}")
            documents = rag.load_documents(str(temp_file))
            chunks = rag.split_documents(documents)
            
            # Almacenar chunks en la base de datos
            rag.store_in_supabase(chunks, chat_id)
            
            return jsonify({
                "message": "Archivo procesado exitosamente",
                "chat_id": chat_id
            }), 200
            
        finally:
            # Limpiar archivo temporal
            if temp_file.exists():
                temp_file.unlink()
        
    except Exception as e:
        logger.error(f"Error en upload_file: {e}")
        return jsonify({"error": str(e)}), 500 