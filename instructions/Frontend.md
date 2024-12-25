# 1. Objetivos del Frontend

1. **Interfaz de Chat** para conversar con tu Asistente (mostrar y persistir el historial de mensajes).
2. **Secciones** para gestionar Proyectos, Archivos y Repositorios GitHub (según las funcionalidades que brinda tu Backend con Flask + PhiData).
3. **Diseño Responsivo** y moderno, usando **TailwindCSS** como framework de estilos.
4. **Integración** con tu Backend a través de llamadas HTTP (fetch/axios), intercambiando datos en formato JSON.
5. **Escalabilidad** y **mantenibilidad**, gracias a TypeScript y la estructura modular de Next.js.

---

## 2. Planificación General

### 2.1. Creación del Proyecto

- Ejecutar:
  ```bash
  npx create-next-app@latest my-assistant-frontend --typescript --tailwind
  ```
  O, si no usas banderas, instalar manualmente **Tailwind** y **TypeScript**.
- Verificar que la versión de Next.js (15, hipotéticamente) genere una carpeta `app/` con `layout.tsx`, `page.tsx`, `globals.css`, etc.

### 2.2. Estructura y Layout

Con la **estructura estándar** de Next.js 13+ (o superior) como base, ampliamos para incluir las páginas de “chat”, “projects”, “files” y “github”. Una posible organización:

```
frontend/
├── app/
│   ├── layout.tsx           # Layout principal (Navbar, Footer, etc.)
│   ├── page.tsx             # Página inicial (root /)
│   ├── globals.css          # Estilos globales (incluye Tailwind)
│   ├── chat/
│   │   └── page.tsx         # Ruta /chat (interfaz de Chat)
│   ├── projects/
│   │   └── page.tsx         # Ruta /projects
│   ├── files/
│   │   └── page.tsx         # Ruta /files
│   └── github/
│       └── page.tsx         # Ruta /github
├── components/
│   ├── Navbar.tsx           # Barra de navegación global
│   ├── Footer.tsx           # Footer global
│   └── ... (otros comp.)
├── public/
│   └── ... (assets estáticos)
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── tsconfig.json
└── README.md
```

1. **`app/layout.tsx`**:
   - Define un layout global para todas las páginas.
   - Importa `globals.css` y puede incluir `<Navbar />` y `<Footer />`.
2. **`app/page.tsx`**:
   - La **Home** (ruta `/`).
   - Puede ser un dashboard básico o una introducción al Asistente.
3. **Subcarpetas** en `app/` para cada sección: `chat`, `projects`, `files`, `github`.
   - Cada una con su propio `page.tsx`, representando la **ruta** correspondiente.
4. **`components/`**:
   - Directorio con componentes globales reutilizables (Navbar, Footer, Botones, Modales, etc.).
5. **`globals.css`** y `tailwind.config.js`:
   - Configuración y estilos base de TailwindCSS.

### 2.3. Pantallas Clave

1. **Chat (`/chat`)**

   - Muestra historial de mensajes: (user / assistant).
   - Campo de texto + botón “Enviar” para mandar nuevas preguntas al Backend (`/assistant/ask`).
   - Opcional: Botón “Ver Historial Completo”.

2. **Projects (`/projects`)**

   - Formulario para crear proyectos (llamando a `/project/create`).
   - Lista de proyectos ya creados (si el backend los guarda) con enlaces o acciones adicionales.

3. **Files (`/files`)**

   - Vista de la **estructura de archivos** (árbol).
   - Posibilidad de crear, editar, eliminar archivos, usando endpoints del Admin de Archivos en Backend.
   - Un editor de texto (por ejemplo, `react-monaco-editor` o `@uiw/react-textarea-code-editor`) para modificar archivos.

4. **GitHub (`/github`)**

   - Formulario o botones para crear repos, hacer commits/push, PRs, forks, etc.
   - Llamadas a `/github/*` en tu Backend.

---

## 3. Layout de Diseño de cada Pantalla

### 3.1. Chat

```
┌───────────────────────────────────────────┐
│ Navbar                                  │
├───────────────────────────────────────────┤
│ Chat con el Asistente                   │
│ ┌───────────────────────────────────────┐│
│ │ [User] Hola, asistente...           ││
│ │ [Assistant] Hola, en qué te ayudo?  ││
│ │ [User] Crea un proyecto React...    ││
│ │ ...                                 ││
│ └───────────────────────────────────────┘│
│                                          │
│ ┌───────────────────────────────────────┐ │
│ │ [ Escribe tu mensaje ] (Send)        │ │
│ └───────────────────────────────────────┘ │
└───────────────────────────────────────────┘
│ Footer                                   │
└───────────────────────────────────────────┘
```

- **Componente** `ChatWindow` para el historial.
- **Componente** `ChatMessage` para cada mensaje.
- **Manejo** de estado con hooks (ej. `useState` o un `useChatContext`).

### 3.2. Projects

```
┌─────────────────────────────────────────────────┐
│ Navbar                                         │
├─────────────────────────────────────────────────┤
│ Proyectos                                       │
│ ┌───────────────────────────┬──────────────────┐│
│ │ Crear Proyecto           │ Listado Proyectos││
│ │  Nombre: ____            │ - MyProject1     ││
│ │  Tipo: ____              │ - MyProject2     ││
│ │  [ Botón Crear ]         │ - ...            ││
│ └───────────────────────────┴──────────────────┘│
└─────────────────────────────────────────────────┘
│ Footer                                            │
└────────────────────────────────────────────────────┘
```

- **Form**: Llamar `POST /project/create` en el backend.
- **Listado**: Llamar `GET /project/list` (si existe).

### 3.3. Files

```
┌─────────────────────────────────────────────────┐
│ Navbar                                         │
├─────────────────────────────────────────────────┤
│ Archivos                                        │
│ ┌────────────────────┬─────────────────────────┐│
│ │ Estructura         │ Editor                  ││
│ │  - src/            │  [Código del archivo]   ││
│ │     - main.py      │  (Botón Guardar)        ││
│ │     - ...          │                         ││
│ └────────────────────┴─────────────────────────┘│
└─────────────────────────────────────────────────┘
│ Footer                                            │
└────────────────────────────────────────────────────┘
```

- **Arbol** de archivos (GET `/files/structure`).
- **Editor** (PUT/PATCH `/files/update`).

### 3.4. GitHub

```
┌─────────────────────────────────────────────────┐
│ Navbar                                         │
├─────────────────────────────────────────────────┤
│ Integración con GitHub                          │
│  [Crear Repo]  [Push changes]  [Crear PR]       │
│  Lista de repos:                                │
│   - Repo1   - Repo2   - ...                     │
└─────────────────────────────────────────────────┘
│ Footer                                            │
└────────────────────────────────────────────────────┘
```

- **Conexión** con el backend (endpoints `/github/create-repo`, etc.).

---

## 4. Interacción con Backend

1. **Requests** a los endpoints del servidor Flask (por ejemplo, `https://api.midominio.com/assistant/ask`).
2. Manejo de **estado local** o **global** (Context API) según la complejidad.
3. **TypeScript**: Define **tipos**/**interfaces** para las respuestas (por ejemplo, `interface Project { id: number; name: string; ... }`).
4. **Errores** y **loading states**: Manejar con Hooks y condicionales (Tailwind para spinners, alertas, etc.).

---

## 5. Plan de Desarrollo (Sugerido)

1. **Inicializar Proyecto** (Día 1):

   - `npx create-next-app@latest my-assistant-frontend --typescript --tailwind`
   - Verificar layout inicial: `app/layout.tsx`, `app/page.tsx`, `globals.css`.

2. **Layout Global** (Día 1-2):

   - Crear `Navbar.tsx` y `Footer.tsx` en `components/`.
   - Incluirlos en `layout.tsx` para que aparezcan en todas las rutas.

3. **Página de Chat** (Semana 1):

   - `app/chat/page.tsx` con un estado local de mensajes (`useState`).
   - Al enviar un mensaje, hacer `POST` a `/assistant/ask`, actualizar la lista de mensajes.
   - Usar un componente `ChatMessage` con estilos Tailwind.

4. **Página de Proyectos** (Semana 2):

   - `app/projects/page.tsx` con formulario de creación y listado de proyectos.
   - Llamar al backend (`/project/create`, `/project/list`).

5. **Página de Archivos** (Semana 3):

   - `app/files/page.tsx` con un árbol de archivos y editor.
   - Llamar a `/files/` para CRUD de archivos.
   - Integrar un editor de código (opcional) y un panel para la estructura.

6. **Página de GitHub** (Semana 4):

   - `app/github/page.tsx` con botones para crear repos, push changes, etc.
   - Usar endpoints `/github/`.

7. **Refinamientos & Testing** (Semana 5-6):

   - Ajustar detalles de UI (responsividad, colores).
   - Pruebas de integración con el backend.
   - Deploy en la plataforma de tu elección (Vercel, Netlify, etc.).

---

## 6. Resumen Final

1. **Estructura**:

   - Aprovechar la **estructura base** que Next.js 15 (o 13+) crea con `create-next-app`.
   - **Organizar** las secciones en subcarpetas (`chat/`, `projects/`, `files/`, `github/`).
   - Uso de `components/` para elementos globales (Navbar, Footer, etc.).

2. **Diseño**:

   - **TailwindCSS** para un estilo responsivo y rápido de desarrollar.
   - **Layouts** con un `<Navbar>` y `<Footer>` global.
   - Páginas con vistas y formularios específicos para Chat, Proyectos, Archivos, GitHub.

3. **Conexión con Backend**:

   - Llamadas a la API de Flask + PhiData.
   - Manejo de estados y tipados con **React + TypeScript**.

4. **Plan de Desarrollo**:

   - Ir página por página, integrando la lógica necesaria para cada sección y testeando la conexión con el Backend.
