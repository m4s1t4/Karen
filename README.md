# Karen - Intelligent Personal Assistant

Karen is an intelligent personal assistant that combines the power of AI with a modern and functional interface. Designed to understand user requests, analyze information, and efficiently manage projects and files.

## 🌟 Features

- **Smart Chat**: Chat interface with persistent history and context
- **Document Processing**:
  - Upload and process PDF documents
  - Smart document chunking and embedding
  - Semantic search within documents
  - Contextual references and citations
- **Project Management**: Creation and structuring of projects following architectural patterns
- **File Management**: Ability to create, edit, and manage files
- **GitHub Integration**: Repository management and Git operations
- **Modern Interface**: Responsive UI with light/dark theme support

## 🛠️ Technologies

### Backend

- Python 3.x
- Flask (REST API)
- OpenAI API (GPT-4 & Embeddings)
- Supabase (Database & Vector Store)
- PostgreSQL with PgVector
- LangChain for document processing

### Frontend

- Next.js 13+
- TypeScript
- TailwindCSS
- Shadcn/UI
- next-themes

## 📁 Project Structure

```
karen/
├── backend/
│   ├── agents/
│   │   ├── assistant.py        # Main assistant logic
│   │   ├── chat_summarizer.py
│   │   └── prompts/           # System prompts
│   ├── db/
│   │   ├── migrations/        # Database migrations
│   │   └── supabase_utils.py
│   ├── rag/                   # Document processing
│   │   └── optimized_rag.py
│   ├── routes/
│   │   └── assistant_routes.py
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
│
└── frontend/
    ├── app/
    │   ├── chat/
    │   ├── projects/
    │   ├── files/
    │   └── github/
    ├── components/
    │   ├── chat/
    │   │   ├── message-item.tsx
    │   │   └── file-upload-button.tsx
    │   ├── chat-sidebar.tsx
    │   ├── mode-toggle.tsx
    │   └── navbar.tsx
    └── ...
```

## 🚀 Installation & Setup

### Backend

1. Create virtual environment and install dependencies:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
# Create .env file in backend root
OPENAI_API_KEY=your_api_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

3. Initialize the database and run migrations:

```bash
python init_db.py
psql -U your_user -d your_database -f db/migrations/add_metadata_to_messages.sql
```

4. Run the server:

```bash
python app.py
```

### Frontend

1. Install dependencies:

```bash
cd frontend
bun install  # or npm install
```

2. Run in development mode:

```bash
bun dev  # or npm run dev
```

## 🔧 Usage

1. Access the application at `http://localhost:3000`
2. The main interface is the chat, where you can:
   - Start new conversations
   - Upload and process documents
   - Get contextual answers with references
   - View chat history
   - Toggle between light/dark themes
   - Manage projects and files

### Document Processing Features

The assistant can process uploaded documents and provide contextual answers with references:

- **Smart Chunking**: Documents are automatically split into meaningful chunks
- **Semantic Search**: Uses OpenAI embeddings for accurate context retrieval
- **Reference System**:
  - Citations in responses using [Chunk X] format
  - Document source tracking
  - Page number references when available
  - Relevance scoring for retrieved chunks

## 📝 API Endpoints

### Chat

- `POST /api/assistant/chat/start`: Start a new chat session
- `POST /api/assistant/chat/message`: Send a message to the assistant
- `GET /api/assistant/chat/history/<session_id>`: Get chat history
- `GET /api/assistant/chat/list`: List all chat sessions
- `DELETE /api/assistant/chat/delete/<session_id>`: Delete a chat

### Documents

- `POST /api/assistant/upload`: Upload and process a document
- `GET /api/assistant/documents/<chat_id>`: Get documents for a chat session
- `DELETE /api/assistant/documents/<document_id>`: Delete a document

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
