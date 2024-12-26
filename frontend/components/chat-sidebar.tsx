"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface Chat {
  id: number;
  created_at: string;
  title: string;
  description: string;
}

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectChat: (chatId: number) => void;
  onDeleteChat: (chatId: number) => void;
  selectedChatId?: number;
}

export function ChatSidebar({
  isOpen,
  onClose,
  onSelectChat,
  onDeleteChat,
  selectedChatId,
}: ChatSidebarProps) {
  const [chats, setChats] = useState<Chat[]>([]);

  const fetchChats = async () => {
    try {
      const response = await fetch(
        "http://localhost:5000/api/assistant/chat/list"
      );
      if (!response.ok) throw new Error("Error al cargar los chats");
      const data = await response.json();
      setChats(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  // Manejar la eliminación de chat
  const handleDeleteChat = async (chatId: number) => {
    try {
      await onDeleteChat(chatId);
      // Actualizar la lista de chats después de eliminar
      await fetchChats();
    } catch (error) {
      console.error("Error:", error);
    }
  };

  useEffect(() => {
    fetchChats();
  }, [selectedChatId]); // Actualizar cuando cambie el chat seleccionado

  return (
    <>
      {/* Overlay */}
      <div
        className={cn("fixed inset-0 z-40", isOpen ? "block" : "hidden")}
        onClick={onClose}
      />
      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[400px] flex-col bg-background/80 backdrop-blur-md backdrop-saturate-150 transition-transform duration-300 ease-in-out supports-[backdrop-filter]:bg-background/60",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between px-4 backdrop-blur-sm">
          <h2 className="text-lg font-semibold">Mis Conversaciones</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="opacity-70 hover:opacity-100 rounded-full"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Cerrar</span>
          </Button>
        </div>
        <ScrollArea className="flex-1">
          <div className="space-y-1.5 p-3">
            {chats.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">
                No hay conversaciones
              </p>
            ) : (
              chats.map((chat) => (
                <div
                  key={chat.id}
                  className={cn(
                    "group flex flex-col space-y-1 rounded-md p-2 hover:bg-accent/30 transition-colors cursor-pointer backdrop-blur-sm",
                    selectedChatId === chat.id && "bg-accent/40"
                  )}
                  onClick={() => onSelectChat(chat.id)}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-sm font-medium line-clamp-1 flex-1 px-1">
                      {chat.title}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-70 hover:opacity-100 transition-opacity"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      <span className="sr-only">Eliminar chat</span>
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground/80 line-clamp-1 px-1">
                    {chat.description}
                  </p>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </>
  );
}
