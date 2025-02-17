"use client";
import { MemoizedReactMarkdown } from "@/components/ui/markdown";
import rehypeExternalLinks from "rehype-external-links";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { Code } from "@/components/ui/codeblock";

export function BotMessage({ content }: { content: string }) {
  const containsLaTeX = /\\\[([\s\S]*?)\\\]|\\$$([\s\S]*?)\\$$/.test(
    content || "",
  );

  // Check if the content is HTML
  const isHTML =
    content.trim().startsWith("<!DOCTYPE html>") ||
    content.trim().startsWith("<html");

  // If it's HTML, wrap it in a code block
  const processedContent = isHTML ? "```html\n" + content + "\n```" : content;

  const processedData = preprocessLaTeX(processedContent || "");

  return (
    <div className="max-w-3xl mx-auto">
      <div className="px-4 py-6">
        <MemoizedReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[
            [rehypeExternalLinks, { target: "_blank" }],
            rehypeKatex,
          ]}
          components={{
            h1: ({ node, ...props }) => (
              <h1
                className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-6"
                {...props}
              />
            ),
            h2: ({ node, ...props }) => (
              <h2
                className="text-xl font-semibold text-neutral-800 dark:text-neutral-200 mb-4"
                {...props}
              />
            ),
            h3: ({ node, ...props }) => (
              <h3
                className="text-lg font-medium text-neutral-800 dark:text-neutral-200 mb-2"
                {...props}
              />
            ),
            // p: ({ children }) => {
            //   return (
            //     <p className="text-base text-neutral-700 dark:text-neutral-300 leading-relaxed mb-4 ml-4">
            //       {children}
            //     </p>
            //   );
            // },
            p: ({ node, children, ...props }) => {
              // Revisamos si en el array de hijos hay un "code" o "pre"
              const hasBlockElement =
                Array.isArray(node.children) &&
                node.children.some(
                  (child: any) =>
                    child.tagName === "pre" || child.tagName === "code",
                );

              // Si detecta un bloque de código, no envuelvas en <p>
              if (hasBlockElement) {
                return <>{children}</>;
              }

              return (
                <p
                  className="text-base text-neutral-700 dark:text-neutral-300 leading-relaxed mb-4 ml-4"
                  {...props}
                >
                  {children}
                </p>
              );
            },

            code({ node, inline, className, children, ...props }) {
              const content = Array.isArray(children)
                ? children.join("")
                : children;

              if (content === "▍") {
                return (
                  <span className="mt-1 cursor-default animate-pulse">▍</span>
                );
              }

              const processedContent = content.replace("`▍`", "▍");
              const match = /language-(\w+)/.exec(className || "");

              if (inline) {
                return (
                  <code className={className} {...props}>
                    {processedContent}
                  </code>
                );
              }

              return (
                <div className="mb-4">
                  <Code language={(match && match[1]) || ""}>
                    {processedContent.replace(/\n$/, "")}
                  </Code>
                </div>
              );
            },
            strong: ({ node, ...props }) => (
              <strong
                className="font-semibold text-neutral-900 dark:text-neutral-100"
                {...props}
              />
            ),
            ul: ({ node, ...props }) => (
              <ul className="list-disc ml-6 mb-4 space-y-2" {...props} />
            ),
            ol: ({ node, ...props }) => (
              <ol className="list-decimal ml-6 mb-4 space-y-2" {...props} />
            ),
            li: ({ node, ...props }) => (
              <li
                className="text-neutral-700 dark:text-neutral-300"
                {...props}
              />
            ),
            blockquote: ({ node, ...props }) => (
              <blockquote
                className="border-l-4 border-neutral-200 dark:border-neutral-700 pl-4 my-4 text-neutral-600 dark:text-neutral-400 italic"
                {...props}
              />
            ),
          }}
        >
          {processedData}
        </MemoizedReactMarkdown>
      </div>
    </div>
  );
}

// Preprocess LaTeX equations to be rendered by KaTeX
const preprocessLaTeX = (content: string) => {
  const blockProcessedContent = content.replace(
    /\\\[([\s\S]*?)\\\]/g,
    (_, equation) => `$$${equation}$$`,
  );
  const inlineProcessedContent = blockProcessedContent.replace(
    /\\$$([\s\S]*?)\\$$/g,
    (_, equation) => `$${equation}$`,
  );
  return inlineProcessedContent;
};
