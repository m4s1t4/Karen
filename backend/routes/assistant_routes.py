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
        # Crear una nueva sesión de chat
        response = (
            supabase.table("chat_sessions")
            .insert(
                {"title": "Nueva conversación", "description": "Conversación iniciada"}
            )
            .execute()
        )

        if not response.data:
            raise Exception("Error al crear la sesión de chat")

        session_id = response.data[0]["id"]
        return jsonify({"message": "Sesión de chat creada", "session_id": session_id})
    except Exception as e:
        logger.error(f"Error al iniciar sesión: {e}")
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
        response = (
            supabase.table("messages")
            .select("role,content,created_at")
            .eq("chat_session_id", session_id)
            .order("created_at")
            .execute()
        )
        return jsonify(response.data)
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return jsonify({"error": str(e)}), 500


@assistant_bp.route("/chat/list", methods=["GET"])
def list_chats():
    """Lista todas las sesiones de chat"""
    try:
        response = (
            supabase.table("chat_sessions")
            .select("id,title,description,created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return jsonify(response.data)
    except Exception as e:
        print(f"Error al listar chats: {e}")
        return jsonify({"error": str(e)}), 500


@assistant_bp.route("/chat/delete/<int:session_id>", methods=["DELETE"])
def delete_chat(session_id):
    """Elimina un chat y sus mensajes"""
    try:
        # Los mensajes se eliminarán automáticamente por la restricción ON DELETE CASCADE
        supabase.table("chat_sessions").delete().eq("id", session_id).execute()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error al eliminar chat: {e}")
        return jsonify({"error": str(e)}), 500


@assistant_bp.route("/upload", methods=["POST"])
async def upload_file():
    try:
        # Obtener el archivo y chat_id
        file = request.files.get("file")
        chat_id = request.form.get("chat_id")

        if not file or not chat_id:
            return jsonify({"error": "Se requiere archivo y chat_id"}), 400

        # Crear directorio temporal si no existe
        temp_dir = Path("backend/temp")
        temp_dir.mkdir(exist_ok=True)

        # Guardar archivo temporalmente
        file_path = temp_dir / file.filename
        file.save(str(file_path))

        try:
            # Procesar archivo con RAG
            rag = OptimizedRAG()
            file_info = await rag.process_file(str(file_path), int(chat_id))

            # Usar el chat_id actualizado del file_info
            updated_chat_id = file_info.get("chat_id", int(chat_id))

            # Procesar el archivo con el asistente
            assistant = Assistant()
            welcome_message = await assistant.process_uploaded_files(
                file_info, updated_chat_id
            )

            # Eliminar archivo temporal
            file_path.unlink()

            return jsonify(
                {
                    "message": "Archivo procesado exitosamente",
                    "welcome_message": welcome_message,
                    "file_info": {
                        "file_name": file_info["file_name"],
                        "file_url": file_info["file_url"],
                        "num_chunks": file_info["num_chunks"],
                        "chat_id": updated_chat_id,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error en upload_file: {e}")
            # Asegurarse de eliminar el archivo temporal en caso de error
            if file_path.exists():
                file_path.unlink()
            raise

    except Exception as e:
        logger.error(f"Error en upload_file: {e}")
        return jsonify({"error": str(e)}), 500
