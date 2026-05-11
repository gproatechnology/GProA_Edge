import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import {
  Lightning,
  Drop,
  Cube,
  PencilRuler,
  CheckCircle,
  WarningCircle,
  SpinnerGap,
} from "@phosphor-icons/react";

const CATEGORY_CONFIG = {
  ENERGY: { icon: Lightning, color: "sky", label: "Energia" },
  WATER: { icon: Drop, color: "blue", label: "Agua" },
  MATERIALS: { icon: Cube, color: "amber", label: "Materiales" },
  DESIGN: { icon: PencilRuler, color: "emerald", label: "Diseno" },
};

export default function EdgeStatusTab({ projectId }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/projects/${projectId}/edge-status`);
      setStatus(res.data);
    } catch (e) {
      console.error("Error fetching edge status:", e);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20" data-testid="edge-status-loading">
        <SpinnerGap className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (!status || status.total_files === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-20 text-center shadow-sm" data-testid="edge-status-empty">
        <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4 text-muted-foreground">
          <Lightning className="w-8 h-8" />
        </div>
        <p className="text-sm font-bold">Sin datos de estado EDGE</p>
        <p className="text-xs text-muted-foreground mt-1">
          Procesa archivos para ver el estado de certificación
        </p>
      </div>
    );
  }

  const progressPercent = status.total_files > 0
    ? Math.round((status.processed_files / status.total_files) * 100)
    : 0;

  return (
    <div data-testid="edge-status-tab" className="space-y-6">
      {/* Progress & Savings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Progress */}
        <div className="stat-card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">
              Progreso General de Procesamiento
            </p>
            <span className="font-mono text-2xl font-bold text-primary">{progressPercent}%</span>
          </div>
          <div className="w-full h-3 bg-muted rounded-full overflow-hidden mb-4 border border-border">
            <div
              className="h-full bg-primary rounded-full transition-all duration-1000 shadow-glow"
              style={{ width: `${progressPercent}%` }}
              data-testid="progress-bar"
            />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              <span className="font-bold text-foreground">{status.processed_files}</span> de{" "}
              <span className="font-bold text-foreground">{status.total_files}</span> archivos completados
            </p>
            <div className="flex items-center gap-1.5">
               <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
               <span className="text-[10px] font-bold uppercase tracking-tighter opacity-60">En tiempo real</span>
            </div>
          </div>
        </div>

        {/* Savings Indicators */}
        <div className="stat-card">
          <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground mb-4">
            Ahorro Estimado EDGE
          </p>
          <div className="space-y-4">
            {[
              { id: 'energy', label: 'Energia', val: status.savings?.energy || 0, color: 'text-sky-500', bg: 'bg-sky-500/20' },
              { id: 'water', label: 'Agua', val: status.savings?.water || 0, color: 'text-blue-500', bg: 'bg-blue-500/20' },
              { id: 'materials', label: 'Materiales', val: status.savings?.materials || 0, color: 'text-amber-500', bg: 'bg-amber-500/20' },
            ].map(s => (
              <div key={s.id} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase">{s.label}</span>
                  <span className={`text-xs font-bold ${s.color}`}>{s.val}%</span>
                </div>
                <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${s.bg.replace('/20', '')} transition-all duration-1000`} 
                    style={{ width: `${s.val}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="text-[9px] text-muted-foreground mt-4 italic text-center">Datos proyectados según WBS actual</p>
        </div>
      </div>

      {/* Category Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
          const count = status.categories[key] || 0;
          const Icon = config.icon;
          const colorClass = key === 'ENERGY' ? 'text-sky-500' : key === 'WATER' ? 'text-blue-500' : key === 'MATERIALS' ? 'text-amber-500' : 'text-emerald-500';
          const bgClass = key === 'ENERGY' ? 'bg-sky-500/10' : key === 'WATER' ? 'bg-blue-500/10' : key === 'MATERIALS' ? 'bg-amber-500/10' : 'bg-emerald-500/10';
          
          return (
            <div
              key={key}
              className="stat-card hover:border-primary/20 transition-all group"
              data-testid={`category-card-${key.toLowerCase()}`}
            >
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-8 h-8 ${bgClass} ${colorClass} rounded-lg flex items-center justify-center transition-transform group-hover:scale-110`}>
                  <Icon weight="fill" className="w-4 h-4" />
                </div>
                <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">
                  {config.label}
                </p>
              </div>
              <p className="text-3xl font-bold font-mono">{count}</p>
              <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-tighter mt-1">documento{count !== 1 ? "s" : ""}</p>
            </div>
          );
        })}
      </div>

      {/* Measures breakdown */}
      {Object.keys(status.measures).length > 0 && (
        <div className="stat-card">
          <h3 className="text-sm font-bold mb-4" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Medidas EDGE Detectadas
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(status.measures)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([measure, count]) => (
                <div
                  key={measure}
                  className="flex items-center gap-3 px-3 py-2 bg-muted/50 border border-border rounded-xl hover:bg-muted transition-colors"
                  data-testid={`measure-badge-${measure}`}
                >
                  <span className="font-mono text-xs font-bold text-primary">{measure}</span>
                  <span className="w-6 h-6 flex items-center justify-center bg-primary/10 rounded-full text-[10px] font-bold text-primary">
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Missing documents */}
      {status.faltantes && status.faltantes.length > 0 && (
        <div className="bg-amber-500/10 border-l-4 border-amber-500 p-5 rounded-r-xl animate-fadeIn">
          <h3 className="text-sm font-bold text-amber-500 mb-4 flex items-center gap-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
            <WarningCircle weight="fill" className="w-5 h-5" />
            Alertas de Certificación
          </h3>
          <div className="space-y-3">
            {status.faltantes.map((item, idx) => (
              <div
                key={idx}
                className="flex items-start gap-4 p-3 bg-amber-500/5 border border-amber-500/10 rounded-xl"
                data-testid={`faltante-${idx}`}
              >
                <span className="font-mono text-xs font-bold text-amber-500 mt-1 shrink-0">
                  {item.medida}
                </span>
                <div className="flex flex-wrap gap-2">
                  {(item.faltan || []).map((tipo, tidx) => (
                    <span
                      key={tidx}
                      className="text-[9px] px-2 py-0.5 bg-amber-500/20 text-amber-600 rounded-full font-bold uppercase tracking-tight"
                    >
                      {tipo.replace("_", " ")}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Logs */}
      {status.logs && status.logs.length > 0 && (
        <div className="animate-fadeIn" style={{ animationDelay: '600ms' }}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Registro de Procesamiento (System Logs)
            </h3>
            <span className="text-[9px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold uppercase">Consola en Vivo</span>
          </div>
          <div className="bg-[#0f1117] border border-slate-800 rounded-xl p-4 font-mono text-[11px] leading-relaxed shadow-2xl">
            <div className="flex flex-col gap-1.5">
              {status.logs.map((log, i) => {
                const isError = log.includes("ERROR");
                const isWarning = log.includes("WARNING");
                const isInfo = log.includes("INFO");
                const isDemo = log.includes("MODO DEMO");
                
                return (
                  <div key={i} className="flex gap-3 group">
                    <span className="text-slate-600 shrink-0 select-none">[{new Date().toLocaleTimeString()}]</span>
                    <span className={
                      isError ? "text-red-400" : 
                      isWarning ? "text-amber-400" : 
                      isDemo ? "text-purple-400 font-bold" :
                      isInfo ? "text-emerald-400" : 
                      "text-slate-300"
                    }>
                      {log}
                    </span>
                  </div>
                );
              })}
              <div className="flex gap-3 animate-pulse mt-1">
                <span className="text-slate-600">[{new Date().toLocaleTimeString()}]</span>
                <span className="text-primary font-bold">_</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* All complete */}
      {status.faltantes && status.faltantes.length === 0 && status.processed_files > 0 && (
        <div className="stat-card border-l-4 border-l-emerald-500 bg-emerald-500/5 animate-fadeIn">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-emerald-500/20 text-emerald-500 rounded-full flex items-center justify-center">
              <CheckCircle weight="fill" className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-bold">Documentación Completa</p>
              <p className="text-xs text-muted-foreground mt-0.5">Todos los archivos necesarios han sido detectados satisfactoriamente</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
