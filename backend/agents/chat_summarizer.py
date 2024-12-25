from openai import OpenAI
from config import Config

class ChatSummarizer:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def generate_title(self, messages):
        """Genera un título corto y descriptivo para el chat basado en los mensajes."""
        if not messages:
            return "Nueva conversación"

        prompt = f"""
        Basándote en los siguientes mensajes de una conversación, genera un título corto (máximo 50 caracteres) 
        que resuma el tema principal. El título debe ser conciso pero descriptivo.

        Mensajes:
        {self._format_messages(messages)}

        Genera solo el título, sin comillas ni puntos finales.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=50
        )

        return response.choices[0].message.content.strip()

    def generate_description(self, messages):
        """Genera una descripción breve del contenido del chat."""
        if not messages:
            return "Conversación sin mensajes"

        prompt = f"""
        Basándote en los siguientes mensajes de una conversación, genera una descripción breve (máximo 150 caracteres)
        que resuma los puntos principales discutidos.

        Mensajes:
        {self._format_messages(messages)}

        Genera solo la descripción, sin puntos finales.
        """

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=50
        )

        return response.choices[0].message.content.strip()

    def _format_messages(self, messages):
        """Formatea los mensajes para incluirlos en el prompt."""
        formatted = []
        for msg in messages:
            role = "Usuario" if msg["role"] == "user" else "Karen"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted) 