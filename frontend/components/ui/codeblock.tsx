"use client";

import { useEffect, useRef } from "react";
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
  const codeElement = useRef<HTMLElement>(null);

  useEffect(() => {
    if (codeElement.current) {
      Prism.highlightElement(codeElement.current);
    }
  }, [children, language]);

  return (
    <pre className="rounded-md bg-gray-800 p-4">
      <code ref={codeElement} className={`language-${language}`}>
        {children}
      </code>
    </pre>
  );
}
