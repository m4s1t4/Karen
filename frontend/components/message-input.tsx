import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { AutoResizeTextarea } from "@/components/autoresize-textarea";
import { ArrowUpIcon, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { FileUploadButton } from "./file-upload-button";

interface MessageInputProps {
  input: string;
  isLoading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onChange: (value: string) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  disabled?: boolean;
}

export function MessageInput({
  input,
  isLoading,
  onSubmit,
  onChange,
  onKeyDown,
  disabled,
}: MessageInputProps) {
  return (
    <form
      onSubmit={onSubmit}
      className="relative flex items-center gap-2 rounded-[16px] border px-2 py-1.5 text-sm backdrop-blur-md backdrop-filter"
    >
      <div className="flex-shrink-0">
        <FileUploadButton disabled={isLoading} />
      </div>
      <div className="flex-1 min-w-0">
        <AutoResizeTextarea
          onKeyDown={onKeyDown}
          onChange={(v) => onChange(v)}
          value={input}
          placeholder="Escribe un mensaje..."
          className="w-full placeholder:text-muted-foreground bg-transparent focus:outline-none resize-none"
          disabled={isLoading || disabled}
        />
      </div>
      <div className="flex-shrink-0">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="submit"
              variant="ghost"
              size="sm"
              className={cn(
                "size-6 rounded-full transition-transform",
                isLoading && "rotate-180"
              )}
              disabled={isLoading || disabled || !input.trim()}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUpIcon size={16} />
              )}
              <span className="sr-only">
                {isLoading ? "Enviando..." : "Enviar mensaje"}
              </span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top" align="end">
            {isLoading ? "Enviando..." : "Enviar mensaje (Enter)"}
          </TooltipContent>
        </Tooltip>
      </div>
    </form>
  );
}
