"use client";

import { useEffect } from "react";
import Prism from "prismjs";
import "prismjs/themes/prism-tomorrow.css";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-jsx";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-tsx";
import "prismjs/components/prism-css";
import "prismjs/components/prism-python";

interface CodeProps {
  children: string;
  language: string;
}

export function Code({ children, language }: CodeProps) {
  useEffect(() => {
    Prism.highlightAll();
  }, []);

  return (
    <pre className="rounded-md bg-gray-800 p-4">
      <code className={`language-${language}`}>{children}</code>
    </pre>
  );
}
