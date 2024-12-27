import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Loader2, Paperclip } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { useChat } from "@/contexts/chat-context";

interface FileUploadButtonProps {
  onUploadComplete?: () => void;
  disabled?: boolean;
}

type ProcessingStage =
  | "uploading"
  | "loading"
  | "splitting"
  | "processing"
  | "storing"
  | "complete";

export function FileUploadButton({
  onUploadComplete,
  disabled,
}: FileUploadButtonProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [stage, setStage] = useState<ProcessingStage>("uploading");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const { currentChatId, setCurrentChat } = useChat();

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const getStageMessage = (stage: ProcessingStage, progress: number) => {
    switch (stage) {
      case "uploading":
        return "Subiendo archivo...";
      case "loading":
        return "Cargando documento...";
      case "splitting":
        return "Dividiendo documento...";
      case "processing":
        return "Procesando chunks...";
      case "storing":
        return "Almacenando en base de datos...";
      case "complete":
        return "¡Proceso completado!";
      default:
        return `Procesando... ${progress}%`;
    }
  };

  const simulateProgress = () => {
    // Tiempos aproximados basados en los logs:
    // - Carga: ~35s (0-20%)
    // - División: ~1s (20-25%)
    // - Procesamiento: ~15s (25-60%)
    // - Almacenamiento: ~45s (60-100%)

    setUploadProgress(0);
    setStage("loading");

    const stages: Array<[ProcessingStage, number]> = [
      ["loading", 35], // 35 segundos
      ["splitting", 1], // 1 segundo
      ["processing", 15], // 15 segundos
      ["storing", 45], // 45 segundos
    ];

    let currentStageIndex = 0;
    let elapsedTime = 0;

    const interval = setInterval(() => {
      const [currentStage, duration] = stages[currentStageIndex];

      setStage(currentStage);
      elapsedTime += 1;

      // Calcular progreso total basado en el tiempo transcurrido
      const totalDuration = stages.reduce((acc, [, dur]) => acc + dur, 0);
      const progress = Math.min(
        Math.round((elapsedTime / totalDuration) * 100),
        95
      );
      setUploadProgress(progress);

      // Cambiar a la siguiente etapa si el tiempo transcurrido supera la duración
      if (elapsedTime >= duration && currentStageIndex < stages.length - 1) {
        currentStageIndex++;
        elapsedTime = 0;
      }

      // Detener si llegamos al 95%
      if (progress >= 95) {
        clearInterval(interval);
      }
    }, 1000);

    return interval;
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Verificar si es un archivo PDF
    if (
      !file.name.toLowerCase().endsWith(".pdf") ||
      file.type !== "application/pdf"
    ) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Solo se permiten archivos PDF",
      });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    try {
      setIsUploading(true);
      setStage("uploading");
      const progressInterval = simulateProgress();

      const formData = new FormData();
      formData.append("file", file);
      if (currentChatId) {
        formData.append("chat_id", currentChatId.toString());
      }

      const response = await fetch(
        "http://localhost:5000/api/assistant/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Error al procesar el archivo");
      }

      const data = await response.json();
      clearInterval(progressInterval);
      setUploadProgress(100);
      setStage("complete");

      // Si se creó un nuevo chat, actualizar el ID
      if (data.chat_id && !currentChatId) {
        setCurrentChat(data.chat_id);
      }

      toast({
        title: "¡Archivo subido!",
        description: "El archivo PDF ha sido procesado y está listo para usar",
        variant: "success",
        duration: 3000,
        className: "bg-green-50 border-green-200",
      });

      // Esperar un momento antes de resetear el progreso
      setTimeout(() => {
        setUploadProgress(0);
        setIsUploading(false);
        setStage("uploading");
      }, 1000);

      onUploadComplete?.();
    } catch (error) {
      setUploadProgress(0);
      setIsUploading(false);
      setStage("uploading");
      toast({
        variant: "destructive",
        title: "Error",
        description:
          error instanceof Error ? error.message : "Error al subir el archivo",
      });
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="relative">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
        accept=".pdf,application/pdf"
      />
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="size-9 rounded-full p-0 relative"
            onClick={handleFileButtonClick}
            disabled={disabled || isUploading}
          >
            {isUploading ? (
              <div className="relative flex items-center justify-center">
                <Loader2
                  className="animate-spin transition-all duration-1000 ease-in-out"
                  style={{
                    width: `${Math.max(20, (uploadProgress / 100) * 20 + 2)}px`,
                    height: `${Math.max(
                      20,
                      (uploadProgress / 100) * 20 + 2
                    )}px`,
                  }}
                />
              </div>
            ) : (
              <Paperclip className="h-5 w-5" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent
          side="top"
          align="start"
          className="max-w-[200px] text-xs"
        >
          {isUploading
            ? getStageMessage(stage, uploadProgress)
            : "Subir archivo PDF"}
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
