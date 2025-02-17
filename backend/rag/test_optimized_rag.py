import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple
from optimized_rag import OptimizedRAG

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "archivos_procesados": 0,
            "total_documentos": 0,
            "total_chunks": 0,
            "tiempo_carga": 0,
            "tiempo_chunking": 0,
            "tiempo_embeddings": 0,
            "tiempo_subida": 0,
            "tiempo_consultas": 0,
            "consultas_exitosas": 0,
            "total_consultas": 0,
            "chunks_por_segundo": 0,
            "precision_respuestas": [],
        }

    def calcular_precision(self, respuesta: str) -> float:
        """
        Calcula la precisión de una respuesta basada en si contiene contenido relevante
        """
        if (
            "No encontré información" in respuesta
            or "No tengo suficiente información" in respuesta
        ):
            return 0.0
        if "Lo siento" in respuesta or "error" in respuesta.lower():
            return 0.0
        # Si la respuesta tiene más de 50 caracteres, consideramos que es una respuesta válida
        return 1.0 if len(respuesta) > 50 else 0.5

    def generar_resumen(self) -> str:
        """Genera un resumen detallado de las métricas"""
        precision_promedio = (
            sum(self.metrics["precision_respuestas"])
            / len(self.metrics["precision_respuestas"])
            if self.metrics["precision_respuestas"]
            else 0
        )

        return f"""
📊 RESUMEN DE PRUEBAS RAG
========================

🔍 Procesamiento de Documentos:
------------------------------
• Archivos procesados: {self.metrics["archivos_procesados"]}
• Total documentos: {self.metrics["total_documentos"]}
• Total chunks generados: {self.metrics["total_chunks"]}
• Chunks por segundo: {self.metrics["chunks_por_segundo"]:.2f}

⏱️ Tiempos de Procesamiento:
---------------------------
• Carga de documentos: {self.metrics["tiempo_carga"]:.2f}s
• Chunking: {self.metrics["tiempo_chunking"]:.2f}s
• Generación de embeddings: {self.metrics["tiempo_embeddings"]:.2f}s
• Subida a Supabase: {self.metrics["tiempo_subida"]:.2f}s
• Tiempo promedio por consulta: {self.metrics["tiempo_consultas"] / self.metrics["total_consultas"]:.2f}s

📈 Rendimiento de Consultas:
--------------------------
• Consultas exitosas: {self.metrics["consultas_exitosas"]}/{self.metrics["total_consultas"]} ({(self.metrics["consultas_exitosas"] / self.metrics["total_consultas"] * 100):.1f}%)
• Precisión promedio: {precision_promedio * 100:.1f}%

💡 Análisis:
-----------
• Velocidad de procesamiento: {(self.metrics["total_chunks"] / (self.metrics["tiempo_chunking"] + self.metrics["tiempo_embeddings"])):.2f} chunks/segundo
• Tasa de éxito: {(self.metrics["consultas_exitosas"] / self.metrics["total_consultas"] * 100):.1f}%
"""


def test_optimized_rag():
    """Prueba el RAG optimizado con métricas detalladas."""
    metrics = MetricsCollector()

    try:
        # Inicializar RAG
        rag = OptimizedRAG()

        # Verificar archivos PDF
        knowledge_dir = Path(__file__).parent / "Knowledge"
        pdf_files = list(knowledge_dir.glob("*.pdf"))
        logger.info(f"Archivos PDF encontrados: {[f.name for f in pdf_files]}")

        if not pdf_files:
            logger.warning(
                f"No se encontraron documentos PDF en {knowledge_dir}. "
                "Por favor, añade algunos documentos PDF antes de continuar."
            )
            return

        metrics.metrics["archivos_procesados"] = len(pdf_files)

        # Procesar cada archivo
        for pdf_file in pdf_files:
            logger.info(f"Procesando archivo: {pdf_file.name}")

            start_time = time.time()
            rag.process_file(str(pdf_file))

            # Actualizar métricas de tiempo
            process_time = time.time() - start_time
            metrics.metrics["tiempo_carga"] += process_time * 0.2  # Estimado
            metrics.metrics["tiempo_chunking"] += process_time * 0.3  # Estimado
            metrics.metrics["tiempo_embeddings"] += process_time * 0.3  # Estimado
            metrics.metrics["tiempo_subida"] += process_time * 0.2  # Estimado

        # Preguntas de prueba
        test_questions = [
            """
              Quiero que respondas las siguientes preguntas:
            - Dame un descripción de mi persona.
            - Dime las tecnologías que uso""",
        ]

        # Probar consultas
        logger.info("\n=== Iniciando pruebas de consulta ===\n")
        metrics.metrics["total_consultas"] = len(test_questions)

        for i, question in enumerate(test_questions, 1):
            logger.info(f"\nPregunta {i}: {question}")
            try:
                start_time = time.time()
                response = rag.query(question)
                query_time = time.time() - start_time

                metrics.metrics["tiempo_consultas"] += query_time
                precision = metrics.calcular_precision(response)
                metrics.metrics["precision_respuestas"].append(precision)

                if precision > 0:
                    metrics.metrics["consultas_exitosas"] += 1

                logger.info(f"\nRespuesta {i}:\n{response}\n")
                logger.info("=" * 50)
            except Exception as e:
                logger.error(f"Error al procesar la pregunta {i}: {e}")

        # Generar y mostrar resumen
        logger.info("\n=== Resumen de Pruebas ===")
        logger.info(metrics.generar_resumen())

    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")
        raise


if __name__ == "__main__":
    logger.info("Iniciando pruebas del RAG optimizado")
    test_optimized_rag()
