"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { AutoResizeTextarea } from "@/components/autoresize-textarea";
import { ArrowUpIcon, Loader2, Paperclip } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat } from "@/contexts/chat-context";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";
import { Skeleton } from "@/components/ui/skeleton";

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
      const messageContent = input;
      setInput("");

      // Agregar mensaje del usuario inmediatamente
      const userMessage: Message = {
        role: "user",
        content: messageContent,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

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
        {messages.length > 0 ? (
          <>
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
                          : ""
                      }`}
                    >
                      {message.role === "assistant" ? (
                        <ReactMarkdown
                          className="text-sm prose dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:p-0"
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex, rehypeHighlight]}
                          components={{
                            p: ({ children }) => (
                              <p className="mb-2 last:mb-0">{children}</p>
                            ),
                            pre: ({ children }) => (
                              <pre className="bg-secondary/50 rounded-md p-4 overflow-x-auto">
                                {children}
                              </pre>
                            ),
                            code: ({
                              node,
                              inline,
                              className,
                              children,
                              ...props
                            }) => {
                              if (inline) {
                                return (
                                  <code
                                    className="bg-secondary/50 rounded-sm px-1 py-0.5"
                                    {...props}
                                  >
                                    {children}
                                  </code>
                                );
                              }
                              return (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              );
                            },
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="text-sm">{message.content}</p>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading &&
                  messages.length > 0 &&
                  messages[messages.length - 1].role === "user" && (
                    <div className="flex justify-start">
                      <div className="max-w-[80%] rounded-lg px-4 py-2">
                        <div className="flex flex-col gap-3">
                          <div className="flex items-center gap-2">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            <span className="text-sm text-muted-foreground">
                              Karen está escribiendo
                            </span>
                          </div>
                          <div className="space-y-2">
                            <Skeleton className="h-4 w-[250px]" />
                            <Skeleton className="h-4 w-[200px]" />
                            <Skeleton className="h-4 w-[150px]" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
              </div>
            </ScrollArea>
            <div className="p-4">
              <div className="mx-auto max-w-[800px]">
                <form
                  onSubmit={handleSubmit}
                  className="relative flex items-center rounded-[16px] border px-3 py-1.5 pr-8 text-sm backdrop-blur-md backdrop-filter space-x-5"
                >
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="submit"
                        variant="ghost"
                        size="sm"
                        className="absolute bottom-1 left-1 size-6 rounded-full"
                      >
                        {isLoading ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Paperclip size={16} />
                        )}
                        <span className="sr-only">
                          {isLoading ? "Enviando..." : "Enviar mensaje"}
                        </span>
                      </Button>
                    </TooltipTrigger>
                  </Tooltip>
                  <AutoResizeTextarea
                    onKeyDown={handleKeyDown}
                    onChange={(v) => setInput(v)}
                    value={input}
                    placeholder="Escribe un mensaje..."
                    className="placeholder:text-muted-foreground flex-1 bg-transparent focus:outline-none "
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
                        disabled={
                          isLoading ||
                          (!currentChatId && !isNewChat) ||
                          !input.trim()
                        }
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
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="w-full max-w-[600px] px-4">
              <form
                onSubmit={handleSubmit}
                className="relative flex items-center rounded-[16px] border px-3 py-1.5 pr-8 text-sm backdrop-blur-md backdrop-filter space-x-5"
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="submit"
                      variant="ghost"
                      size="sm"
                      className="absolute bottom-1 left-1 size-6 rounded-full"
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Paperclip size={16} />
                      )}
                      <span className="sr-only">
                        {isLoading ? "Enviando..." : "Enviar mensaje"}
                      </span>
                    </Button>
                  </TooltipTrigger>
                </Tooltip>
                <AutoResizeTextarea
                  onKeyDown={handleKeyDown}
                  onChange={(v) => setInput(v)}
                  value={input}
                  placeholder="Escribe un mensaje..."
                  className="placeholder:text-muted-foreground flex-1 bg-transparent focus:outline-none "
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
                      disabled={
                        isLoading ||
                        (!currentChatId && !isNewChat) ||
                        !input.trim()
                      }
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
        )}
      </div>
    </div>
  );
}
