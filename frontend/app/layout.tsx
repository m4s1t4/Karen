"use client";

import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { ChatSidebar } from "@/components/chat-sidebar";
import { useState } from "react";
import { ChatProvider, useChat } from "@/contexts/chat-context";
import { cn } from "@/lib/utils";
import { TooltipProvider } from "@/components/ui/tooltip";

function LayoutContent({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { currentChatId, setCurrentChat, startNewChat } = useChat();

  const handleNewChat = () => {
    startNewChat();
    setIsSidebarOpen(false);
  };

  const handleSelectChat = (chatId: number) => {
    setCurrentChat(chatId);
    setIsSidebarOpen(false);
  };

  const handleDeleteChat = async (chatId: number) => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/assistant/chat/delete/${chatId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Error al eliminar el chat");
      }

      if (chatId === currentChatId) {
        startNewChat();
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="flex h-screen flex-col">
      <Navbar
        onToggleSidebar={() => setIsSidebarOpen(true)}
        onNewChat={handleNewChat}
      />
      <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        selectedChatId={currentChatId}
      />
      <main
        className={cn(
          "flex-col flex-grow overflow-hidden transition-[padding] duration-300",
          isSidebarOpen && "pl-[300px]"
        )}
      >
        {children}
      </main>
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <TooltipProvider>
            <ChatProvider>
              <LayoutContent>{children}</LayoutContent>
            </ChatProvider>
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
