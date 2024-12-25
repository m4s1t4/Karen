# 2. Layout de Diseño de la Aplicación

Para entenderlo mejor, dividiremos el layout en **Front-end**, **Back-end** (o lógica central), y **Módulos internos** (agentes).

## 2.1. Estructura General

```
┌──────────────────────────────────────┐
│              Usuario               │
│ (Interfaz de Texto/Voz en Tiempo   │
│    Real y/o GUI/CLI/Web)           │
└──────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│             Asistente               │
│  (Orquestador y Punto de Entrada)   │
└──────────────────────────────────────┘
               │
    ┌──────────┼───────────┐
    │          │           │
    ▼          ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│  RAG    │ │Creador  │ │Admin.   │
│(Consultor│ │Proyectos│ │Archivos │
│de Archivos)│ └─────────┘ └─────────┘
└─────────┘          │
               ┌─────┴─────────────────┐
               │       Admin. GitHub   │
               └───────────────────────┘
```

1. **Usuario**: Interactúa vía comandos de voz/texto.
2. **Asistente**: El _core_ que recibe la petición y decide a qué agente enviarla.
3. **RAG / Consultor de Archivos**:
    - Indexa la información y la hace disponible para el Asistente.
    - Permite búsquedas contextuales en la documentación/archivos.
4. **Creador de Proyectos**:
    - Se encarga de generar la arquitectura de un proyecto nuevo.
    - Crea directorios, subdirectorios y archivos base.
5. **Administrador de Archivos**:
    - Maneja la creación, lectura, edición y borrado de archivos en el disco.
6. **Administrador de GitHub**:
    - Conecta con la API de GitHub para repos, commits, pushes, forks, PRs, etc.

## 2.2. Diagramas de Módulos

### 2.2.1. Módulo de Interfaz (Front-end)

- **Componente de Reconocimiento de Voz** (opcional, si se desea integrarlo directamente en la app):
    - Captura de audio -> Transcribe -> Envía texto al Asistente.
- **Componente de Text/CLI**:
    - Terminal o caja de texto.
    - Envía las peticiones al Asistente y recibe la respuesta.

### 2.2.2. Módulo Asistente (Back-end)

- **Router / Dispatcher**:
    - Analiza el mensaje (por ejemplo, “Crea un proyecto con 3 capas”).
    - Determina si es tarea de Creador de Proyectos, Consultor de Archivos, etc.
- **Context Manager**:
    - Mantiene información del estado (sesión, variables, etc.) para no perder contexto.
- **Orquestador**:
    - Interactúa con RAG para consultas de contexto.
    - Interactúa con el Administrador de GitHub para operaciones en repositorios.

### 2.2.3. Módulo de Agentes (Servicios Internos)

1. **Consultor de Archivos (RAG)**:
    
    - _Vector DB/Chunker_: Almacena la información extraída de archivos en forma de _embeddings_ para búsquedas semánticas.
    - _Processor/Extractor_: Lógica para parsear PDFs, DOCs, TXTs, etc.
2. **Creador de Proyectos**:
    
    - _Project Template Loader_: Contiene plantillas (templates) de estructura de proyecto.
    - _File Generator_: Crea archivos base, `README.md`, `.gitignore`, etc.
3. **Administrador de Archivos**:
    
    - _File System Interface_: Métodos para crear carpetas, leer archivos, escribir en archivos, borrar, etc.
    - _Error Handler & Logger_: Manejo de errores y logging de operaciones.
4. **Administrador de GitHub**:
    
    - _GitHub API Manager_: Autenticación, creación de repos, push, pull requests, etc.
    - _Repo Synchronizer_: Mantiene sincronizados los cambios con GitHub.

## 2.3. Diseño de Interfaz (Mockup / Boceto)

#### Opción A: CLI/Terminal

```
+---------------------------------------------+
| Asistente Personal (CLI)                    |
|---------------------------------------------|
| Usuario: Hola, crea un proyecto Django.     |
| Asistente: Entendido. Nombre del proyecto?  |
| Usuario: "MiProyectoDjango"                 |
| Asistente: Proyecto creado con éxito.       |
|           ¿Deseas subirlo a GitHub? (S/N)   |
| Usuario: Sí                                 |
| Asistente: Repositorio creado y subido.     |
|---------------------------------------------|
| >                                           |
+---------------------------------------------+
```

#### Opción B: Web/GUI

- **Pantalla Principal**:
    - Barra lateral con menús (Proyectos, Archivos, Configuración de GitHub, RAG).
    - Sección central con el “Chat” o “Console” para interactuar con el Asistente.
- **Modal de Creación de Proyectos**: Permite configurar nombre, estructura, lenguaje, etc.
- **Panel de Archivos**: Lista en árbol de los archivos/directorios creados.

## 2.4. Flujo de Interacción Típico

1. **El usuario da un comando** (vía voz o texto).
2. **El Asistente** recibe el comando y lo analiza:
    - Si se trata de crear un proyecto, delega al **Creador de Proyectos**.
    - Si se trata de una consulta a un archivo, usa el **Consultor de Archivos** (RAG).
    - Si es para manipular un archivo local (crear, modificar, eliminar), se llama al **Administrador de Archivos**.
    - Si debe trabajar con un repositorio remoto, interviene el **Administrador de GitHub**.
3. **El agente correspondiente** ejecuta la tarea y retorna el estado/resultado al Asistente.
4. **El Asistente** retorna la respuesta al usuario.