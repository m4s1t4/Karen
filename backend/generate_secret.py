import secrets
import os
from pathlib import Path

def generate_secret_key():
    """Genera una clave secreta segura y la guarda en .env"""
    # Generar clave secreta
    secret_key = secrets.token_hex(32)
    
    # Ruta al archivo .env
    env_path = Path('.env')
    
    # Si el archivo .env existe, leer su contenido
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Buscar si ya existe SECRET_KEY
        secret_key_exists = False
        for i, line in enumerate(lines):
            if line.startswith('SECRET_KEY='):
                lines[i] = f'SECRET_KEY={secret_key}\n'
                secret_key_exists = True
                break
        
        # Si no existe, añadirla
        if not secret_key_exists:
            lines.append(f'\nSECRET_KEY={secret_key}\n')
        
        # Escribir el archivo actualizado
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    else:
        # Si no existe el archivo .env, crearlo con la SECRET_KEY
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f'SECRET_KEY={secret_key}\n')
    
    print(f"\nSe ha generado una nueva SECRET_KEY y se ha guardado en el archivo .env")
    print(f"La clave generada es: {secret_key}")
    print("\nNOTA: Asegúrate de nunca compartir esta clave ni subirla a control de versiones.")

if __name__ == '__main__':
    generate_secret_key() 