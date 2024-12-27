"use client";

import { useState, useEffect } from "react";
import { useChat } from "@/contexts/chat-context";
import { useToast } from "@/components/ui/use-toast";
import { Message } from "@/types/chat";
import { MessageList } from "@/components/message-list";
import { MessageInput } from "@/components/message-input";

export default function ChatPage() {
  const { currentChatId, setCurrentChat, isNewChat } = useChat();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    // Cargar mensajes cuando cambie el chat
    if (currentChatId && !isNewChat) {
      fetch(`http://localhost:5000/api/assistant/chat/history/${currentChatId}`)
        .then((res) => res.json())
        .then((data) => setMessages(data))
        .catch((error) => console.error("Error al cargar mensajes:", error));
    } else {
      setMessages([]);
    }
  }, [currentChatId, isNewChat]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    try {
      setIsLoading(true);
      const messageContent = input;
      setInput("");

      // Agregar mensaje del usuario inmediatamente
      const userMessage: Message = {
        role: "user",
        content: messageContent,
        created_at: new Date().toISOString(),
      };

      // Actualizar mensajes con el mensaje del usuario
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);

      // Enviar mensaje al backend
      const response = await fetch(
        "http://localhost:5000/api/assistant/chat/message",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: messageContent,
            session_id: currentChatId,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Error al enviar mensaje");
      }

      const data = await response.json();

      // Si es un chat nuevo, actualizar el ID
      if (isNewChat && data.session_id) {
        setCurrentChat(data.session_id);
      }

      // Agregar respuesta del asistente
      const assistantMessage: Message = {
        role: "assistant",
        content: data.message,
        created_at: new Date().toISOString(),
      };

      // Actualizar mensajes incluyendo la respuesta del asistente
      setMessages((prevMessages) => [...prevMessages, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Hubo un error al enviar el mensaje",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent<HTMLFormElement>);
    }
  };

  return (
    <div className="flex h-full">
      <div className="w-full flex flex-col">
        {messages.length > 0 ? (
          <>
            <MessageList messages={messages} isLoading={isLoading} />
            <div className="p-4">
              <div className="mx-auto max-w-[800px]">
                <MessageInput
                  input={input}
                  isLoading={isLoading}
                  onSubmit={handleSubmit}
                  onChange={setInput}
                  onKeyDown={handleKeyDown}
                  disabled={!currentChatId && !isNewChat}
                />
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="w-full max-w-[600px] px-4">
              <MessageInput
                input={input}
                isLoading={isLoading}
                onSubmit={handleSubmit}
                onChange={setInput}
                onKeyDown={handleKeyDown}
                disabled={!currentChatId && !isNewChat}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
