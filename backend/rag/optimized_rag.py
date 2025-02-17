import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import tenacity
from tqdm import tqdm
import numpy as np

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.vectorstores.supabase import SupabaseVectorStore
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
CHUNK_OVERLAP = 50  # Superposición entre chunks
EMBEDDING_MODEL = "text-embedding-ada-002"  # Modelo con 1536 dimensiones
EMBEDDING_BATCH_SIZE = 500  # Aumentado para menos llamadas a la API

# Configurar Supabase
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


class OptimizedRAG:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL, chunk_size=EMBEDDING_BATCH_SIZE
        )
        self.vector_store = SupabaseVectorStore(
            client=supabase,
            embedding=self.embeddings,
            table_name="documents",
            query_name="match_documents",
        )

    def load_documents(self, file_path: str) -> List[Document]:
        """Carga un documento individual con logging mejorado."""
        logger.info(f"Cargando documento: {file_path}")
        start_time = time.time()

        try:
            loader = PyPDFDirectoryLoader(str(Path(file_path).parent))
            all_documents = loader.load()

            documents = [
                doc
                for doc in all_documents
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
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            )

            chunks = []
            for doc in documents:
                splits = splitter.split_text(doc.page_content)
                chunks.extend(
                    [
                        Document(
                            page_content=split,
                            metadata={
                                **doc.metadata,
                                "chunk_index": i,
                                "total_chunks": len(splits),
                            },
                        )
                        for i, split in enumerate(splits)
                    ]
                )

            duration = time.time() - start_time
            logger.info(
                f"Documento dividido en {len(chunks)} chunks en {duration:.2f}s"
            )
            return chunks

        except Exception as e:
            logger.error(f"Error dividiendo documento: {e}")
            raise

    def store_in_supabase(self, chunks: List[Document], chat_id: int):
        """Almacena documentos en Supabase Vector Store."""
        logger.info(f"Almacenando chunks en Supabase para el chat {chat_id}")
        start_time = time.time()

        try:
            # Agregar chat_id a la metadata de cada documento
            for chunk in chunks:
                chunk.metadata["chat_id"] = chat_id
                # Asegurarse de que no haya campos que puedan causar conflictos
                if "id" in chunk.metadata:
                    del chunk.metadata["id"]

            # Preparar los documentos para inserción
            documents_to_insert = []

            # Generar embeddings en lotes
            texts = [chunk.page_content for chunk in chunks]
            embeddings = []

            for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
                batch = texts[i : i + EMBEDDING_BATCH_SIZE]
                batch_embeddings = self.embeddings.embed_documents(batch)
                embeddings.extend(batch_embeddings)
                logger.info(
                    f"Procesado lote de embeddings {i // EMBEDDING_BATCH_SIZE + 1}"
                )

            # Verificar dimensiones
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if len(embedding) != 1536:
                    logger.warning(
                        f"Embedding {i} tiene dimensión incorrecta: {len(embedding)}"
                    )
                    continue

                doc = {
                    "content": chunk.page_content,
                    "metadata": chunk.metadata,
                    "embedding": embedding,
                    "chat_id": chat_id,  # Agregar chat_id como campo directo
                }
                documents_to_insert.append(doc)

            if not documents_to_insert:
                raise Exception("No se pudieron generar embeddings válidos")

            # Insertar documentos en Supabase
            response = supabase.table("documents").insert(documents_to_insert).execute()

            if hasattr(response, "error") and response.error is not None:
                raise Exception(f"Error insertando documentos: {response.error}")

            duration = time.time() - start_time
            logger.info(f"Chunks almacenados exitosamente en {duration:.2f}s")
            logger.info(
                f"Se almacenaron {len(documents_to_insert)} documentos para el chat {chat_id}"
            )

        except Exception as e:
            logger.error(f"Error almacenando chunks: {str(e)}")
            raise

    async def upload_file_to_supabase(self, file_path: str, chat_id: int) -> str:
        """Sube un archivo a Supabase Storage y retorna su URL."""
        try:
            # Verificar si el chat existe
            logger.info(f"Verificando si existe el chat {chat_id}...")
            chat_exists = (
                supabase.table("chat_sessions").select("id").eq("id", chat_id).execute()
            )

            if not chat_exists.data:
                logger.info(f"Chat {chat_id} no existe, creando uno nuevo...")
                chat_response = (
                    supabase.table("chat_sessions")
                    .insert(
                        {
                            "title": "Nueva conversación",
                            "description": "Conversación iniciada por subida de archivo",
                        }
                    )
                    .execute()
                )
                if not chat_response.data:
                    raise Exception("No se pudo crear el chat")
                # Usar el ID generado automáticamente
                chat_id = chat_response.data[0]["id"]
                logger.info(f"Chat creado exitosamente con ID: {chat_id}")
            else:
                logger.info(f"Usando chat existente con ID: {chat_id}")

            file_name = Path(file_path).name
            bucket_name = "chat-files"

            logger.info(f"Intentando subir archivo {file_name} al bucket {bucket_name}")

            # Verificar que el bucket existe
            try:
                logger.info("Verificando si el bucket existe...")
                bucket = supabase.storage.get_bucket(bucket_name)
                logger.info(f"Bucket encontrado: {bucket}")
            except Exception as e:
                logger.warning(f"Bucket no encontrado, intentando crear: {str(e)}")
                try:
                    supabase.storage.create_bucket(
                        id=bucket_name,
                        options={
                            "public": True,
                            "file_size_limit": 5242880,
                            "allowed_mime_types": ["application/pdf"],
                        },
                    )
                    logger.info("Bucket creado exitosamente")
                except Exception as create_error:
                    logger.error(f"Error creando bucket: {str(create_error)}")
                    raise

            # Generar un nombre único para el archivo usando timestamp
            import time

            timestamp = int(time.time())
            file_name_without_ext = Path(file_name).stem
            file_extension = Path(file_name).suffix
            unique_file_name = f"{file_name_without_ext}_{timestamp}{file_extension}"

            # Subir archivo
            logger.info(
                f"Iniciando subida del archivo con nombre único: {unique_file_name}"
            )
            with open(file_path, "rb") as f:
                file_path_in_supabase = f"chat_{chat_id}/{unique_file_name}"
                try:
                    result = supabase.storage.from_(bucket_name).upload(
                        path=file_path_in_supabase,
                        file=f,
                        file_options={"content-type": "application/pdf"},
                    )
                    logger.info(f"Archivo subido exitosamente: {result}")
                except Exception as upload_error:
                    logger.error(f"Error en la subida: {str(upload_error)}")
                    raise

            # Obtener URL del archivo
            try:
                file_url = supabase.storage.from_(bucket_name).get_public_url(
                    file_path_in_supabase
                )
                logger.info(f"URL pública obtenida: {file_url}")
            except Exception as url_error:
                logger.error(f"Error obteniendo URL pública: {str(url_error)}")
                raise

            # Registrar archivo en la tabla de archivos
            try:
                logger.info("Registrando archivo en la base de datos...")
                result = (
                    supabase.table("chat_files")
                    .insert(
                        {
                            "chat_id": chat_id,
                            "file_name": file_name,  # Guardamos el nombre original
                            "file_url": file_url,
                            "file_path": file_path_in_supabase,
                        }
                    )
                    .execute()
                )
                logger.info("Archivo registrado exitosamente en la base de datos")
            except Exception as db_error:
                logger.error(f"Error registrando en base de datos: {str(db_error)}")
                raise

            return file_url

        except Exception as e:
            logger.error(f"Error subiendo archivo a Supabase: {str(e)}")
            if hasattr(e, "response"):
                logger.error(
                    f"Detalles de la respuesta: {e.response.text if hasattr(e.response, 'text') else str(e.response)}"
                )
            raise

    async def process_file(self, file_path: str, chat_id: int):
        """Procesa un archivo y lo almacena en Supabase."""
        try:
            logger.info(f"Iniciando procesamiento de {file_path}")
            start_time = time.time()

            # Subir archivo a Supabase Storage
            file_url = await self.upload_file_to_supabase(file_path, chat_id)

            # Verificar si el chat existe
            chat_exists = (
                supabase.table("chat_sessions").select("id").eq("id", chat_id).execute()
            )

            # Si el chat no existe, obtener el último chat creado
            if not chat_exists.data:
                latest_chat = (
                    supabase.table("chat_sessions")
                    .select("id")
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if latest_chat.data:
                    chat_id = latest_chat.data[0]["id"]
                    logger.info(f"Usando el nuevo chat_id: {chat_id}")
                else:
                    raise Exception("No se pudo encontrar o crear un chat válido")

            # Cargar y procesar documento
            documents = self.load_documents(file_path)

            # Agregar metadata adicional
            for doc in documents:
                doc.metadata["file_url"] = file_url
                doc.metadata["chat_id"] = chat_id
                if "id" in doc.metadata:
                    del doc.metadata["id"]

            # Dividir en chunks y almacenar
            chunks = self.split_documents(documents)
            self.store_in_supabase(chunks, chat_id)

            duration = time.time() - start_time
            logger.info(f"Archivo procesado exitosamente en {duration:.2f}s")

            # Preparar resumen del archivo procesado
            file_info = {
                "file_name": Path(file_path).name,
                "file_url": file_url,
                "num_chunks": len(chunks),
                "chat_id": chat_id,  # Incluir el chat_id actualizado
                "chunks": [
                    {"content": chunk.page_content, "metadata": chunk.metadata}
                    for chunk in chunks
                ],
            }

            return file_info

        except Exception as e:
            logger.error(f"Error procesando archivo {file_path}: {e}")
            raise

    def query(self, question: str, chat_id: int) -> str:
        """Realiza una búsqueda semántica en la base de datos vectorial."""
        try:
            logger.info(f"Buscando documentos relevantes para chat {chat_id}")
            # Realizar búsqueda de similitud
            relevant_docs = self.vector_store.similarity_search_with_relevance_scores(
                question,
                k=4,  # Número de documentos a recuperar
                filter={
                    "metadata": {"chat_id": chat_id}
                },  # Filtrar por chat_id en metadata
            )

            if not relevant_docs:
                return "No encontré información relevante para responder tu pregunta."

            # Formatear el contexto con los documentos relevantes
            formatted_context = []
            for i, (doc, score) in enumerate(relevant_docs, 1):
                # Solo incluir documentos con score mayor a 0.7 para asegurar relevancia
                if score > 0.7:
                    # Incluir metadata relevante en el contexto
                    source_info = ""
                    if doc.metadata.get("source"):
                        from pathlib import Path

                        filename = Path(doc.metadata["source"]).name
                        source_info = f" [Fuente: {filename}]"
                    if doc.metadata.get("page"):
                        source_info += f" [Página: {doc.metadata['page']}]"

                    chunk_text = f"[Fragmento {i}] (Relevancia: {score:.2f}){source_info}\n{doc.page_content}\n"
                    formatted_context.append(chunk_text)

            if not formatted_context:
                return "Aunque encontré algunos documentos, no son lo suficientemente relevantes para tu pregunta. ¿Podrías reformularla?"

            context = "\n".join(formatted_context)

            # Crear prompt mejorado
            prompt = PromptTemplate(
                template="""Utiliza el siguiente contexto para responder la pregunta.
                Si la información no está en el contexto, di "No tengo suficiente información para responder esa pregunta específica".

                Reglas:
                1. SIEMPRE cita los fragmentos específicos usando [Fragmento X] cuando uses información de ellos
                2. Si la información está dispersa en varios fragmentos, combínalos de manera coherente
                3. Si hay información contradictoria entre fragmentos, señálalo explícitamente
                4. Mantén un tono profesional y claro
                5. Si la pregunta tiene múltiples partes, responde cada una por separado
                6. NO inventes información que no esté en los fragmentos
                7. Si un fragmento tiene información de una página específica, inclúyela en la cita

                Contexto:
                {context}

                Pregunta: {question}

                Respuesta:""",
                input_variables=["context", "question"],
            )

            # Crear y ejecutar cadena RAG
            chain = (
                {
                    "context": lambda x: context,
                    "question": RunnablePassthrough(),
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )

            response = chain.invoke(question)
            logger.info("Respuesta generada exitosamente")

            # Agregar un resumen de las fuentes utilizadas
            used_chunks = set()
            import re

            for match in re.finditer(r"\[Fragmento (\d+)\]", response):
                used_chunks.add(int(match.group(1)))

            if used_chunks:
                response += "\n\n---\nFuentes utilizadas:\n"
                for chunk_num in sorted(used_chunks):
                    if chunk_num <= len(relevant_docs):
                        doc, score = relevant_docs[chunk_num - 1]
                        source_info = ""
                        if doc.metadata.get("source"):
                            filename = Path(doc.metadata["source"]).name
                            source_info = f"[Archivo: {filename}]"
                        if doc.metadata.get("page"):
                            source_info += f" [Página: {doc.metadata['page']}]"
                        response += f"\n[Fragmento {chunk_num}] {source_info} (Relevancia: {score:.2f})"

            return response

        except Exception as e:
            logger.error(f"Error en consulta: {e}")
            return "Lo siento, hubo un error procesando tu pregunta. Por favor, intenta de nuevo."
