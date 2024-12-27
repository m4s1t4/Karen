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
        
        # Llamar a la función match_documents_for_chat
        result = supabase.rpc(
            'match_documents_for_chat',
            {
                'query_embedding': query_embedding,
                'chat_id': chat_id,
                'match_threshold': 0.7,
                'match_count': top_k
            }
        ).execute()
        
        if hasattr(result, 'error') and result.error is not None:
            logger.error(f"Error en match_documents_for_chat: {result.error}")
            raise Exception(f"Error en match_documents_for_chat: {result.error}")
            
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {str(e)}")
        raise

def check_documents_exist(chat_id: int) -> bool:
    """Verifica si existen documentos para un chat específico."""
    try:
        result = supabase.table("documents") \
            .select("id", count="exact") \
            .eq("chat_id", chat_id) \
            .execute()
        return result.count > 0 if result.count is not None else False
    except Exception as e:
        logger.error(f"Error verificando documentos: {str(e)}")
        return False

class Assistant:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0
        )
        self.current_chat_id = None

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
            
            # Verificar si hay documentos antes de hacer la búsqueda semántica
            has_documents = check_documents_exist(chat_id)
            relevant_docs = []
            
            if has_documents:
                # Solo buscar documentos relevantes si existen documentos para este chat
                relevant_docs = search_similar_for_chat(message, chat_id)
            
            # Crear el contexto con los documentos relevantes
            context = ""
            if relevant_docs:
                context = "\n".join(d["content"] for d in relevant_docs)
            
            # Guardar mensaje del usuario
            supabase.table("messages").insert({
                "chat_session_id": chat_id,
                "role": "user",
                "content": message
            }).execute()
            
            # Generar respuesta
            prompt = PromptTemplate(
                template="""Utiliza el siguiente contexto para responder la pregunta.
                Si la información no está en el contexto, responde basándote en tu conocimiento general.
                
                Contexto: {context}
                Pregunta: {question}
                
                Respuesta:""",
                input_variables=["context", "question"]
            )

            chain = (
                {"context": lambda x: context, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            response = chain.invoke(message)
            
            # Guardar respuesta del asistente
            supabase.table("messages").insert({
                "chat_session_id": chat_id,
                "role": "assistant",
                "content": response
            }).execute()
            
            return {
                "message": response,
                "chat_id": chat_id
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            raise 