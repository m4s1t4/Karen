from db.supabase_utils import supabase_manager

def init_tables():
    """Inicializa las tablas en Supabase"""
    try:
        # SQL para crear la tabla de sesiones de chat
        chat_sessions_sql = """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id BIGSERIAL PRIMARY KEY,
            title VARCHAR,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """

        # SQL para crear la tabla de mensajes
        messages_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGSERIAL PRIMARY KEY,
            session_id BIGINT REFERENCES chat_sessions(id) ON DELETE CASCADE,
            role VARCHAR NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """

        # Ejecutar las consultas SQL
        supabase_manager.supabase.postgrest.rpc('exec_sql', {'query': chat_sessions_sql}).execute()
        supabase_manager.supabase.postgrest.rpc('exec_sql', {'query': messages_sql}).execute()

        print("✅ Tablas inicializadas correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar las tablas: {str(e)}")
        raise e

if __name__ == "__main__":
    init_tables() 