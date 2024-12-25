"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/mode-toggle";
import { Menu, Plus } from "lucide-react";

interface NavbarProps {
  onToggleSidebar: () => void;
  onNewChat: () => void;
}

export function Navbar({ onToggleSidebar, onNewChat }: NavbarProps) {
  return (
    <header className="">
      <div className="container mx-auto py-3">
        <nav className="flex items-center justify-between">
          <div className="flex items-center">
            <Button variant="ghost" size="icon" onClick={onToggleSidebar}>
              <Menu className="h-5 w-5" />
              <span className="sr-only">Abrir menú</span>
            </Button>
            <Button variant="default" size="icon" onClick={onNewChat}>
              <Plus className="h-5 w-5" />
              <span className="sr-only">Nuevo chat</span>
            </Button>
          </div>
          <div className="flex items-center">
            <ModeToggle />
          </div>
        </nav>
      </div>
    </header>
  );
}
