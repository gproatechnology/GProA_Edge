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
  ArrowRight,
  Gauge,
} from "@phosphor-icons/react";

const CATEGORY_CONFIG = {
  ENERGY: { icon: Lightning, bgColor: "bg-sky-500/10", borderColor: "border-sky-500/20", textColor: "text-sky-500", iconColor: "text-sky-500", label: "Energia" },
  WATER: { icon: Drop, bgColor: "bg-blue-500/10", borderColor: "border-blue-500/20", textColor: "text-blue-500", iconColor: "text-blue-500", label: "Agua" },
  MATERIALS: { icon: Cube, bgColor: "bg-amber-500/10", borderColor: "border-amber-500/20", textColor: "text-amber-500", iconColor: "text-amber-500", label: "Materiales" },
  DESIGN: { icon: PencilRuler, bgColor: "bg-emerald-500/10", borderColor: "border-emerald-500/20", textColor: "text-emerald-500", iconColor: "text-emerald-500", label: "Diseno" },
};

export default function EdgeComplianceTab({ projectId, refreshKey }) {
  const [validation, setValidation] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [wbsRes, kpisRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}/wbs-validation`),
        axios.get(`${API}/projects/${projectId}/kpis`),
      ]);
      setValidation(wbsRes.data);
      setKpis(kpisRes.data);
    } catch (e) {
      console.error("Error fetching compliance data:", e);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData, refreshKey]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20" data-testid="compliance-loading">
        <SpinnerGap className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const measures = validation?.measures || {};
  const processedFilesCount = validation?.processed_files || 0;
  const hasData = Object.keys(measures).length > 0 || processedFilesCount > 0;

  if (!validation || !hasData) {
    return (
      <div className="bg-card border border-border rounded-xl p-20 text-center shadow-sm" data-testid="compliance-empty">
        <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4 text-muted-foreground">
          <Gauge className="w-8 h-8" />
        </div>
        <p className="text-sm font-bold">Sin datos de compliance</p>
        <p className="text-xs text-muted-foreground mt-1 max-w-[280px] mx-auto">
          Procesa archivos con el botón <strong className="text-primary">"Procesar Proyecto EDGE"</strong> para ver el estado de cumplimiento
        </p>
      </div>
    );
  }

  const coverage = validation.coverage;
  const sortedMeasures = Object.entries(measures).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div data-testid="edge-compliance-tab" className="space-y-6">
      {/* Coverage overview */}
      <div className="stat-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Cobertura del Proyecto
          </h3>
          <span className="font-mono text-3xl font-bold text-primary" data-testid="coverage-percent">
            {coverage.coverage_percent}%
          </span>
        </div>
        <div className="w-full h-3 bg-muted rounded-full overflow-hidden mb-6">
          <div
            className="h-full bg-primary rounded-full transition-all duration-1000 shadow-[0_0_12px_rgba(var(--primary),0.3)]"
            style={{ width: `${coverage.coverage_percent}%` }}
          />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
            const catData = coverage.categories[key] || { total: 0, detected: 0 };
            const Icon = config.icon;
            return (
              <div key={key} className={`p-4 rounded-xl border ${config.borderColor} ${config.bgColor} transition-transform hover:scale-[1.02] shadow-sm`} data-testid={`coverage-${key.toLowerCase()}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Icon weight="fill" className={`w-4 h-4 ${config.iconColor}`} />
                  <span className={`text-[10px] uppercase tracking-widest font-bold ${config.textColor}`}>{config.label}</span>
                </div>
                <p className={`font-mono text-2xl font-bold ${config.textColor}`}>
                  {catData.detected}<span className="text-xs opacity-60 mx-0.5">/</span>{catData.total}
                </p>
                <p className="text-[10px] text-muted-foreground font-medium mt-1">medidas detectadas</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* KPIs */}
      {kpis && Object.keys(kpis).length > 0 && (
        <div className="animate-fadeIn" style={{ animationDelay: '200ms' }}>
          <h3 className="text-sm font-bold mb-4" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Métricas de Desempeño (KPIs)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(kpis).map(([measure, kpi]) => (
              <div key={measure} className="stat-card group hover:border-primary/30" data-testid={`kpi-${measure}`}>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <span className="font-mono text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{measure}</span>
                    <p className="text-sm font-bold">{kpi.nombre}</p>
                  </div>
                  {kpi.cumple !== undefined && (
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${kpi.cumple ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
                      {kpi.cumple ? (
                        <CheckCircle weight="fill" className="w-5 h-5" />
                      ) : (
                        <WarningCircle weight="fill" className="w-5 h-5" />
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className={`font-mono text-3xl font-bold ${kpi.cumple ? 'text-emerald-500' : kpi.cumple === false ? 'text-amber-500' : 'text-foreground'}`}>
                    {typeof kpi.valor === 'number' ? kpi.valor.toLocaleString() : kpi.valor}
                  </span>
                  <span className="text-xs font-bold text-muted-foreground">{kpi.unidad}</span>
                </div>
                {kpi.umbral_edge && (
                  <div className="mt-4 pt-3 border-t border-border flex items-center justify-between">
                    <p className="text-[10px] text-muted-foreground font-medium">
                      Umbral EDGE: <span className="font-bold text-foreground">{kpi.umbral_edge} {kpi.unidad}</span>
                    </p>
                    <span className={`text-[10px] font-bold uppercase ${kpi.cumple ? 'text-emerald-500' : 'text-amber-500'}`}>
                      {kpi.cumple ? "Cumple" : "No cumple"}
                    </span>
                  </div>
                )}
                {kpi.alertas && kpi.alertas.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {kpi.alertas.slice(0, 3).map((a, i) => (
                      <p key={i} className="text-[10px] text-amber-500 flex items-center gap-1.5 font-medium">
                        <WarningCircle weight="fill" className="w-3 h-3 flex-shrink-0" />
                        {a}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* WBS Compliance Table */}
      <div className="animate-fadeIn" style={{ animationDelay: '400ms' }}>
        <h3 className="text-sm font-bold mb-4" style={{ fontFamily: "'Outfit', sans-serif" }}>
          Checklist de Cumplimiento EDGE
        </h3>
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <table className="w-full data-table" data-testid="wbs-compliance-table">
            <thead>
              <tr className="bg-muted/50 border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Medida</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Nombre</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Progreso</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Documentación</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {sortedMeasures.map(([measure, data]) => {
                return (
                  <tr key={measure} className="hover:bg-muted/30 transition-colors" data-testid={`wbs-row-${measure}`}>
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs font-bold text-primary">{measure}</span>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-xs font-medium">{data.nombre}</p>
                      <span className="text-[9px] text-muted-foreground uppercase tracking-wider font-bold">{data.categoria}</span>
                    </td>
                    <td className="px-4 py-3">
                      {data.estado === "completo" ? (
                        <div className="flex items-center gap-1.5 text-emerald-500 font-bold text-[10px] uppercase tracking-wider">
                          <CheckCircle weight="fill" className="w-3.5 h-3.5" /> Completo
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-amber-500 font-bold text-[10px] uppercase tracking-wider">
                          <WarningCircle weight="fill" className="w-3.5 h-3.5" /> Incompleto
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${data.progreso >= 1 ? 'bg-emerald-500' : data.progreso >= 0.5 ? 'bg-amber-400' : 'bg-red-400'}`}
                            style={{ width: `${(data.progreso || 0) * 100}%` }}
                          />
                        </div>
                        <span className="font-mono text-[10px] font-bold">{Math.round((data.progreso || 0) * 100)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(data.documentos_disponibles || []).map((d, i) => (
                          <span key={i} className="text-[9px] px-1.5 py-0.5 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded-md font-bold uppercase tracking-tighter">{d.replace("_", " ")}</span>
                        ))}
                        {(data.faltantes || []).map((d, i) => (
                          <span key={i} className="text-[9px] px-1.5 py-0.5 bg-destructive/10 text-destructive border border-destructive/20 rounded-md font-bold uppercase tracking-tighter">{d.replace("_", " ")}</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alerts summary */}
      {sortedMeasures.some(([, d]) => d.estado === "incompleto") && (
        <div className="bg-amber-500/10 border-l-4 border-amber-500 p-5 rounded-r-xl animate-fadeIn" data-testid="compliance-alerts">
          <h3 className="text-sm font-bold text-amber-500 mb-4 flex items-center gap-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
            <WarningCircle weight="fill" className="w-5 h-5" />
            Alertas de Documentación Faltante
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {sortedMeasures
              .filter(([, d]) => d.estado === "incompleto")
              .map(([measure, data]) => (
                <div key={measure} className="flex items-start gap-3 p-2 rounded-lg bg-amber-500/5 hover:bg-amber-500/10 transition-colors border border-amber-500/10">
                  <span className="font-mono text-xs font-bold text-amber-500 mt-0.5">{measure}</span>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-amber-600/80 mb-1">{data.nombre}</p>
                    <p className="text-[10px] text-amber-600/60 leading-relaxed font-medium">
                      Falta: {data.faltantes.map(f => f.replace("_", " ")).join(", ")}
                    </p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
