import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Clock, CheckCircle, File, User, SpinnerGap, ArrowCircleDown } from "@phosphor-icons/react";

export default function LoadFlowTab({ projectId }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, [projectId]);

  const fetchLogs = async () => {
    try {
      const res = await axios.get(`${API}/google-drive/logs/${projectId}`);
      setLogs(res.data.logs);
    } catch (e) {
      console.error("Error fetching sync logs:", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <SpinnerGap className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-muted/20 rounded-3xl border border-dashed border-border">
        <Clock className="w-12 h-12 text-muted-foreground/30 mb-4" />
        <h3 className="text-lg font-bold text-muted-foreground">Sin actividad reciente</h3>
        <p className="text-sm text-muted-foreground/60">Conecta Google Drive para ver el flujo de carga.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold flex items-center gap-3">
          <ArrowCircleDown weight="fill" className="text-primary" />
          Historial de Sincronización
        </h2>
        <button onClick={fetchLogs} className="text-xs text-primary hover:underline font-medium">Actualizar</button>
      </div>

      <div className="space-y-4">
        {logs.map((log) => (
          <div key={log.id} className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm hover:border-primary/20 transition-all">
            <div className="p-4 bg-muted/30 flex items-center justify-between border-b border-border">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/10 rounded-lg">
                  <CheckCircle weight="fill" className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <div className="text-sm font-bold capitalize">Sincronización Exitosa</div>
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">
                    {new Date(log.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 bg-white border border-border rounded-full text-xs font-medium">
                <User weight="bold" className="w-3 h-3 text-primary" />
                {log.user_id}
              </div>
            </div>
            
            <div className="p-4">
              <div className="text-xs font-bold text-muted-foreground mb-3 flex items-center gap-2">
                <File weight="bold" /> ARCHIVOS CARGADOS ({log.files_synced.length})
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {log.files_synced.map((file, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-muted/50 rounded-xl border border-border/50 text-[11px] font-medium truncate">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                    {file}
                  </div>
                ))}
              </div>
              
              {log.files_synced.some(f => f.toLowerCase().endswith('.dxf')) && (
                <div className="mt-4 p-3 bg-primary/5 border border-primary/10 rounded-xl flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary font-bold text-xs">DXF</div>
                  <div className="flex-1">
                    <div className="text-xs font-bold text-primary">Procesamiento Especializado</div>
                    <p className="text-[10px] text-muted-foreground">Se detectaron planos CAD. Aplicando estándares de Luis (EOSIS_Luis_COTAS_EDGE).</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
