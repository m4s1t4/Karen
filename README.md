# Karen - Intelligent Personal Assistant

Karen is an intelligent personal assistant that combines the power of AI with a modern and functional interface. Designed to understand user requests, analyze information, and efficiently manage projects and files.

## 🌟 Features

- **Smart Chat**: Chat interface with persistent history and context
- **Project Management**: Creation and structuring of projects following architectural patterns
- **File Management**: Ability to create, edit, and manage files
- **GitHub Integration**: Repository management and Git operations
- **Modern Interface**: Responsive UI with light/dark theme support

## 🛠️ Technologies

### Backend

- Python 3.x
- Flask (REST API)
- OpenAI API
- Supabase (Database)
- PostgreSQL with PgVector

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
│   │   ├── assistant.py
│   │   ├── chat_summarizer.py
│   │   └── ...
│   ├── db/
│   │   └── supabase_utils.py
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

3. Initialize the database:

```bash
python init_db.py
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
   - View chat history
   - Toggle between light/dark themes
   - Manage projects and files

## 📝 API Endpoints

### Chat

- `POST /api/assistant/chat/start`: Start a new chat session
- `POST /api/assistant/chat/message`: Send a message to the assistant
- `GET /api/assistant/chat/history/<session_id>`: Get chat history
- `GET /api/assistant/chat/list`: List all chat sessions
- `DELETE /api/assistant/chat/delete/<session_id>`: Delete a chat

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
