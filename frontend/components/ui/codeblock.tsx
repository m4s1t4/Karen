'use client'

import { cn } from "@/lib/utils"

interface CodeBlockProps {
  language: string
  value: string
}

export function CodeBlock({
  language,
  value,
  ...props
}: CodeBlockProps) {
  return (
    <pre
      className={cn(
        "bg-zinc-800/50 rounded p-2 overflow-x-auto",
        language && "language-" + language
      )}
      {...props}
    >
      <code className={cn("text-sm", language && "language-" + language)}>
        {value}
      </code>
    </pre>
  )
}
