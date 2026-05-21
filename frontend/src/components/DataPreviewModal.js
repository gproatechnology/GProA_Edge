import { X, CheckCircle, FileText, Database, Lightning, Drop, Cube } from "@phosphor-icons/react";

export default function DataPreviewModal({ isOpen, onClose, file }) {
  if (!isOpen || !file) return null;

  const getCategoryIcon = (cat) => {
    switch (cat?.toUpperCase()) {
      case "ENERGY": return <Lightning weight="fill" className="text-sky-500" />;
      case "WATER": return <Drop weight="fill" className="text-blue-500" />;
      case "MATERIALS": return <Cube weight="fill" className="text-amber-500" />;
      default: return <FileText className="text-muted-foreground" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-md animate-fadeIn" onClick={onClose}>
      <div 
        className="bg-card border border-border rounded-3xl shadow-2xl w-[600px] max-w-[95vw] overflow-hidden" 
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-6 border-b border-border bg-muted/30">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary shadow-sm">
              <Database weight="fill" className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground leading-tight">Previsualización de Datos</h3>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1.5 font-bold">Información extraída por IA</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-8 py-8 space-y-8">
          {/* File Info */}
          <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-2xl border border-border">
            <div className="w-10 h-10 bg-background rounded-xl flex items-center justify-center border border-border">
              <FileText className="w-5 h-5 text-muted-foreground" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-foreground truncate">{file.filename}</p>
              <p className="text-[10px] text-muted-foreground font-mono mt-1 uppercase">ID: {file.id.substring(0,8)}...</p>
            </div>
            <div className="flex flex-col items-end">
              <span className="text-[10px] font-bold text-primary uppercase tracking-tighter">Estado</span>
              <div className="flex items-center gap-1 mt-1 text-emerald-500">
                <CheckCircle weight="fill" className="w-4 h-4" />
                <span className="text-xs font-bold uppercase">Procesado</span>
              </div>
            </div>
          </div>

          {/* Data Grid */}
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground ml-1">Categoría EDGE</p>
              <div className="flex items-center gap-3 p-3 bg-card border border-border rounded-xl">
                {getCategoryIcon(file.category_edge)}
                <span className="text-sm font-bold">{file.category_edge || "Sin Clasificar"}</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground ml-1">Medida Detectada</p>
              <div className="flex items-center gap-3 p-3 bg-card border border-border rounded-xl">
                <div className="w-5 h-5 bg-primary/10 rounded flex items-center justify-center text-[10px] font-bold text-primary">ID</div>
                <span className="text-sm font-mono font-bold text-primary">{file.measure_edge || "N/A"}</span>
              </div>
            </div>
          </div>

          {/* Specialized metrics */}
          <div className="space-y-4">
            <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground ml-1">Métricas Extraídas</p>
            <div className="grid grid-cols-1 gap-3">
              {file.consumption_kwh != null && (
                <div className="flex items-center justify-between p-4 bg-muted/30 rounded-2xl border border-border">
                  <span className="text-xs font-medium text-muted-foreground">Consumo Eléctrico</span>
                  <span className="text-sm font-mono font-bold text-foreground">{file.consumption_kwh.toLocaleString()} kWh</span>
                </div>
              )}
              {file.cost != null && (
                <div className="flex items-center justify-between p-4 bg-muted/30 rounded-2xl border border-border">
                  <span className="text-xs font-medium text-muted-foreground">Costo Detectado</span>
                  <span className="text-sm font-mono font-bold text-primary">${file.cost.toLocaleString()}</span>
                </div>
              )}
              {file.watts != null && (
                <div className="flex items-center justify-between p-4 bg-muted/30 rounded-2xl border border-border">
                  <span className="text-xs font-medium text-muted-foreground">Potencia Instalada</span>
                  <span className="text-sm font-mono font-bold text-foreground">{file.watts.toLocaleString()} W</span>
                </div>
              )}
            </div>
          </div>

          {/* Traceability Section */}
          <div className="space-y-4 animate-fadeIn">
            <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground ml-1">Trazabilidad y Origen</p>
            <div className="p-5 bg-primary/5 border border-primary/20 rounded-2xl space-y-4">
              {file.specialized_data?.classification?.drawing_title && (
                <div>
                  <p className="text-[10px] font-bold text-primary/60 uppercase mb-1">Título detectado en Cajetín</p>
                  <p className="text-sm font-bold text-foreground uppercase italic border-l-2 border-primary pl-3">
                    "{file.specialized_data.classification.drawing_title}"
                  </p>
                </div>
              )}
              
              {file.specialized_data?.mensaje && (
                <div>
                  <p className="text-[10px] font-bold text-primary/60 uppercase mb-1">Razonamiento de la IA</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {file.specialized_data.mensaje}
                  </p>
                </div>
              )}

              {file.specialized_data?.tableros?.length > 0 && (
                <div>
                  <p className="text-[10px] font-bold text-primary/60 uppercase mb-2">Fuentes de carga (Tableros)</p>
                  <div className="flex flex-wrap gap-2">
                    {file.specialized_data.tableros.map((t, i) => (
                      <span key={i} className="px-2 py-1 bg-background border border-border rounded-lg text-[10px] font-mono">
                        {t.nombre}: <span className="text-primary font-bold">{t.watts}W</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {!file.specialized_data?.mensaje && !file.specialized_data?.classification?.drawing_title && (
                <p className="text-xs text-muted-foreground italic">No hay datos de trazabilidad adicionales para este documento.</p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-8 py-6 border-t border-border bg-muted/20 flex justify-center">
          <button 
            onClick={onClose}
            className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-2xl hover:shadow-glow transition-all active:scale-[0.98]"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
