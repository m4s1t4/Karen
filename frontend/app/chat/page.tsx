"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { AutoResizeTextarea } from "@/components/autoresize-textarea";
import { ArrowUpIcon, Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat } from "@/contexts/chat-context";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export default function ChatPage() {
  const { currentChatId, setCurrentChat, isNewChat } = useChat();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

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
      let chatId = currentChatId;

      // Si es un chat nuevo, crearlo primero
      if (isNewChat) {
        const createResponse = await fetch(
          "http://localhost:5000/api/assistant/chat/start",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (!createResponse.ok) {
          throw new Error("Error al crear nuevo chat");
        }

        const data = await createResponse.json();
        chatId = data.session_id;
        setCurrentChat(chatId);
      }

      // Agregar mensaje del usuario
      const userMessage: Message = {
        role: "user",
        content: input,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setInput("");

      // Enviar mensaje al backend
      const response = await fetch(
        "http://localhost:5000/api/assistant/chat/message",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: input,
            session_id: chatId,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Error al enviar mensaje");
      }

      const data = await response.json();

      // Agregar respuesta del asistente
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
      // TODO: Mostrar error al usuario
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
        <ScrollArea className="flex-1">
          <div className="mx-auto max-w-[800px] space-y-4 p-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg px-4 py-2 bg-muted">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span>Karen está escribiendo...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="p-4 ">
          <div className="mx-auto max-w-[800px]">
            <form
              onSubmit={handleSubmit}
              className="bg-background focus-within:ring-ring/10 relative flex items-center rounded-[16px] border px-3 py-1.5 pr-8 text-sm focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-0 backdrop-blur-md backdrop-filter"
            >
              <AutoResizeTextarea
                onKeyDown={handleKeyDown}
                onChange={(v) => setInput(v)}
                value={input}
                placeholder="Escribe un mensaje..."
                className="placeholder:text-muted-foreground flex-1 bg-transparent focus:outline-none"
                disabled={isLoading}
              />
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="submit"
                    variant="ghost"
                    size="sm"
                    className={cn(
                      "absolute bottom-1 right-1 size-6 rounded-full transition-transform",
                      isLoading && "rotate-180"
                    )}
                    disabled={isLoading || !currentChatId || !input.trim()}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ArrowUpIcon size={16} />
                    )}
                    <span className="sr-only">
                      {isLoading ? "Enviando..." : "Enviar mensaje"}
                    </span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" align="end">
                  {isLoading ? "Enviando..." : "Enviar mensaje (Enter)"}
                </TooltipContent>
              </Tooltip>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
