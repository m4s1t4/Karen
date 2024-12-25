## 1. Estructura Global del Proyecto

```
backend/
├── app.py
├── requirements.txt
├── config.py
├── main.py
├── db/
│   ├── models.py           # Definición de tablas/ORM (Mensajes, ChatSession, etc.)
│   └── db_utils.py         # Funciones de conexión y setup de la BD
├── agents/
│   ├── __init__.py
│   ├── assistant.py        # Orquestador principal
│   ├── project_creator.py  # Creador de proyectos
│   ├── file_consultant.py  # Consulta de archivos (RAG)
│   ├── file_admin.py       # Administrador de archivos
│   └── github_admin.py     # Administrador de repos en GitHub
├── routes/
│   ├── __init__.py
│   ├── assistant_routes.py
│   ├── project_creator_routes.py
│   ├── file_consultant_routes.py
│   ├── file_admin_routes.py
│   └── github_admin_routes.py
└── ...
```

- **`app.py`**: Configura Flask (crea la aplicación, registra blueprints).
- **`requirements.txt`**: Dependencias y versiones.
- **`db/`**: Lógica de base de datos (modelos con SQLAlchemy, PostgreSQL, PgVector).
- **`agents/`**: Cada _agente_ implementado con PhiData, con sus herramientas específicas.
- **`routes/`**: Blueprints de Flask, cada archivo agrupa endpoints de un agente o funcionalidad.

---

## 2. Uso de Python (Flask) + PhiData

### 2.1. PhiData para los Agentes

Cada agente se implementa con la clase `Agent` de PhiData, especificando:

- **Modelo** (p. ej. `OpenAIChat(id="gpt-4")`)
- **Tools** (DuckDuckGo, Newspaper4k, o herramientas personalizadas)
- **Descripción** e **instrucciones** (definen el rol y la responsabilidad del agente)

Por ejemplo, para el Agente Asistente (orquestador):

```python
# agents/assistant.py
from phi.agent import Agent
from phi.model.openai import OpenAIChat

assistant_agent = Agent(
    model=OpenAIChat(id="gpt-4"),
    description="Eres el Asistente principal, orquestas todo el sistema.",
    instructions=[
        "Coordina con el Creador de Proyectos, Consultor de Archivos, etc.",
        "Usa RAG cuando se requiera contexto adicional de la base de datos."
    ],
    markdown=True,
    show_tool_calls=True,
)

def run(query: str) -> str:
    # Lógica para guardar el mensaje del usuario en BD, generar embeddings, etc.
    # Recuperar mensajes previos / RAG con PgVector
    # Construir prompt y ejecutar assistant_agent.run(prompt)
    # Guardar la respuesta en la BD y retornarla
    ...
```

### 2.2. Flask Endpoints

Cada agente puede exponer uno o varios endpoints en un blueprint de Flask. Ejemplo de “assistant”:

```python
# routes/assistant_routes.py
from flask import Blueprint, request, jsonify
from agents.assistant import run as run_assistant

assistant_bp = Blueprint('assistant_bp', __name__)

@assistant_bp.route('/ask', methods=['POST'])
def ask_assistant():
    data = request.json
    user_query = data.get("query", "")
    response_text = run_assistant(user_query)
    return jsonify({"response": response_text})
```

---

## 3. Persistencia de Chats y RAG con PostgreSQL + PgVector

### 3.1. Modelo de Datos

```python
# db/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import VECTOR

from db.db_utils import Base

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=True)
    user_id = Column(String, nullable=True)
    role = Column(String, nullable=False)   # "user" o "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    # Vector de longitud 1536 (por ej. embeddings OpenAI)
    embedding = Column(VECTOR(1536), nullable=True)
```

### 3.2. Flujo de Mensajes

1. **Usuario envía** una pregunta (texto o voz transcrito).
2. **Se crea** un registro `Message` con la `role='user'`, se genera su embedding y se guarda en la BD.
3. **Se recuperan** los últimos 5 mensajes (o se hace RAG con PgVector) para armar el contexto.
4. **El agente** genera respuesta, se guarda también como `Message(role='assistant', ...)` con su embedding.
5. **Se retorna** la respuesta al usuario.

### 3.3. Ejemplo de Consulta Semántica

```sql
SELECT id, content
FROM messages
ORDER BY embedding <-> :query_embedding
LIMIT 5;
```

Donde `<->` es el operador de distancia vectorial de pgvector.

---

## 4. Diagrama de Flujo de Información

![[Pasted image 20241225161448.png]]

- **User**: Inicia la interacción.
- **Asistente**: Recibe la petición y decide si requiere RAG, creación de proyectos, consulta de archivos, etc.
- **RAG**: Consulta la base vectorial (PgVector) para encontrar información relevante en los mensajes o archivos.
- **Consultor de Archivos**: Extrae contenido y lo devuelve al Asistente.
- **Creador de Proyectos**: Crea la arquitectura de proyectos. Puede necesitar el **Admin Archivos** para escribir en disco.
- **Admin Archivos**: Opera en el sistema de archivos (crear, editar, eliminar).

---

## 3. Manejando Conversación y RAG en el Backend

### 3.1. Flujo General

1. **Usuario envía un mensaje** (texto o voz transcrito) a la ruta `/assistant/ask`.
2. **Flask** recibe el mensaje, lo guarda en la BD (con su embedding).
3. **Se obtienen** los últimos 5 mensajes de la BD o se hace una búsqueda semántica en PgVector para recuperar el contexto relevante.
4. **Se llama** al “Asistente” (el `Assistant Agent` de PhiData) pasándole tanto la nueva pregunta como el resumen o los 5 mensajes recuperados.
5. **El Asistente** genera la respuesta, la guardamos en la BD (incluyendo embedding).
6. **Se regresa** la respuesta al usuario.

### 3.2. Creación de Embeddings

Para almacenar y buscar con embeddings, lo más común es que, **antes** de guardar un mensaje en la BD, generemos su embedding con algún modelo (por ejemplo, `text-embedding-ada-002` de OpenAI).

Ejemplo simplificado (pseudocódigo):
```python
from openai.embeddings_utils import get_embedding

def store_user_message(user_id: str, content: str, role="user"):
    # Generar embedding con OpenAI
    embedding_vector = get_embedding(content, engine="text-embedding-ada-002")

    # Crear instancia de modelo SQLAlchemy
    message_obj = Message(
        user_id=user_id,
        content=content,
        role=role,
        embedding=embedding_vector
    )
    db.session.add(message_obj)
    db.session.commit()
```
Luego, para **recuperar** los 5 mensajes anteriores:
```python
def get_last_5_messages():
    return (db.session.query(Message)
                     .order_by(Message.created_at.desc())
                     .limit(5)
                     .all())

```
O para **búsqueda semántica**:
```python
def get_similar_messages(query: str, top_k=5):
    query_embedding = get_embedding(query, engine="text-embedding-ada-002")
    # vector -> array de floats
    # depende de la forma en que configuraste la columna vector:
    return db.session.execute("""
        SELECT *
        FROM messages
        ORDER BY embedding <-> :query_embedding
        LIMIT :top_k
    """, {"query_embedding": query_embedding, "top_k": top_k}).fetchall()
```
---
## 4. Ajustes en los Agentes con PhiData

### 4.1. Cómo pasarles las “últimas 5 interacciones” o el “contexto”:

En **PhiData** con un `Agent`, puedes construir dinámicamente su `instructions` o un **prompt** base que incluya el texto de los últimos 5 mensajes (o el snippet más relevante). Por ejemplo:
```python
# agents/assistant.py

def build_context_string():
    last_messages = get_last_5_messages()  # O get_similar_messages()
    # Generar un texto que contenga "User said: ..." o algo similar
    context_str = ""
    for msg in reversed(last_messages): 
        # reversed para que aparezcan en orden cronológico
        context_str += f"{msg.role.capitalize()} said: {msg.content}\n"
    return context_str

assistant_agent = Agent(
    model=OpenAIChat(id="gpt-4"),
    # tools=[DuckDuckGo(), ...],
    description="Eres el Asistente principal, con la capacidad de recordar contexto.",
    instructions=[
        # Nota: Podrías dejar un set de 'instrucciones' fijas aquí
    ],
    markdown=True,
    show_tool_calls=True,
)

def run(query: str) -> str:
    # 1. Guardar el mensaje del usuario con su embedding
    store_user_message(user_id="123", content=query, role="user")

    # 2. Obtener contexto
    context = build_context_string()

    # 3. Enriquecer prompt
    complete_prompt = f"Contexto:\n{context}\n\nNueva pregunta del usuario: {query}"

    # 4. Invocar al agente
    response_text = assistant_agent.run(complete_prompt)

    # 5. Guardar respuesta en la BD
    store_user_message(user_id="assistant", content=response_text, role="assistant")

    return response_text
```
> Con este flujo, cada **query** y **respuesta** queda registrada en la DB, y cada nuevo turno de conversación añade más mensajes. Cuando inicias el agente, en realidad estás usando tu “assistant_agent” con la info recuperada desde la BD.
---
## 5. Rutas (EndPoints) Actualizadas

### 5.1. `/assistant/ask` (POST)
```python
# routes/assistant_routes.py

from flask import Blueprint, request, jsonify
from agents.assistant import run as run_assistant

assistant_bp = Blueprint('assistant_bp', __name__)

@assistant_bp.route('/ask', methods=['POST'])
def ask_assistant():
    data = request.json
    user_query = data.get("query", "")
    
    # Llamada a la función del agente
    response_text = run_assistant(user_query)
    
    return jsonify({"response": response_text})
```
5.2. (Opcional) Endpoint para ver historial `/assistant/history`
```python
@assistant_bp.route('/history', methods=['GET'])
def get_history():
    last_msgs = get_last_5_messages()
    return jsonify([
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in last_msgs
    ])
```
---
## 6. Librerías y Versiones Recomendadas

En tu **`requirements.txt`** o _Poetry_, se sugiere:
```txt
# Flask
Flask==2.3.3       # Versión estable 2.x

# SQLAlchemy (para ORM con Postgres)
SQLAlchemy==2.0.19

# Driver Postgres
psycopg2==2.9.7   # O psycopg2-binary

# pgvector (Python binding) - depende de la implementación que uses
pgvector==0.1.8   # Ajustar a la versión actual

# PhiData - última versión disponible
phi-data==[última versión]

# openai - para embeddings
openai==0.28.0   # Ajustar a la versión más reciente

# Extra librerías que puedas usar
duckduckgo_search==2.9.5  # si la usas
newspaper4k==0.2.8        # etc.
```
_Nota:_ Revisa las versiones vigentes al momento de desarrollo, ya que pueden cambiar con frecuencia.

---
## 7. Resumen

1. **Persistencia de Conversaciones**:
    - Se guardan mensajes (rol: user/assistant) en PostgreSQL con su **embedding** (usando OpenAI u otro modelo).
2. **Recuperación de Historial**:
    - Seleccionar los últimos 5 mensajes o hacer una búsqueda semántica con PgVector para traer mensajes relevantes.
3. **Integración con PhiData**:
    - Los agentes (por ejemplo, `assistant_agent`) reciben el contexto (últimos mensajes) y la nueva pregunta.
    - Generan la respuesta y la devuelven, registrando también la respuesta en la BD.
4. **Flask Endpoints**:
    - `/assistant/ask` para recibir preguntas del usuario.
    - Rutas adicionales según los agentes (proyectos, archivos, GitHub), cada uno con su blueprint.
5. **Últimas Versiones de Librerías**:
    - Actualizar `Flask`, `SQLAlchemy`, `PhiData`, `openai`, `pgvector`, etc. a las releases más recientes.
6. **Ventajas**:
    - Con **PgVector** + PostgreSQL, tu Asistente puede escalar el RAG de modo robusto y eficiente.
    - Mantienes la historia conversacional, lo que permite más coherencia al Asistente y la capacidad de “buscar” en el historial cuando sea necesario.