import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
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

def load_documents(path: str = str(SCRIPT_DIR / "Knowledge")) -> List[Document]:
    """Carga documentos con logging mejorado."""
    logger.info(f"Cargando documentos desde: {path}")
    start_time = time.time()
    
    loader = PyPDFDirectoryLoader(path)
    documents = loader.load()
    
    duration = time.time() - start_time
    logger.info(f"Cargados {len(documents)} documentos en {duration:.2f}s")
    return documents

def split_documents(documents: List[Document]) -> List[Document]:
    """División optimizada de documentos con mejor manejo de memoria."""
    logger.info("Iniciando división de documentos")
    start_time = time.time()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    
    chunks = []
    for doc in tqdm(documents, desc="Dividiendo documentos"):
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
    logger.info(f"Documentos divididos en {len(chunks)} chunks en {duration:.2f}s")
    return chunks

def store_in_supabase(chunks: List[Document]):
    """Almacena documentos en Supabase con inserción en lotes optimizada."""
    logger.info("Almacenando documentos en Supabase")
    start_time = time.time()
    
    # Procesar chunks en paralelo
    data = process_chunks_in_batches(chunks)
    
    if not data:
        logger.error("No hay datos válidos para almacenar")
        return
    
    total_items = len(data)
    successful_inserts = 0
    retry_count = 0
    
    # Insertar en lotes grandes con progreso y reintentos
    with tqdm(
        total=total_items,
        desc="Insertando en Supabase"
    ) as pbar:
        for i in range(0, total_items, BATCH_SIZE):
            batch = data[i:i + BATCH_SIZE]
            success = False
            attempts = 0
            
            while not success and attempts < MAX_RETRIES:
                try:
                    # Verificar dimensiones antes de insertar
                    if any(len(item["embedding"]) != 1536 for item in batch):
                        logger.error(f"Dimensiones incorrectas en lote {i//BATCH_SIZE}")
                        break
                    
                    # Insertar usando la sintaxis correcta de Supabase
                    response = supabase.table("documents").insert(
                        batch,
                        returning="minimal",  # Solo retorna IDs
                        count="exact"  # Obtener conteo exacto
                    ).execute()
                    
                    if hasattr(response, 'error') and response.error is not None:
                        raise Exception(f"Error de Supabase: {response.error}")
                    
                    successful_inserts += len(batch)
                    pbar.update(len(batch))
                    success = True
                    
                except Exception as e:
                    attempts += 1
                    retry_count += 1
                    if attempts < MAX_RETRIES:
                        logger.warning(f"Reintento {attempts} para lote {i//BATCH_SIZE}: {e}")
                        time.sleep(2 ** attempts)  # Espera exponencial
                    else:
                        logger.error(f"Error insertando lote {i//BATCH_SIZE} después de {MAX_RETRIES} intentos: {e}")
    
    duration = time.time() - start_time
    logger.info(
        f"Documentos almacenados en {duration:.2f}s. "
        f"Exitosos: {successful_inserts}/{total_items} ({successful_inserts/total_items*100:.1f}%). "
        f"Reintentos: {retry_count}"
    )

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    stop=tenacity.stop_after_attempt(5),
    retry=tenacity.retry_if_exception_type(Exception)
)
def search_similar(query: str, top_k: int = 5) -> List[Dict]:
    """Búsqueda semántica optimizada."""
    try:
        # Intentar obtener embedding desde cache
        try:
            query_embedding = get_cached_embedding(query)
            
            # Verificar dimensiones
            if len(query_embedding) != 1536:
                raise ValueError("Dimensiones de embedding incorrectas")
                
        except Exception:
            # Si falla el cache, usar método normal
            embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                chunk_size=EMBEDDING_BATCH_SIZE
            )
            query_embedding = embeddings.embed_query(query)
        
        # Verificar que el embedding sea una lista de floats
        if not isinstance(query_embedding, list) or not all(isinstance(x, float) for x in query_embedding):
            raise ValueError("Embedding debe ser una lista de floats")
            
        # Verificar longitud del embedding
        if len(query_embedding) != 1536:
            raise ValueError(f"Embedding debe tener 1536 dimensiones, tiene {len(query_embedding)}")
        
        # Llamar a la función match_documents
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.7,
                'match_count': top_k
            }
        ).execute()
        
        if hasattr(result, 'error') and result.error is not None:
            logger.error(f"Error en match_documents: {result.error}")
            raise Exception(f"Error en match_documents: {result.error}")
            
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {str(e)}")
        raise

class OptimizedRAG:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0
        )
    
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
    
    def store_in_supabase(self, chunks: List[Document], chat_id: int):
        """Almacena documentos en Supabase con relación al chat."""
        logger.info("Almacenando documentos en Supabase")
        start_time = time.time()
        
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
        
        # Insertar en lotes grandes con progreso y reintentos
        with tqdm(total=total_items, desc="Insertando en Supabase") as pbar:
            for i in range(0, total_items, BATCH_SIZE):
                batch = data[i:i + BATCH_SIZE]
                success = False
                attempts = 0
                
                while not success and attempts < MAX_RETRIES:
                    try:
                        response = supabase.table("documents").insert(
                            batch,
                            returning="minimal",
                            count="exact"
                        ).execute()
                        
                        if hasattr(response, 'error') and response.error is not None:
                            raise Exception(f"Error de Supabase: {response.error}")
                        
                        successful_inserts += len(batch)
                        pbar.update(len(batch))
                        success = True
                        
                    except Exception as e:
                        attempts += 1
                        retry_count += 1
                        if attempts < MAX_RETRIES:
                            logger.warning(f"Reintento {attempts} para lote {i//BATCH_SIZE}: {e}")
                            time.sleep(2 ** attempts)
                        else:
                            logger.error(f"Error insertando lote {i//BATCH_SIZE} después de {MAX_RETRIES} intentos: {e}")
        
        duration = time.time() - start_time
        logger.info(
            f"Documentos almacenados en {duration:.2f}s. "
            f"Exitosos: {successful_inserts}/{total_items} ({successful_inserts/total_items*100:.1f}%). "
            f"Reintentos: {retry_count}"
        )
    
    async def process_file(self, file_path: str, chat_id: int):
        """Procesa un archivo y lo almacena en Supabase."""
        try:
            logger.info(f"Iniciando procesamiento de {file_path}")
            start_time = time.time()
            
            # Subir archivo a Supabase Storage
            file_url = await self.upload_file_to_supabase(file_path, chat_id)
            
            # Cargar y procesar documento
            documents = load_documents(str(Path(file_path).parent))
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
            chunks = split_documents(documents)
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