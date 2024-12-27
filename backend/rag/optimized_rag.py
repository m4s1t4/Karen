import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import tenacity
from tqdm import tqdm

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.schema import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from supabase.client import Client, create_client

import dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
SCRIPT_DIR = Path(__file__).parent.absolute()
dotenv.load_dotenv()

# Configuración de parámetros optimizados
CHUNK_SIZE = 1000  # Tamaño de chunk para embeddings
BATCH_SIZE = 500   # Aumentado para menos llamadas a Supabase
MAX_WORKERS = 8    # Más workers para mejor paralelismo
EMBEDDING_MODEL = "text-embedding-ada-002"  # Modelo con 1536 dimensiones
EMBEDDING_BATCH_SIZE = 100  # Aumentado para menos llamadas a la API
MAX_RETRIES = 3    # Número máximo de reintentos

# Configurar Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Cache para embeddings
@lru_cache(maxsize=1000)
def get_cached_embedding(text: str) -> List[float]:
    """Cache para embeddings frecuentes."""
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        chunk_size=EMBEDDING_BATCH_SIZE
    )
    return embeddings.embed_query(text)

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    stop=tenacity.stop_after_attempt(5),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.warning(
        f"Error al generar embeddings, reintentando en {retry_state.next_action.sleep} segundos..."
    )
)
def get_embeddings_with_retry(texts: List[str]) -> List[List[float]]:
    """Genera embeddings con retry logic y procesamiento en lotes."""
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        chunk_size=EMBEDDING_BATCH_SIZE
    )
    return embeddings.embed_documents(texts)

def process_chunk_batch(batch: List[Document]) -> List[Dict]:
    """Procesa un lote de chunks en paralelo."""
    texts = [chunk.page_content for chunk in batch]
    try:
        embeddings_batch = get_embeddings_with_retry(texts)
        
        # Verificar dimensiones
        if any(len(emb) != 1536 for emb in embeddings_batch):
            logger.error("Dimensiones de embeddings incorrectas")
            return []
            
        return [
            {
                "content": chunk.page_content,
                "metadata": chunk.metadata,
                "embedding": embedding
            }
            for chunk, embedding in zip(batch, embeddings_batch)
        ]
    except Exception as e:
        logger.error(f"Error procesando lote: {e}")
        return []

def process_chunks_in_batches(chunks: List[Document]) -> List[Dict]:
    """Procesa chunks en lotes con procesamiento paralelo mejorado."""
    all_data = []
    total_chunks = len(chunks)
    
    # Calcular número óptimo de workers basado en CPU y tamaño de datos
    optimal_workers = min(MAX_WORKERS, (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE)
    
    with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
        # Dividir chunks en lotes más grandes
        batches = [
            chunks[i:i + BATCH_SIZE] 
            for i in range(0, len(chunks), BATCH_SIZE)
        ]
        
        # Crear futures para procesamiento paralelo
        futures = {
            executor.submit(process_chunk_batch, batch): i 
            for i, batch in enumerate(batches)
        }
        
        # Procesar resultados con barra de progreso
        with tqdm(
            total=len(batches),
            desc="Procesando chunks"
        ) as pbar:
            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_data.extend(result)
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Error en lote {batch_idx}: {e}")
                    continue
    
    return all_data

def store_chunks_in_supabase(chunks: List[Dict], chat_id: int) -> Tuple[int, int]:
    """Almacena los chunks en Supabase de forma optimizada."""
    successful = 0
    retries = 0
    batch_size = 100  # Reducir el tamaño del lote para evitar timeouts
    
    try:
        # Dividir en lotes más pequeños
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            documents = []
            
            for chunk in batch:
                doc = {
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "embedding": chunk["embedding"],
                    "chat_id": chat_id
                }
                documents.append(doc)
            
            # Intentar insertar con reintentos
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    result = supabase.table("documents").insert(documents).execute()
                    if not result.data:
                        raise Exception("No se recibió confirmación de inserción")
                    successful += len(documents)
                    break
                except Exception as e:
                    retry_count += 1
                    retries += 1
                    logger.warning(f"Reintento {retry_count} para lote {i//batch_size + 1}: {str(e)}")
                    if retry_count == max_retries:
                        logger.error(f"Error insertando lote {i//batch_size + 1} después de {max_retries} intentos: {str(e)}")
                    else:
                        time.sleep(2 ** retry_count)  # Espera exponencial entre reintentos
            
            # Pequeña pausa entre lotes para evitar sobrecarga
            time.sleep(0.5)
            
        return successful, retries
        
    except Exception as e:
        logger.error(f"Error almacenando chunks: {str(e)}")
        return successful, retries

class OptimizedRAG:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0
        )
    
    def load_documents(self, file_path: str) -> List[Document]:
        """Carga un documento individual con logging mejorado."""
        logger.info(f"Cargando documento: {file_path}")
        start_time = time.time()
        
        try:
            # Cargar solo el archivo especificado
            loader = PyPDFDirectoryLoader(str(Path(file_path).parent))
            all_documents = loader.load()
            
            # Filtrar para obtener solo el archivo deseado
            documents = [
                doc for doc in all_documents 
                if Path(doc.metadata["source"]).name == Path(file_path).name
            ]
            
            if not documents:
                raise FileNotFoundError(f"No se pudo cargar el archivo: {file_path}")
            
            duration = time.time() - start_time
            logger.info(f"Documento cargado en {duration:.2f}s")
            return documents
            
        except Exception as e:
            logger.error(f"Error cargando documento {file_path}: {e}")
            raise

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """División optimizada de documentos."""
        logger.info("Iniciando división de documento")
        start_time = time.time()
        
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            
            chunks = []
            for doc in documents:
                splits = splitter.split_text(doc.page_content)
                chunks.extend([
                    Document(
                        page_content=split,
                        metadata={
                            **doc.metadata,
                            "chunk_index": i,
                            "total_chunks": len(splits)
                        }
                    ) for i, split in enumerate(splits)
                ])
            
            duration = time.time() - start_time
            logger.info(f"Documento dividido en {len(chunks)} chunks en {duration:.2f}s")
            return chunks
            
        except Exception as e:
            logger.error(f"Error dividiendo documento: {e}")
            raise

    def store_in_supabase(self, chunks: List[Document], chat_id: int):
        """Almacena documentos en Supabase con relación al chat."""
        logger.info(f"Almacenando chunks en Supabase para el chat {chat_id}")
        start_time = time.time()
        
        try:
            # Procesar chunks en paralelo
            data = process_chunks_in_batches(chunks)
            
            if not data:
                logger.error("No hay datos válidos para almacenar")
                return
            
            # Agregar chat_id a cada documento
            for item in data:
                item["chat_id"] = chat_id
            
            total_items = len(data)
            successful_inserts = 0
            retry_count = 0
            
            # Reducir el tamaño del lote y aumentar el tiempo entre reintentos
            BATCH_SIZE = 50  # Lotes más pequeños
            MAX_RETRIES = 5  # Más intentos
            
            # Insertar en lotes con progreso y reintentos
            with tqdm(total=total_items, desc="Insertando en Supabase") as pbar:
                for i in range(0, total_items, BATCH_SIZE):
                    batch = data[i:i + BATCH_SIZE]
                    success = False
                    attempts = 0
                    
                    while not success and attempts < MAX_RETRIES:
                        try:
                            # Dividir el lote en sub-lotes más pequeños
                            SUB_BATCH_SIZE = 10
                            for j in range(0, len(batch), SUB_BATCH_SIZE):
                                sub_batch = batch[j:j + SUB_BATCH_SIZE]
                                response = supabase.table("documents").insert(
                                    sub_batch,
                                    returning="minimal",
                                    count="exact"
                                ).execute()
                                
                                if hasattr(response, 'error') and response.error is not None:
                                    raise Exception(f"Error de Supabase: {response.error}")
                                
                                successful_inserts += len(sub_batch)
                                pbar.update(len(sub_batch))
                                
                                # Pausa entre sub-lotes
                                time.sleep(0.5)
                            
                            success = True
                            
                        except Exception as e:
                            attempts += 1
                            retry_count += 1
                            if attempts < MAX_RETRIES:
                                wait_time = min(30, 2 ** (attempts + 2))  # Máximo 30 segundos
                                logger.warning(f"Reintento {attempts} para lote {i//BATCH_SIZE + 1}: {e}")
                                logger.info(f"Esperando {wait_time} segundos antes del siguiente intento...")
                                time.sleep(wait_time)
                            else:
                                logger.error(f"Error insertando lote {i//BATCH_SIZE + 1} después de {MAX_RETRIES} intentos: {e}")
                                # Continuar con el siguiente lote en lugar de fallar completamente
                                break
                    
                    # Pausa entre lotes principales
                    time.sleep(1)
            
            duration = time.time() - start_time
            success_rate = (successful_inserts/total_items*100) if total_items > 0 else 0
            logger.info(
                f"Chunks almacenados en {duration:.2f}s. "
                f"Exitosos: {successful_inserts}/{total_items} ({success_rate:.1f}%). "
                f"Reintentos: {retry_count}"
            )
            
        except Exception as e:
            logger.error(f"Error almacenando chunks: {e}")
            raise
    
    async def upload_file_to_supabase(self, file_path: str, chat_id: int) -> str:
        """Sube un archivo a Supabase Storage y retorna su URL."""
        try:
            file_name = Path(file_path).name
            bucket_name = "chat-files"
            
            # Asegurarse de que el bucket existe
            try:
                supabase.storage.get_bucket(bucket_name)
            except:
                supabase.storage.create_bucket(bucket_name)
            
            # Subir archivo
            with open(file_path, 'rb') as f:
                file_path_in_supabase = f"chat_{chat_id}/{file_name}"
                supabase.storage.from_(bucket_name).upload(
                    file_path_in_supabase,
                    f
                )
            
            # Obtener URL del archivo
            file_url = supabase.storage.from_(bucket_name).get_public_url(file_path_in_supabase)
            
            # Registrar archivo en la tabla de archivos
            supabase.table("chat_files").insert({
                "chat_id": chat_id,
                "file_name": file_name,
                "file_url": file_url,
                "file_path": file_path_in_supabase
            }).execute()
            
            return file_url
            
        except Exception as e:
            logger.error(f"Error subiendo archivo a Supabase: {e}")
            raise
    
    async def process_file(self, file_path: str, chat_id: int):
        """Procesa un archivo y lo almacena en Supabase."""
        try:
            logger.info(f"Iniciando procesamiento de {file_path}")
            start_time = time.time()
            
            # Subir archivo a Supabase Storage
            file_url = await self.upload_file_to_supabase(file_path, chat_id)
            
            # Cargar y procesar documento
            documents = self.load_documents(str(Path(file_path).parent))
            documents = [
                doc for doc in documents 
                if Path(doc.metadata["source"]).name == Path(file_path).name
            ]
            
            if not documents:
                raise FileNotFoundError(f"No se pudo cargar el archivo: {file_path}")
            
            # Agregar metadata adicional
            for doc in documents:
                doc.metadata["file_url"] = file_url
                doc.metadata["chat_id"] = chat_id
            
            # Dividir en chunks y almacenar
            chunks = self.split_documents(documents)
            self.store_in_supabase(chunks, chat_id)
            
            duration = time.time() - start_time
            logger.info(f"Archivo procesado exitosamente en {duration:.2f}s")
            
            return file_url
            
        except Exception as e:
            logger.error(f"Error procesando archivo {file_path}: {e}")
            raise
    
    def query(self, question: str) -> str:
        """Consulta optimizada con cache."""
        try:
            # Buscar documentos relevantes
            relevant_docs = search_similar(question)
            
            if not relevant_docs:
                return "No encontré información relevante para responder tu pregunta."
            
            # Crear prompt
            prompt = PromptTemplate(
                template="""Utiliza el siguiente contexto para responder la pregunta.
                Si la información no está en el contexto, di "No tengo suficiente información".
                
                Contexto: {context}
                Pregunta: {question}
                
                Respuesta:""",
                input_variables=["context", "question"]
            )
            
            # Crear y ejecutar cadena RAG
            chain = (
                {"context": lambda x: "\n".join(d["content"] for d in relevant_docs), "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            return chain.invoke(question)
            
        except Exception as e:
            logger.error(f"Error en consulta: {e}")
            return "Lo siento, hubo un error procesando tu pregunta. Por favor, intenta de nuevo." 