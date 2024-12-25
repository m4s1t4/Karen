# 1. Planificación del Proyecto

## 1.1. Visión General

El proyecto se denomina “Asistente Personal”. El objetivo es crear un sistema que:

- **Entienda** las peticiones del usuario (texto o voz).
- **Tenga la capacidad** de ver y analizar lo que ocurre en la pantalla (en tiempo real si es posible).
- **Interactúe** con archivos, directorios y repositorios (GitHub).
- **Escale** para procesar distintos tipos de tareas y coordinar a diferentes “agentes” especializados (Creador de Proyectos, Consultor de Archivos, Administrador de Archivos, etc.).

## 1.2. Objetivos Principales

1. **Orquestación**: El Asistente es quien administra la comunicación entre el _usuario_ y los demás _agentes_, delegando las tareas adecuadas a cada uno.
2. **Creación y Estructuración de Proyectos**: Se deben poder generar proyectos completos (carpetas, archivos, scripts) siguiendo patrones de arquitectura definidos.
3. **Manejo de Archivos**: Incluir la capacidad de crear, editar, actualizar y eliminar archivos, así como la extracción de información de formatos (PDF, DOC, TXT, MD, etc.).
4. **Capacidad de Programación y Automatización**: Correr scripts, realizar RAG (Retrieval Augmented Generation), ejecutar consultas contextuales y corregir errores.
5. **Integración con GitHub**: Crear repositorios, subir cambios, hacer _forks_, manejar _pull requests_, entre otros.
6. **Interfaz de Usuario**: Permitir interacción vía voz o texto, y mostrar resultados en pantalla con actualización en tiempo real (si es posible).

## 1.3. Alcance y Fases de Desarrollo

#### Fase 1: **Análisis & Diseño**

- **Requerimientos**: Detallar cada requerimiento funcional (crear proyectos, RAG, subir a GitHub, etc.) y no funcional (seguridad, rendimiento, etc.).
- **Arquitectura inicial**: Definir la arquitectura multi-agente (Asistente - Creador de Proyectos - Administrador de Archivos - Consultor de Archivos - Admin GitHub).
- **Tecnologías**:
    - Lenguaje principal (por ejemplo, Python + frameworks para IA y voice recognition).
    - Framework web (si se requiere interfaz web) o GUI (si se opta por interfaz de escritorio).
    - Librerías de reconocimiento de voz (SpeechRecognition, pyaudio, etc.).
    - Integración con APIs (GitHub, ChatGPT u otros).

### Fase 2: **Desarrollo de la Base (MVP)**

1. **Módulo de Interfaz** (CLI o GUI básica):
    - Recepción de comandos de texto o voz.
    - Visualización de respuestas en tiempo real.
2. **Módulo de Agentes**:
    - Estructurar la comunicación interna. El Asistente delegará tareas a cada agente especializado.
    - Implementar la lógica de “Creador de Proyectos” (solo la parte básica de la estructura de directorios).
    - Implementar la lógica de “Administrador de Archivos” (crear y eliminar archivos/directorios).
3. **Integración GitHub** (versión inicial):
    - Mínimo: crear repositorios, hacer commit y push.

#### Fase 3: **Funcionalidades Avanzadas**

1. **RAG (Retrieval Augmented Generation)**:
    - Integración con una base vectorial (por ejemplo, _FAISS_, _Chroma_, etc.) para chunking y embeddings.
    - Consultas más complejas a archivos (PDF, DOC, etc.).
2. **Ejecución de Scripts**:
    - Capacidad de leer y ejecutar scripts (por ejemplo, Python, Bash, etc.).
    - Corrección de errores en runtime o con IA.
3. **Mejoras en GitHub**:
    - Fork de repositorios, Pull Requests, revisiones, etc.

#### Fase 4: **Interfaz y Experiencia de Usuario**

- Mejora de la experiencia visual (posible interfaz web con React/Vue/Angular o interfaz de escritorio con PyQt, Electron, etc.).
- Integración de reconocimiento de voz de alta fiabilidad.
- Acceso rápido a logs y debugging.

#### Fase 5: **Pruebas, Optimización y Despliegue**

- **Pruebas unitarias y de integración** de todos los módulos.
- **Optimización** del rendimiento de la IA y la comunicación entre agentes.
- **Despliegue** en un entorno local o en la nube (según sea el caso).

## 1.4. Equipo y Roles

1. **Asistente**: Orquestador principal.
2. **Creador de Proyectos**: Genera la arquitectura de proyectos, crea archivos y directorios según patrones establecidos.
3. **Consultor de Archivos**: Extrae información de PDFs, DOCs, TXTs, etc. y la pone a disposición del Asistente.
4. **Administrador de Archivos**: Opera sobre el sistema de archivos (crear, actualizar, eliminar).
5. **Administrador de GitHub**: Interactúa con la API de GitHub para crear repos, subir cambios, abrir PRs, etc.