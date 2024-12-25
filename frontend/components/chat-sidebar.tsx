"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface Chat {
  id: number;
  created_at: string;
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
        className={cn(
          "fixed inset-0 z-40 bg-background/80 backdrop-blur-sm",
          isOpen ? "block" : "hidden"
        )}
        onClick={onClose}
      />
      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[300px] flex-col border-r bg-background transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b px-6">
          <h2 className="text-lg font-semibold">Mis Conversaciones</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
            <span className="sr-only">Cerrar</span>
          </Button>
        </div>
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-2 py-4">
            {chats.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">
                No hay conversaciones
              </p>
            ) : (
              chats.map((chat) => (
                <div
                  key={chat.id}
                  className={cn(
                    "flex items-center justify-between p-2 rounded-lg hover:bg-accent",
                    selectedChatId === chat.id && "bg-accent"
                  )}
                >
                  <Button
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => onSelectChat(chat.id)}
                  >
                    {`Chat ${chat.id}`}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteChat(chat.id);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                    <span className="sr-only">Eliminar chat</span>
                  </Button>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </>
  );
}
