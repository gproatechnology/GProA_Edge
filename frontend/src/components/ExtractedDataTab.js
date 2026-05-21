import { useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { DownloadSimple, Table as TableIcon, Lightning, PencilSimple, Check, X } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function ExtractedDataTab({ projectId, files, onRefresh }) {
  const [exporting, setExporting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);

  const processedFiles = files.filter((f) => f.status === "processed");

  const handleExport = async () => {
    setExporting(true);
    toast.info("Generando archivo Excel...");
    try {
      const res = await axios.get(`${API}/projects/${projectId}/export-excel`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `proyecto_EDGE.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Excel exportado con éxito");
    } catch (e) {
      console.error("Error exporting:", e);
      toast.error("Error al exportar el archivo");
    } finally {
      setExporting(false);
    }
  };

  const startEditing = (file) => {
    setEditingId(file.id);
    setEditForm({
      category_edge: file.category_edge,
      measure_edge: file.measure_edge,
      watts: file.watts,
      lumens: file.lumens,
      tipo_equipo: file.tipo_equipo,
      marca: file.marca,
      modelo: file.modelo,
      consumption_kwh: file.consumption_kwh,
      cost: file.cost
    });
  };

  const saveEdit = async (fileId) => {
    setSaving(true);
    try {
      await axios.put(`${API}/files/${fileId}`, editForm);
      setEditingId(null);
      toast.success("Cambios guardados correctamente");
      if (onRefresh) onRefresh(); // Para recargar los datos
    } catch (e) {
      console.error("Error saving edit:", e);
      toast.error("Error al guardar los cambios");
    } finally {
      setSaving(false);
    }
  };

  const categoryBadgeClass = (cat) => {
    switch (cat?.toUpperCase()) {
      case "ENERGY": return "energy";
      case "WATER": return "water";
      case "MATERIALS": return "materials";
      case "DESIGN": return "design";
      default: return "pending";
    }
  };

  if (processedFiles.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-12 text-center" data-testid="extracted-data-empty">
        <TableIcon className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">Sin datos extraidos</p>
        <p className="text-xs text-muted-foreground/60 mt-1">
          Procesa archivos con "Procesar Proyecto EDGE" para ver datos extraidos
        </p>
      </div>
    );
  }

  // Separate EEM22 files for special display
  const eem22Files = processedFiles.filter(
    (f) => (f.measure_edge === "EEM22" || f.measure_edge === "EEM23") && 
           (f.specialized_data?.luminarias?.length > 0 || f.specialized_data?.tableros?.length > 0)
  );

  return (
    <div data-testid="extracted-data-tab">
      {/* Actions */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">
          <span className="font-mono font-medium text-foreground">{processedFiles.length}</span> archivo{processedFiles.length !== 1 ? "s" : ""} procesado{processedFiles.length !== 1 ? "s" : ""}
        </p>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-card text-foreground border border-border rounded-xl hover:bg-muted transition-all shadow-sm disabled:opacity-50"
          data-testid="export-excel"
        >
          <DownloadSimple className="w-4 h-4" />
          {exporting ? "Exportando..." : "Exportar Excel"}
        </button>
      </div>

      {/* Billing Insights Panel */}
      {processedFiles.some(f => f.cost > 0 || f.consumption_kwh > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 animate-fadeIn">
          <div className="bg-primary/5 border border-primary/20 rounded-2xl p-4">
            <p className="text-[10px] uppercase tracking-wider font-bold text-primary mb-1">Gasto Total Detectado</p>
            <p className="text-2xl font-bold text-primary font-mono">
              ${processedFiles.reduce((sum, f) => sum + (f.cost || 0), 0).toLocaleString()}
            </p>
          </div>
          <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-4">
            <p className="text-[10px] uppercase tracking-wider font-bold text-emerald-500 mb-1">Consumo Total</p>
            <p className="text-2xl font-bold text-emerald-600 font-mono">
              {processedFiles.reduce((sum, f) => sum + (f.consumption_kwh || 0), 0).toLocaleString()} <span className="text-xs">kWh</span>
            </p>
          </div>
          <div className="bg-muted/30 border border-border rounded-2xl p-4">
            <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-1">Confianza Media IA</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold text-foreground font-mono">
                {(processedFiles.reduce((sum, f) => sum + (f.confidence || 0), 0) / processedFiles.length * 100).toFixed(0)}%
              </p>
              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-1000" 
                  style={{ width: `${(processedFiles.reduce((sum, f) => sum + (f.confidence || 0), 0) / processedFiles.length * 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* General Data Table */}
      <div className="bg-card border border-border rounded-xl overflow-x-auto mb-6 shadow-sm">
        <table className="w-full data-table" data-testid="extracted-data-table">
          <thead>
            <tr className="bg-muted/50 border-b border-border">
              <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Archivo</th>
              <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Categoria</th>
              <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Medida</th>
              <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Consumo / Costo</th>
              <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Watts / Lumens</th>
              <th className="px-4 py-3 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Confianza</th>
              <th className="px-4 py-3 text-right text-xs font-bold text-muted-foreground uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {processedFiles.map((f) => {
              const isEditing = editingId === f.id;
              return (
                <tr key={f.id} className="hover:bg-muted/30 transition-colors group">
                  <td className="px-4 py-3">
                    <span className="truncate max-w-[180px] block text-sm font-medium">{f.filename}</span>
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <select 
                        value={editForm.category_edge || ""} 
                        onChange={(e) => setEditForm({...editForm, category_edge: e.target.value})}
                        className="bg-background border border-border rounded px-1 text-xs"
                      >
                        <option value="ENERGY">ENERGY</option>
                        <option value="WATER">WATER</option>
                        <option value="MATERIALS">MATERIALS</option>
                      </select>
                    ) : (
                      <span className={`edge-badge ${categoryBadgeClass(f.category_edge)}`}>{f.category_edge}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {isEditing ? (
                      <input 
                        value={editForm.measure_edge || ""} 
                        onChange={(e) => setEditForm({...editForm, measure_edge: e.target.value})}
                        className="bg-background border border-border rounded px-1 w-16"
                      />
                    ) : f.measure_edge || "-"}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <div className="flex flex-col gap-1">
                        <input 
                          type="number"
                          placeholder="kWh"
                          value={editForm.consumption_kwh || ""} 
                          onChange={(e) => setEditForm({...editForm, consumption_kwh: parseFloat(e.target.value)})}
                          className="bg-background border border-border rounded px-1 text-[10px] w-20"
                        />
                        <input 
                          type="number"
                          placeholder="$ Costo"
                          value={editForm.cost || ""} 
                          onChange={(e) => setEditForm({...editForm, cost: parseFloat(e.target.value)})}
                          className="bg-background border border-border rounded px-1 text-[10px] w-20"
                        />
                      </div>
                    ) : (
                      <div className="text-[10px]">
                        {f.consumption_kwh != null && (
                          <div className="font-mono font-medium">{f.consumption_kwh.toLocaleString()} <span className="opacity-50">kWh</span></div>
                        )}
                        {f.cost != null && (
                          <div className="font-mono text-primary">${f.cost.toLocaleString()}</div>
                        )}
                        {f.consumption_kwh == null && f.cost == null && "-"}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-[10px]">
                    {isEditing ? (
                      <div className="flex flex-col gap-1">
                        <input 
                          type="number"
                          placeholder="Watts"
                          value={editForm.watts || ""} 
                          onChange={(e) => setEditForm({...editForm, watts: parseFloat(e.target.value)})}
                          className="bg-background border border-border rounded px-1 w-16"
                        />
                        <input 
                          type="number"
                          placeholder="Lumens"
                          value={editForm.lumens || ""} 
                          onChange={(e) => setEditForm({...editForm, lumens: parseFloat(e.target.value)})}
                          className="bg-background border border-border rounded px-1 w-16"
                        />
                      </div>
                    ) : (
                      <>
                        {f.watts != null && <span>{f.watts}W</span>}
                        {f.lumens != null && <span className="text-muted-foreground ml-1">/ {f.lumens}lm</span>}
                        {f.watts == null && f.lumens == null && "-"}
                      </>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {f.confidence != null ? (
                      <div className="w-full max-w-[100px]">
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className={`text-[10px] font-bold ${f.confidence >= 1.0 ? "text-primary" : f.confidence >= 0.8 ? "text-emerald-500" : "text-amber-500"}`}>
                            {(f.confidence * 100).toFixed(0)}%
                          </span>
                          {f.confidence >= 1.0 && <Check size={10} className="text-primary" />}
                        </div>
                        <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-500 ${f.confidence >= 1.0 ? "bg-primary" : f.confidence >= 0.8 ? "bg-emerald-500" : "bg-amber-500"}`}
                            style={{ width: `${f.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    ) : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {isEditing ? (
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => saveEdit(f.id)}
                          disabled={saving}
                          className="p-1.5 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors"
                        >
                          <Check size={16} weight="bold" />
                        </button>
                        <button 
                          onClick={() => setEditingId(null)}
                          className="p-1.5 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 transition-colors"
                        >
                          <X size={16} weight="bold" />
                        </button>
                      </div>
                    ) : (
                      <button 
                        onClick={() => startEditing(f)}
                        className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/5 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                      >
                        <PencilSimple size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* EEM22 Luminaire Detail */}
      {eem22Files.length > 0 && (
        <div className="mb-6" data-testid="eem22-section">
          <div className="flex items-center gap-2 mb-3">
            <Lightning weight="fill" className="w-4 h-4 text-primary" />
            <h3 className="text-base font-medium text-foreground" style={{ fontFamily: "'Outfit', sans-serif" }}>
              EEM22 — Tabla de Luminarias
            </h3>
          </div>
          {eem22Files.map((f) => {
            const sd = f.specialized_data;
            return (
              <div key={f.id} className="mb-6 animate-fadeIn">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-muted-foreground">Fuente: <span className="font-medium text-foreground">{f.filename}</span></p>
                  {sd.classification?.drawing_title && (
                    <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold uppercase tracking-tighter">
                      {sd.classification.drawing_title}
                    </span>
                  )}
                </div>

                <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
                  {sd.tipo_documento === "diagrama_unifilar" ? (
                    <table className="w-full data-table">
                      <thead>
                        <tr className="bg-muted/50 border-b border-border">
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">Nombre Tablero</th>
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">Descripción / Servicio</th>
                          <th className="px-4 py-2 text-right text-[10px] font-bold text-muted-foreground uppercase">Carga (Watts)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {(sd.tableros || []).map((tab, idx) => (
                          <tr key={idx} className="hover:bg-muted/20 transition-colors">
                            <td className="px-4 py-2 font-mono text-xs font-bold text-primary">{tab.nombre || "-"}</td>
                            <td className="px-4 py-2 text-xs text-muted-foreground">{tab.descripcion || "Tablero de Alumbrado"}</td>
                            <td className="px-4 py-2 text-right font-mono text-xs font-medium">{tab.watts?.toLocaleString() || 0} W</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <table className="w-full data-table" data-testid={`luminaire-table-${f.id}`}>
                      <thead>
                        <tr className="bg-muted/50 border-b border-border">
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">ID</th>
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">Modelo</th>
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">Cant.</th>
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">Lm</th>
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">W</th>
                          <th className="px-4 py-2 text-left text-[10px] font-bold text-muted-foreground uppercase">Eficiencia</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {(sd.luminarias || []).map((lum, idx) => (
                          <tr key={idx} className="hover:bg-muted/20 transition-colors">
                            <td className="px-4 py-2 font-mono text-xs">{lum.id || "-"}</td>
                            <td className="px-4 py-2 text-xs">{lum.modelo || "-"}</td>
                            <td className="px-4 py-2 font-mono text-xs font-medium">{lum.cantidad || 0}</td>
                            <td className="px-4 py-2 font-mono text-xs">{lum.lumens || 0}</td>
                            <td className="px-4 py-2 font-mono text-xs">{lum.watts || 0}</td>
                            <td className="px-4 py-2 font-mono text-xs">
                              <span className={lum.eficiencia >= 90 ? "text-emerald-500 font-bold" : lum.eficiencia >= 60 ? "text-amber-500" : "text-red-500"}>
                                {lum.eficiencia || 0}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
                {/* Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                  <div className="bg-muted/30 border border-border rounded-xl p-3 text-center">
                    <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-0.5">Total Lumens</p>
                    <p className="font-mono text-sm font-bold text-foreground">{(sd.total_lumens || 0).toLocaleString()}</p>
                  </div>
                  <div className="bg-muted/30 border border-border rounded-xl p-3 text-center">
                    <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-0.5">Total Watts</p>
                    <p className="font-mono text-sm font-bold text-foreground">{(sd.total_watts || 0).toLocaleString()}</p>
                  </div>
                  <div className={`border rounded-xl p-3 text-center ${sd.cumple_edge ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                    <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-0.5">Eficacia Global</p>
                    <p className={`font-mono text-sm font-bold ${sd.cumple_edge ? 'text-emerald-500' : 'text-red-500'}`}>
                      {sd.eficacia_global || 0} lm/W
                    </p>
                  </div>
                  <div className={`border rounded-xl p-3 text-center ${sd.cumple_edge ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-amber-500/10 border-amber-500/30'}`}>
                    <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-0.5">Cumple EDGE</p>
                    <p className={`text-sm font-bold ${sd.cumple_edge ? 'text-emerald-500' : 'text-amber-500'}`}>
                      {sd.cumple_edge ? "SI" : "NO"}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Areas Section */}
      {processedFiles.some((f) => f.areas && f.areas.length > 0) && (
        <div>
          <h3 className="text-base font-medium text-foreground mb-3" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Areas Calculadas
          </h3>
          <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
            <table className="w-full data-table" data-testid="areas-table">
              <thead>
                <tr className="bg-muted/50 border-b border-border">
                  <th className="px-4 py-2 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Archivo</th>
                  <th className="px-4 py-2 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Espacio</th>
                  <th className="px-4 py-2 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Area (m2)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {processedFiles
                  .filter((f) => f.areas && f.areas.length > 0)
                  .flatMap((f) =>
                    f.areas.map((area, idx) => (
                      <tr key={`${f.id}-${idx}`} className="hover:bg-muted/20 transition-colors">
                        <td className="px-4 py-2 text-sm">{idx === 0 ? f.filename : ""}</td>
                        <td className="px-4 py-2 text-sm">{area.nombre}</td>
                        <td className="px-4 py-2 font-mono text-xs font-bold text-primary">{area.area_m2}</td>
                      </tr>
                    ))
                  )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
