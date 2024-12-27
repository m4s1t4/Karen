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
logger = logging.getLogger(__name__)

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    stop=tenacity.stop_after_attempt(5),
    retry=tenacity.retry_if_exception_type(Exception)
)
def search_similar_for_chat(query: str, chat_id: int, top_k: int = 5) -> List[Dict]:
    """Búsqueda semántica optimizada para un chat específico."""
    try:
        # Obtener embedding de la query
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            chunk_size=100
        )
        query_embedding = embeddings.embed_query(query)
        
        # Verificar dimensiones
        if len(query_embedding) != 1536:
            raise ValueError(f"Embedding debe tener 1536 dimensiones, tiene {len(query_embedding)}")
        
        # Realizar búsqueda directa usando SQL con similitud coseno
        result = supabase.table("documents") \
            .select("content, metadata, embedding") \
            .eq("chat_id", chat_id) \
            .execute()
            
        if not result.data:
            return []
            
        # Calcular similitud coseno localmente
        documents_with_scores = []
        for doc in result.data:
            if "embedding" in doc and doc["embedding"]:
                try:
                    # Convertir el embedding de string a lista de floats
                    # Primero remover corchetes y espacios
                    embedding_str = doc["embedding"].strip('[]').replace(' ', '')
                    # Dividir por comas y convertir a float
                    doc_embedding = [float(x) for x in embedding_str.split(',') if x]
                    
                    if len(doc_embedding) != 1536:
                        logger.warning(f"Embedding inválido: longitud {len(doc_embedding)}")
                        continue
                    
                    # Calcular similitud coseno usando numpy para mayor eficiencia
                    import numpy as np
                    query_array = np.array(query_embedding)
                    doc_array = np.array(doc_embedding)
                    
                    similarity = np.dot(query_array, doc_array) / \
                        (np.linalg.norm(query_array) * np.linalg.norm(doc_array))
                    
                    if similarity > 0.7:  # Umbral de similitud
                        documents_with_scores.append({
                            "content": doc["content"],
                            "metadata": doc["metadata"],
                            "similarity": float(similarity)  # Convertir a float para serialización
                        })
                except Exception as e:
                    logger.warning(f"Error calculando similitud para documento: {e}")
                    continue
        
        # Ordenar por similitud y tomar los top_k
        documents_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
        return documents_with_scores[:top_k]
        
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {str(e)}")
        raise

def chat_has_documents(chat_id: int) -> bool:
    """Verifica si un chat tiene documentos asociados."""
    try:
        result = supabase.table("documents").select("id").eq("chat_id", chat_id).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Error verificando documentos del chat: {e}")
        return False

class Assistant:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3
        )
        self.current_chat_id = None
        self.rules = orchestrator
    
    def process_message(self, message: str, chat_id: int = None) -> Dict:
        """Procesa un mensaje y retorna la respuesta"""
        
        try:
            # Si no hay chat_id, crear nueva sesión
            if not chat_id:
                response = supabase.table("chat_sessions").insert({
                    "title": "Nueva conversación",
                    "description": "Conversación iniciada"
                }).execute()
                chat_id = response.data[0]["id"]
            
            self.current_chat_id = chat_id
            
            # Solo buscar documentos relevantes si el chat tiene documentos asociados
            context = ""
            references = []
            used_sources = set()  # Para trackear fuentes únicas
            if chat_has_documents(chat_id):
                relevant_docs = search_similar_for_chat(message, chat_id)
                if relevant_docs:
                    # Crear el contexto y las referencias
                    context_parts = []
                    for i, doc in enumerate(relevant_docs, 1):
                        # Agregar número de chunk al contenido para referencia
                        chunk_content = f"[Chunk {i}]\n{doc['content']}\n"
                        context_parts.append(chunk_content)
                        # Crear referencia con metadata
                        ref = {
                            "chunk": i,
                            "content": doc["content"],
                            "metadata": doc["metadata"],
                            "similarity": doc["similarity"]
                        }
                        references.append(ref)
                        # Trackear fuente única - solo el nombre del archivo
                        if doc["metadata"].get("source"):
                            import os
                            filename = os.path.basename(doc["metadata"]["source"])
                            used_sources.add(filename)
                    context = "\n".join(context_parts)
            
            # Guardar mensaje del usuario
            supabase.table("messages").insert({
                "chat_session_id": chat_id,
                "role": "user",
                "content": message,
                "metadata": None
            }).execute()
            
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
                input_variables=["context", "question", "rules"]
            )
            
            chain = (
                {
                    "context": lambda x: f"Contexto: {context}" if context else "No hay documentos asociados a esta conversación.",
                    "question": RunnablePassthrough(),
                    "rules": lambda x: self.rules
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            response = chain.invoke(message)
            
            # Preparar metadata con referencias si existen
            message_metadata = {
                "references": references
            } if references else None
            
            # Guardar respuesta del asistente
            supabase.table("messages").insert({
                "chat_session_id": chat_id,
                "role": "assistant",
                "content": response,
                "metadata": message_metadata
            }).execute()
            
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
                cited_chunks = set(re.findall(r'\[(\d+)\]', response))
                
                for chunk_num in cited_chunks:
                    chunk_idx = int(chunk_num) - 1
                    if chunk_idx < len(references):
                        ref = references[chunk_idx]
                        source_info = f"\n[{ref['chunk']}]"
                        if ref['metadata'].get('page'):
                            source_info += f" (Página {ref['metadata']['page']})"
                        source_info += f":\n{ref['content']}\n"
                        response_with_refs += source_info
            else:
                response_with_refs = response
            
            return {
                "message": response_with_refs,
                "chat_id": chat_id,
                "metadata": message_metadata
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            raise 