from supabase_utils import supabase_manager

def init_tables():
    """Inicializa las tablas en Supabase"""
    try:
        # SQL para crear la tabla de sesiones de chat
        chat_sessions_sql = """
        create table if not exists chat_sessions (
            id bigint primary key generated always as identity,
            user_id text,
            created_at timestamptz default now(),
            updated_at timestamptz default now()
        );
        """
        
        # SQL para crear la tabla de mensajes
        messages_sql = """
        create table if not exists messages (
            id bigint primary key generated always as identity,
            chat_session_id bigint references chat_sessions(id),
            user_id text,
            role text not null,
            content text not null,
            created_at timestamptz default now(),
            updated_at timestamptz default now()
        );
        """
        
        # Ejecutar las consultas SQL
        supabase_manager.supabase.postgrest.rpc('exec', {'query': chat_sessions_sql}).execute()
        print("✅ Tabla chat_sessions creada")
        
        supabase_manager.supabase.postgrest.rpc('exec', {'query': messages_sql}).execute()
        print("✅ Tabla messages creada")
        
        print("\n✨ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar las tablas: {str(e)}")
        return False

if __name__ == "__main__":
    init_tables() 