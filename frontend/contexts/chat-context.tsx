"use client";

import { createContext, useContext, useState } from "react";

interface ChatContextType {
  currentChatId: number | undefined;
  setCurrentChatId: (id: number | undefined) => void;
  isNewChat: boolean;
  startNewChat: () => void;
  setCurrentChat: (id: number) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [currentChatId, setCurrentChatId] = useState<number | undefined>();
  const [isNewChat, setIsNewChat] = useState(true);

  const startNewChat = () => {
    setCurrentChatId(undefined);
    setIsNewChat(true);
  };

  const setCurrentChat = (id: number) => {
    setCurrentChatId(id);
    setIsNewChat(false);
  };

  return (
    <ChatContext.Provider
      value={{
        currentChatId,
        setCurrentChatId,
        isNewChat,
        startNewChat,
        setCurrentChat,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
