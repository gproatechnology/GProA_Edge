import { useState, useEffect, useRef } from "react";
import { SpinnerGap, CheckCircle, WarningCircle, Lightning, X } from "@phosphor-icons/react";

export default function BatchProgressModal({ isOpen, onClose, jobId, projectId, api, onComplete }) {
  const [status, setStatus] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!isOpen || !jobId) return;

    const poll = async () => {
      try {
        const res = await fetch(`${api}/projects/${projectId}/process-status/${jobId}`);
        const data = await res.json();
        setStatus(data);
        if (data.status === "completed" || data.status === "error") {
          clearInterval(intervalRef.current);
          if (data.status === "completed" && onComplete) {
            setTimeout(() => onComplete(), 1500);
          }
        }
      } catch (e) {
        console.error("Error polling status:", e);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isOpen, jobId, projectId, api, onComplete]);

  if (!isOpen) return null;

  const percent = status?.percent || 0;
  const isCompleted = status?.status === "completed";
  const isError = status?.status === "error";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-md" data-testid="batch-progress-modal">
      <div className="bg-card border border-border rounded-2xl shadow-2xl w-[560px] max-w-[95vw] animate-fadeIn overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-border bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-glow">
              <Lightning weight="fill" className="text-primary-foreground w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-foreground leading-none">
                {isCompleted ? "Procesamiento Completado" : isError ? "Error en Procesamiento" : "Procesando Proyecto EDGE"}
              </h3>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1.5 font-bold">Diagnóstico en Tiempo Real</p>
            </div>
          </div>
          {(isCompleted || isError) && (
            <button 
              onClick={onClose} 
              className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition-all" 
              data-testid="close-progress-modal"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="px-8 py-6 space-y-6">
          {/* Progress bar */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Progreso de Extracción</span>
              <span className="font-mono text-lg font-bold text-primary" data-testid="progress-percent">{percent}%</span>
            </div>
            <div className="w-full h-4 bg-muted rounded-full overflow-hidden border border-border">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out shadow-glow ${isCompleted ? "bg-emerald-500" : isError ? "bg-destructive" : "bg-primary"}`}
                style={{ width: `${percent}%` }}
                data-testid="batch-progress-bar"
              />
            </div>
          </div>

          {/* Current status info */}
          <div className="bg-muted/50 border border-border rounded-2xl p-5 relative overflow-hidden">
             {!isCompleted && !isError && (
               <div className="absolute top-0 left-0 h-1 bg-primary/20 w-full overflow-hidden">
                 <div className="h-full bg-primary animate-pulse w-full" />
               </div>
             )}
            <div className="flex items-start gap-4">
              <div className="mt-1">
                {isCompleted ? (
                  <CheckCircle weight="fill" className="w-6 h-6 text-emerald-500" />
                ) : isError ? (
                  <WarningCircle weight="fill" className="w-6 h-6 text-destructive" />
                ) : (
                  <SpinnerGap className="w-6 h-6 text-primary animate-spin" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-bold text-foreground truncate" data-testid="current-step">
                  {status?.current_step || "Iniciando análisis de documentos..."}
                </p>
                {status?.current_file && (
                  <div className="flex items-center gap-2 mt-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary/40" />
                    <p className="text-xs text-muted-foreground truncate italic" data-testid="current-file">
                      {status.current_file}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="stat-card p-4 flex flex-col items-center">
              <p className="text-[9px] uppercase tracking-widest font-bold text-muted-foreground mb-1">Total</p>
              <p className="font-mono text-xl font-bold">{status?.total || 0}</p>
            </div>
            <div className="stat-card p-4 flex flex-col items-center border-emerald-500/10">
              <p className="text-[9px] uppercase tracking-widest font-bold text-emerald-500/70 mb-1">Éxito</p>
              <p className="font-mono text-xl font-bold text-emerald-500">{status?.processed || 0}</p>
            </div>
            <div className="stat-card p-4 flex flex-col items-center border-destructive/10">
              <p className="text-[9px] uppercase tracking-widest font-bold text-destructive/70 mb-1">Pendiente</p>
              <p className="font-mono text-xl font-bold text-destructive">
                {(status?.total || 0) - (status?.processed || 0)}
              </p>
            </div>
          </div>

          {/* Results list (completed) */}
          {isCompleted && status?.results?.length > 0 && (
            <div className="max-h-40 overflow-y-auto pr-2 space-y-2 custom-scrollbar">
              <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground ml-1 mb-2">Resumen de Archivos</p>
              {status.results.map((r, i) => (
                <div key={i} className="flex items-center gap-3 py-2.5 px-4 rounded-xl bg-muted/40 border border-border group hover:bg-muted/60 transition-colors">
                  {r.status === "processed" ? (
                    <CheckCircle weight="fill" className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                  ) : (
                    <WarningCircle weight="fill" className="w-4 h-4 text-destructive flex-shrink-0" />
                  )}
                  <span className="truncate text-xs font-medium flex-1">{r.filename}</span>
                  {r.measure && (
                    <span className="px-2 py-0.5 bg-primary/10 text-primary rounded-md font-mono text-[9px] font-bold">
                      {r.measure}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-8 py-5 border-t border-border flex justify-end bg-muted/20">
          {(isCompleted || isError) ? (
            <button
              onClick={onClose}
              className="px-6 py-2.5 text-sm bg-primary text-primary-foreground font-bold rounded-xl hover:shadow-glow transition-all active:scale-95"
              data-testid="close-progress-button"
            >
              {isCompleted ? "Ver Resultados" : "Cerrar Panel"}
            </button>
          ) : (
             <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-muted-foreground animate-pulse-slow">
               No cierres esta ventana mientras se procesa...
             </p>
          )}
        </div>
      </div>
    </div>
  );
}
