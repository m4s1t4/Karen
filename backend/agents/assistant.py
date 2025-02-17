from openai import OpenAI
from config import Config
from db.supabase_utils import supabase
from .chat_summarizer import ChatSummarizer
from agents.prompts.main_prompt import orchestrator
from typing import List, Dict
import tenacity
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores.supabase import SupabaseVectorStore

logger = logging.getLogger(__name__)


def initialize_vector_store():
    """Inicializa el vector store de Supabase con la configuración correcta."""
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", chunk_size=100)
    vector_store = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents",
        query_name="match_documents",
    )
    return vector_store


@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    stop=tenacity.stop_after_attempt(5),
    retry=tenacity.retry_if_exception_type(Exception),
)
def search_similar_for_chat(query: str, chat_id: int, top_k: int = 5) -> List[Dict]:
    """Búsqueda semántica optimizada para un chat específico usando SupabaseVectorStore."""
    try:
        logger.info(f"Iniciando búsqueda semántica para chat {chat_id}")
        vector_store = initialize_vector_store()

        # Realizar búsqueda usando el vector store con el filtro correcto
        # El chat_id está en el campo chat_id de la tabla documents, no en metadata
        relevant_docs = vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter={"chat_id": chat_id},  # Filtro corregido
        )

        if not relevant_docs:
            logger.info("No se encontraron documentos relevantes")
            return []

        # Formatear resultados
        results = []
        for doc, score in relevant_docs:
            if score > 0.7:  # Solo incluir documentos con alta relevancia
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": float(score),
                }
                results.append(result)
                logger.info(
                    f"Documento encontrado con score {score}: {doc.page_content[:100]}..."
                )

        logger.info(f"Se encontraron {len(results)} documentos relevantes")
        return results

    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {str(e)}")
        raise


def chat_has_documents(chat_id: int) -> bool:
    """Verifica si un chat tiene documentos asociados."""
    try:
        logger.info(f"Verificando documentos para chat {chat_id}")
        result = (
            supabase.table("documents")
            .select("id, content")
            .eq("chat_id", chat_id)
            .execute()
        )
        has_docs = len(result.data) > 0
        logger.info(
            f"Chat {chat_id} {'tiene' if has_docs else 'no tiene'} documentos asociados"
        )
        return has_docs
    except Exception as e:
        logger.error(f"Error verificando documentos del chat: {e}")
        return False


class Assistant:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.current_chat_id = None
        self.rules = orchestrator

    async def process_uploaded_files(self, file_info: Dict, chat_id: int):
        """Procesa la información de archivos subidos y genera un resumen inicial."""
        try:
            # Crear un resumen del contenido del archivo
            chunks_content = "\n".join(
                [chunk["content"] for chunk in file_info["chunks"]]
            )

            prompt = PromptTemplate(
                template="""Se ha subido un nuevo archivo a la conversación. Por favor, genera un resumen conciso del contenido
                y menciona los puntos principales que se pueden encontrar en él.

                Archivo: {file_name}
                Contenido:
                {content}

                Resumen:""",
                input_variables=["file_name", "content"],
            )

            chain = (
                {
                    "file_name": lambda x: file_info["file_name"],
                    "content": lambda x: chunks_content,
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )

            summary = chain.invoke({})

            # Crear mensaje de bienvenida con el resumen
            welcome_message = f"""He procesado el archivo "{file_info["file_name"]}" y lo he dividido en {file_info["num_chunks"]} segmentos para su análisis.

{summary}

Ahora puedes hacerme preguntas sobre el contenido del archivo y te ayudaré a encontrar la información relevante."""

            # Guardar el mensaje del asistente
            supabase.table("messages").insert(
                {
                    "chat_session_id": chat_id,
                    "role": "assistant",
                    "content": welcome_message,
                    "metadata": {
                        "file_info": {
                            "file_name": file_info["file_name"],
                            "file_url": file_info["file_url"],
                            "num_chunks": file_info["num_chunks"],
                        }
                    },
                }
            ).execute()

            return welcome_message

        except Exception as e:
            logger.error(f"Error procesando archivos subidos: {e}")
            raise

    def process_message(self, message: str, chat_id: int = None) -> Dict:
        """Procesa un mensaje y retorna la respuesta"""

        try:
            # Si no hay chat_id, crear nueva sesión
            if not chat_id:
                response = (
                    supabase.table("chat_sessions")
                    .insert(
                        {
                            "title": "Nueva conversación",
                            "description": "Conversación iniciada",
                        }
                    )
                    .execute()
                )
                chat_id = response.data[0]["id"]

            self.current_chat_id = chat_id

            # Solo buscar documentos relevantes si el chat tiene documentos asociados
            context = ""
            references = []
            used_sources = set()

            if chat_has_documents(chat_id):
                relevant_docs = search_similar_for_chat(message, chat_id)
                if relevant_docs:
                    # Crear el contexto y las referencias
                    context_parts = []
                    for i, doc in enumerate(relevant_docs, 1):
                        # Agregar número de chunk al contenido para referencia
                        source_info = ""
                        if doc["metadata"].get("source"):
                            from pathlib import Path

                            filename = Path(doc["metadata"]["source"]).name
                            source_info = f" [Fuente: {filename}]"
                        if doc["metadata"].get("page"):
                            source_info += f" [Página: {doc['metadata']['page']}]"

                        chunk_content = f"[Chunk {i}] (Relevancia: {doc['similarity']:.2f}){source_info}\n{doc['content']}\n"
                        context_parts.append(chunk_content)

                        # Crear referencia con metadata
                        ref = {
                            "chunk": i,
                            "content": doc["content"],
                            "metadata": doc["metadata"],
                            "similarity": doc["similarity"],
                        }
                        references.append(ref)

                        # Trackear fuente única
                        if doc["metadata"].get("source"):
                            filename = Path(doc["metadata"]["source"]).name
                            used_sources.add(filename)

                    context = "\n".join(context_parts)

            # Guardar mensaje del usuario
            supabase.table("messages").insert(
                {
                    "chat_session_id": chat_id,
                    "role": "user",
                    "content": message,
                    "metadata": None,
                }
            ).execute()

            # Generar respuesta
            prompt = PromptTemplate(
                template="""Utiliza el siguiente contexto para responder la pregunta si está disponible.
                Si no hay contexto o la información no está en el contexto, responde basándote en tu conocimiento general.

                IMPORTANTE:
                1. Si utilizas información del contexto, debes citar la fuente usando [X] donde X es el número del chunk del que obtuviste la información.
                2. Debes citar TODOS los chunks que uses en tu respuesta.
                3. Las citas deben ir inmediatamente después de cada afirmación que hagas usando información de los chunks.
                4. Estructura tu respuesta en párrafos claros y concisos.
                5. Usa saltos de línea entre párrafos para mejorar la legibilidad.

                Además sigue estas reglas: {rules}

                {context}
                Pregunta: {question}

                Respuesta:""",
                input_variables=["context", "question", "rules"],
            )

            chain = (
                {
                    "context": lambda x: f"Contexto: {context}"
                    if context
                    else "No hay documentos asociados a esta conversación.",
                    "question": RunnablePassthrough(),
                    "rules": lambda x: self.rules,
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )

            response = chain.invoke(message)

            # Preparar metadata con referencias si existen
            message_metadata = {"references": references} if references else None

            # Guardar respuesta del asistente
            supabase.table("messages").insert(
                {
                    "chat_session_id": chat_id,
                    "role": "assistant",
                    "content": response,
                    "metadata": message_metadata,
                }
            ).execute()

            # Si hay referencias, agregarlas al final de la respuesta para mostrar
            if references:
                response_with_refs = response + "\n\n---\nFuentes consultadas:\n"

                # Primero mostrar las fuentes únicas utilizadas
                if used_sources:
                    response_with_refs += "\n📚 Documentos:\n"
                    for source in used_sources:
                        response_with_refs += f"• {source}\n"

                # Luego mostrar los chunks específicos que fueron citados en la respuesta
                response_with_refs += "\n📖 Referencias específicas:\n"

                # Obtener los chunks citados en la respuesta
                import re

                cited_chunks = set(re.findall(r"\[(\d+)\]", response))

                for chunk_num in cited_chunks:
                    chunk_idx = int(chunk_num) - 1
                    if chunk_idx < len(references):
                        ref = references[chunk_idx]
                        source_info = f"\n[{ref['chunk']}]"
                        if ref["metadata"].get("page"):
                            source_info += f" (Página {ref['metadata']['page']})"
                        source_info += f":\n{ref['content']}\n"
                        response_with_refs += source_info
            else:
                response_with_refs = response

            return {
                "message": response_with_refs,
                "chat_id": chat_id,
                "metadata": message_metadata,
            }

        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            raise
