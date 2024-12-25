import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from supabase import create_client
from config import Config

# Crear cliente de Supabase
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def init_tables():
    """Inicializa las tablas en Supabase"""
    try:
        # Eliminar registros existentes en orden inverso (por las foreign keys)
        print("Eliminando registros existentes...")
        supabase.table("messages").delete().neq("id", 0).execute()
        supabase.table("chat_sessions").delete().neq("id", 0).execute()
        
        # SQL para recrear las tablas
        recreate_tables_sql = """
        drop table if exists messages;
        drop table if exists chat_sessions;
        
        create table if not exists chat_sessions (
            id bigint primary key generated always as identity,
            title text default 'Nueva conversación',
            description text default 'Conversación sin mensajes',
            created_at timestamptz default now(),
            updated_at timestamptz default now()
        );
        
        create table if not exists messages (
            id bigint primary key generated always as identity,
            chat_session_id bigint references chat_sessions(id) on delete cascade,
            role text not null,
            content text not null,
            created_at timestamptz default now(),
            updated_at timestamptz default now()
        );
        """
        
        # Ejecutar las consultas SQL
        print("Recreando tablas...")
        supabase.postgrest.rpc('exec', {'query': recreate_tables_sql}).execute()
        
        print("\n✨ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar las tablas: {str(e)}")
        return False

if __name__ == "__main__":
    init_tables() 