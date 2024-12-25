"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/mode-toggle";

export function Navbar() {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-3">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/chat" className="text-xl font-bold">
              Karen
            </Link>
            <div className="hidden md:flex items-center gap-4">
              <Link href="/chat">
                <Button variant="ghost">Chat</Button>
              </Link>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <ModeToggle />
          </div>
        </nav>
      </div>
    </header>
  );
}
