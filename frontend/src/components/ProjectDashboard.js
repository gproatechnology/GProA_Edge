import { useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Plus, Folders, ArrowRight, MagnifyingGlass, Funnel } from "@phosphor-icons/react";
import { toast } from "sonner";
import ProjectAnalytics from "./ProjectAnalytics";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TYPOLOGIES = [
  { value: "Industrial", label: "Industrial" },
  { value: "Residencial", label: "Residencial" },
  { value: "Hospitalidad", label: "Hospitalidad" },
  { value: "Corporativo", label: "Corporativo" },
  { value: "Comercial", label: "Comercial" },
  { value: "Educativo", label: "Educativo" },
  { value: "Cultura, Deporte y Salud", label: "Cultura, Deporte y Salud" },
  { value: "Data Center", label: "Data Center" },
  { value: "Otro", label: "Otro" },
];

const getPriorityColor = (priority) => {
  switch (priority?.toLowerCase()) {
    case "crítica":
    case "critica":
      return "bg-red-500/10 text-red-500 border-red-500/20";
    case "alta":
      return "bg-orange-500/10 text-orange-500 border-orange-500/20";
    case "media":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20";
    case "baja":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
};

export default function ProjectDashboard({ projects, loading, stats, onProjectCreated, onNavigate }) {
  const [showDialog, setShowDialog] = useState(false);
  const [name, setName] = useState("");
  const [typology, setTypology] = useState("");
  const [creating, setCreating] = useState(false);
  const [search, setSearch] = useState("");
  const [filterTypology, setFilterTypology] = useState("all");
  const [filterPriority, setFilterPriority] = useState("all");

  const filteredProjects = projects.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase());
    const matchesTypology = filterTypology === "all" || p.typology === filterTypology;
    const matchesPriority = filterPriority === "all" || p.priority === filterPriority;
    return matchesSearch && matchesTypology && matchesPriority;
  });

  const handleCreate = async () => {
    if (!name.trim() || !typology) return;
    setCreating(true);
    try {
      await axios.post(`${API}/projects/`, { name: name.trim(), typology });
      setName("");
      setTypology("");
      setShowDialog(false);
      onProjectCreated();
      toast.success("Proyecto creado correctamente");
    } catch (e) {
      console.error("Error creating project:", e);
      toast.error("Error al crear el proyecto");
    } finally {
      setCreating(false);
    }
  };

  const clearFilters = () => {
    setSearch("");
    setFilterTypology("all");
    setFilterPriority("all");
  };

  const getCountByTypology = (type) => projects.filter(p => p.typology === type).length;
  const getCountByPriority = (prio) => projects.filter(p => p.priority === prio).length;
  const isFiltered = search !== "" || filterTypology !== "all" || filterPriority !== "all";

  const totalFiles = projects.reduce((sum, p) => sum + (p.file_count || 0), 0);
  const processedFiles = projects.reduce((sum, p) => sum + (p.processed_count || 0), 0);

  return (
    <div className="p-6 md:p-8 max-w-[1600px] mx-auto space-y-8 animate-fadeIn" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Proyectos
          </h1>
          <p className="text-muted-foreground mt-2 font-medium">Gestiona tus proyectos de certificación EDGE</p>
        </div>
        <button
          onClick={() => setShowDialog(true)}
          className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:shadow-glow transition-all active:scale-95 shadow-lg"
          data-testid="create-project-btn"
        >
          <Plus weight="bold" className="w-5 h-5" />
          Nuevo Proyecto
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-1">Total Proyectos</p>
          <p className="text-2xl font-bold font-mono">{stats?.total_projects ?? projects.length}</p>
        </div>
        <div className="stat-card">
          <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-1">Archivos Totales</p>
          <p className="text-2xl font-bold font-mono">{stats?.total_files ?? totalFiles}</p>
        </div>
        <div className="stat-card">
          <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-1">Procesados</p>
          <p className="text-2xl font-bold font-mono">{stats?.processed_files ?? processedFiles}</p>
        </div>
        <div className="stat-card border-l-4 border-l-emerald-500 bg-emerald-500/5">
          <p className="text-[10px] uppercase tracking-wider font-bold text-emerald-600 mb-1">Reducción CO2</p>
          <p className="text-2xl font-bold font-mono text-emerald-600">
            {((stats?.processed_files ?? processedFiles) * 5.2).toFixed(1)} <span className="text-xs">tCO2e</span>
          </p>
        </div>
      </div>

      {/* Analytics Section */}
      {!loading && projects.length > 0 && (
        <ProjectAnalytics projects={projects} />
      )}

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input 
            type="text"
            placeholder="Buscar proyecto por nombre..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-card border border-border rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all shadow-sm"
          />
        </div>
        <div className="flex gap-2">
          {/* Aquí se asume que Select ya usa estilos de tema o es de una librería como shadcn */}
          <Select value={filterTypology} onValueChange={setFilterTypology}>
            <SelectTrigger className="w-[200px] bg-card border-border rounded-xl shadow-sm text-foreground">
              <SelectValue placeholder="Tipología" />
            </SelectTrigger>
            <SelectContent className="bg-popover text-popover-foreground border-border">
              <SelectItem value="all">Todas las tipologías ({projects.length})</SelectItem>
              {TYPOLOGIES.map(t => (
                <SelectItem key={t.value} value={t.value}>
                  <div className="flex items-center justify-between w-full gap-8">
                    <span>{t.label}</span>
                    <span className="text-[10px] bg-muted text-muted-foreground px-1.5 rounded-full">{getCountByTypology(t.value)}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterPriority} onValueChange={setFilterPriority}>
            <SelectTrigger className="w-[160px] bg-card border-border rounded-xl shadow-sm text-foreground">
              <SelectValue placeholder="Prioridad" />
            </SelectTrigger>
            <SelectContent className="bg-popover text-popover-foreground border-border">
              <SelectItem value="all">Todas</SelectItem>
              {["Crítica", "Alta", "Media", "Baja"].map(p => (
                <SelectItem key={p} value={p}>
                  <div className="flex items-center justify-between w-full gap-8">
                    <span>{p}</span>
                    <span className="text-[10px] bg-muted text-muted-foreground px-1.5 rounded-full">{getCountByPriority(p)}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Active Filter Pills */}
      {isFiltered && (
        <div className="flex items-center gap-2 mb-6 animate-fadeIn">
          <span className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mr-2">Filtros Activos:</span>
          {search && (
            <button onClick={() => setSearch("")} className="px-2 py-1 bg-muted text-muted-foreground rounded-lg text-xs hover:bg-muted/80 transition-colors">
              Búsqueda: {search} <span className="ml-1 opacity-60">×</span>
            </button>
          )}
          {filterTypology !== "all" && (
            <button onClick={() => setFilterTypology("all")} className="px-2 py-1 bg-muted text-muted-foreground rounded-lg text-xs hover:bg-muted/80 transition-colors">
              Tipo: {filterTypology} <span className="ml-1 opacity-60">×</span>
            </button>
          )}
          {filterPriority !== "all" && (
            <button onClick={() => setFilterPriority("all")} className="px-2 py-1 bg-muted text-muted-foreground rounded-lg text-xs hover:bg-muted/80 transition-colors">
              Prioridad: {filterPriority} <span className="ml-1 opacity-60">×</span>
            </button>
          )}
          <button 
            onClick={clearFilters}
            className="text-[10px] font-bold text-primary hover:underline ml-2"
          >
            Limpiar todo
          </button>
        </div>
      )}

      {/* Projects grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div key={i} className="stat-card h-40 animate-skeleton" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="bg-card border border-border rounded-2xl p-16 text-center animate-fadeIn shadow-sm">
          <div className="w-16 h-16 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4 text-primary">
            <Folders className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Sin proyectos
          </h3>
          <p className="text-sm text-muted-foreground mb-6">
            Crea tu primer proyecto para comenzar a clasificar documentos EDGE
          </p>
          <button
            onClick={() => setShowDialog(true)}
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-xl text-sm font-medium shadow-lg shadow-primary/20 hover:scale-105 transition-all"
            data-testid="empty-create-project-button"
          >
            <Plus weight="bold" className="w-4 h-4" />
            Crear Proyecto
          </button>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-card border border-border rounded-2xl p-16 text-center animate-fadeIn shadow-sm">
          <div className="w-16 h-16 bg-muted rounded-xl flex items-center justify-center mx-auto mb-4 text-muted-foreground">
            <Funnel className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold mb-2">No hay resultados</h3>
          <p className="text-sm text-muted-foreground">Intenta ajustar los filtros de búsqueda</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((project, idx) => (
            <button
              key={project.id}
              onClick={() => onNavigate(`/projects/${project.id}`)}
              className="stat-card text-left border border-border hover:border-primary transition-all duration-200 group animate-fadeIn"
              style={{ animationDelay: `${idx * 50}ms` }}
              data-testid={`project-card-${project.id}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-bold text-foreground truncate" style={{ fontFamily: "'Outfit', sans-serif" }}>
                    {project.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="edge-badge capitalize">
                      {project.typology}
                    </span>
                    {project.priority && (
                      <span className={`text-[9px] px-2 py-0.5 rounded-full border font-bold uppercase tracking-wider ${getPriorityColor(project.priority)}`}>
                        {project.priority}
                      </span>
                    )}
                  </div>
                  {project.square_meters > 0 && project.annual_consumption_kwh > 0 && (
                    <div className="mt-2 flex items-center gap-1.5 text-muted-foreground">
                      <div className="w-1 h-1 rounded-full bg-primary" />
                      <p className="text-[11px] font-medium">
                        {(project.annual_consumption_kwh / project.square_meters).toFixed(1)} <span className="text-[9px] opacity-60">kWh/m²</span>
                      </p>
                    </div>
                  )}
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 mt-1" />
              </div>
              <div className="flex items-center gap-4 mt-4 pt-3 border-t border-border">
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">Archivos</p>
                  <p className="text-lg font-bold font-mono">{project.file_count}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">Procesados</p>
                  <p className="text-lg font-bold text-emerald-500 font-mono">{project.processed_count}</p>
                </div>
                <div className="ml-auto">
                  <p className="text-[10px] text-muted-foreground">
                    {new Date(project.created_at).toLocaleDateString("es-ES", { day: "2-digit", month: "short" })}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-[420px]" data-testid="create-project-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Outfit', sans-serif" }} className="text-lg font-bold text-slate-900">Nuevo Proyecto</DialogTitle>
            <DialogDescription className="text-xs text-slate-500">Completa los datos básicos para iniciar la clasificación.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="project-name" className="text-[10px] uppercase tracking-[0.1em] font-semibold text-slate-500">
                Nombre del Proyecto
              </Label>
              <Input
                id="project-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ej: Torre Central - EDGE Avanzado"
                className="mt-1.5"
                data-testid="project-name-input"
              />
            </div>
            <div>
              <Label htmlFor="project-type" className="text-[10px] uppercase tracking-[0.1em] font-semibold text-slate-500">
                Tipologia
              </Label>
              <Select value={typology} onValueChange={setTypology}>
                <SelectTrigger className="mt-1.5" data-testid="project-typology-select">
                  <SelectValue placeholder="Seleccionar tipo" />
                </SelectTrigger>
                <SelectContent>
                  {TYPOLOGIES.map((t) => (
                    <SelectItem key={t.value} value={t.value} data-testid={`typology-option-${t.value}`}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <button
              onClick={() => setShowDialog(false)}
              className="px-4 py-2 text-sm font-medium text-slate-700 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
              data-testid="cancel-create-project"
            >
              Cancelar
            </button>
            <button
              onClick={handleCreate}
              disabled={creating || !name.trim() || !typology}
              className="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 shadow-sm hover:shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="confirm-create-project"
            >
              {creating ? "Creando..." : "Crear Proyecto"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
