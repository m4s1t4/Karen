-- Agregar columna metadata como JSONB a la tabla messages
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Crear un índice GIN para búsquedas eficientes en el campo metadata
CREATE INDEX IF NOT EXISTS idx_messages_metadata 
ON messages USING GIN (metadata);

-- Comentario para la columna
COMMENT ON COLUMN messages.metadata IS 'Almacena metadatos adicionales del mensaje como referencias a documentos, chunks, etc.'; 