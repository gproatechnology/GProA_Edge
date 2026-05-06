import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { ArrowLeft, Trash, Lightning, Gauge, FilePdf, DownloadSimple, SpinnerGap } from "@phosphor-icons/react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import FileUploadTab from "@/components/FileUploadTab";
import ExtractedDataTab from "@/components/ExtractedDataTab";
import EdgeStatusTab from "@/components/EdgeStatusTab";
import EdgeComplianceTab from "@/components/EdgeComplianceTab";
import BatchProgressModal from "@/components/BatchProgressModal";
import DataPreviewModal from "@/components/DataPreviewModal";
import { generateProjectPDF } from "@/utils/generateProjectPDF";

const TABS = [
  { id: "files", label: "Archivos" },
  { id: "data", label: "Datos Extraidos" },
  { id: "compliance", label: "Compliance EDGE" },
  { id: "status", label: "Resumen" },
];

export default function ProjectDetail({ projectId, onProjectDeleted }) {
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [activeTab, setActiveTab] = useState("files");
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [processingEdge, setProcessingEdge] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);

  const fetchProject = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/projects/${projectId}`);
      setProject(res.data);
    } catch (e) {
      console.error("Error fetching project:", e);
    }
  }, [projectId]);

  const fetchFiles = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/projects/${projectId}/files`);
      setFiles(res.data);
    } catch (e) {
      console.error("Error fetching files:", e);
    }
  }, [projectId]);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/projects/${projectId}/edge-status`);
      setStatus(res.data);
    } catch (e) {
      console.error("Error fetching status:", e);
    }
  }, [projectId]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([fetchProject(), fetchFiles(), fetchStatus()]);
      setLoading(false);
    };
    load();
  }, [fetchProject, fetchFiles, fetchStatus]);

  const handleDelete = async () => {
    if (!window.confirm("¿Eliminar este proyecto y todos sus archivos?")) return;
    setDeleting(true);
    try {
      await axios.delete(`${API}/projects/${projectId}`);
      toast.success("Proyecto eliminado correctamente");
      onProjectDeleted();
    } catch (e) {
      console.error("Error deleting project:", e);
      toast.error("Error al eliminar el proyecto");
    } finally {
      setDeleting(false);
    }
  };

  const refreshData = useCallback(async () => {
    await Promise.all([fetchProject(), fetchFiles(), fetchStatus()]);
  }, [fetchProject, fetchFiles, fetchStatus]);

  const handleProcessEdge = async () => {
    if (files.length === 0) {
      toast.error("No hay archivos para procesar");
      return;
    }
    setProcessingEdge(true);
    try {
      const res = await axios.post(`${API}/projects/${projectId}/process-edge`);
      setCurrentJobId(res.data.job_id);
      setShowProgress(true);
      toast.info("Iniciando procesamiento EDGE...");
    } catch (e) {
      console.error("Error starting EDGE processing:", e);
      toast.error("Error al iniciar el procesamiento");
      setProcessingEdge(false);
    }
  };

  const handleExportPDF = async () => {
    setGeneratingPdf(true);
    try {
      toast.info("Generando reporte PDF...");
      await refreshData();
      generateProjectPDF(project, files, status);
      toast.success("Reporte PDF generado");
    } catch (e) {
      console.error("Error generating PDF:", e);
      toast.error("Error al generar el PDF");
    } finally {
      setGeneratingPdf(false);
    }
  };

  const handleProgressComplete = useCallback(() => {
    setShowProgress(false);
    setProcessingEdge(false);
    setCurrentJobId(null);
    refreshData();
  }, [refreshData]);

  if (loading) {
    return (
      <div className="p-6 md:p-8 max-w-[1600px] mx-auto">
        <div className="flex items-center justify-center py-20">
          <SpinnerGap className="w-10 h-10 text-primary animate-spin" />
        </div>
      </div>
    );
  }

  if (!project) return null;

  return (
    <div className="p-6 md:p-8 max-w-[1600px] mx-auto space-y-8 animate-fadeIn" data-testid="project-detail">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <button
            onClick={() => onProjectDeleted()}
            className="w-12 h-12 bg-card border border-border rounded-2xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-primary/20 transition-all shadow-sm active:scale-95"
            data-testid="back-button"
          >
            <ArrowLeft weight="bold" className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <h1 className="text-3xl font-bold tracking-tight text-foreground" style={{ fontFamily: "'Outfit', sans-serif" }}>
                {project.name}
              </h1>
              <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border ${
                project.priority?.toLowerCase() === 'crítica' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                project.priority?.toLowerCase() === 'alta' ? 'bg-orange-500/10 text-orange-500 border-orange-500/20' :
                'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
              }`}>
                {project.priority || "Normal"}
              </span>
            </div>
            <div className="flex items-center gap-4 text-muted-foreground text-sm font-medium">
              <div className="flex items-center gap-1.5">
                <Lightning weight="fill" className="w-4 h-4" />
                {project.typology}
              </div>
              <div className="w-1 h-1 bg-border rounded-full" />
              <div className="flex items-center gap-1.5">
                <Gauge weight="fill" className="w-4 h-4" />
                {project.efficiency || 0}% de ahorro
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportPDF}
            disabled={generatingPdf}
            className="flex items-center gap-2.5 px-6 py-3 bg-card border border-border text-foreground rounded-xl font-bold hover:bg-muted transition-all active:scale-95 disabled:opacity-50 shadow-sm"
          >
            {generatingPdf ? (
              <SpinnerGap className="w-5 h-5 animate-spin text-primary" />
            ) : (
              <DownloadSimple weight="bold" className="w-5 h-5 text-primary" />
            )}
            Exportar Reporte
          </button>

          <button
            onClick={handleProcessEdge}
            disabled={processingEdge || files.length === 0}
            className={`flex items-center gap-2.5 px-6 py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:shadow-glow transition-all active:scale-95 disabled:opacity-50 disabled:hover:shadow-none shadow-lg`}
            data-testid="process-edge-btn"
          >
            {processingEdge ? (
              <SpinnerGap className="w-5 h-5 animate-spin" />
            ) : (
              <Lightning weight="fill" className="w-5 h-5" />
            )}
            Procesar Proyecto
          </button>
          
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-3 bg-card border border-border text-muted-foreground hover:text-destructive hover:border-destructive/20 rounded-xl transition-all shadow-sm active:scale-95"
            data-testid="delete-project-btn"
          >
            <Trash weight="bold" className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1.5 bg-muted/30 border border-border rounded-2xl w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-2.5 text-xs font-bold uppercase tracking-wider rounded-xl transition-all ${
              activeTab === tab.id
                ? "bg-card text-primary shadow-sm border border-border"
                : "text-muted-foreground hover:text-foreground"
            }`}
            data-testid={`tab-${tab.id}`}
          >
            {tab.id === "files" && <FilePdf weight="fill" className="w-3.5 h-3.5 inline mr-2" />}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-8 animate-fadeIn">
        {activeTab === "files" && (
          <FileUploadTab 
            projectId={projectId} 
            files={files} 
            onRefresh={refreshData} 
            onPreview={(f) => setPreviewFile(f)}
          />
        )}
        {activeTab === "data" && (
          <ExtractedDataTab projectId={projectId} files={files} onRefresh={refreshData} />
        )}
        {activeTab === "compliance" && <EdgeComplianceTab files={files} />}
        {activeTab === "status" && <EdgeStatusTab projectId={projectId} />}
      </div>

      <BatchProgressModal
        isOpen={showProgress}
        onClose={handleProgressComplete}
        jobId={currentJobId}
        projectId={projectId}
        api={API}
        onComplete={handleProgressComplete}
      />

      <DataPreviewModal
        isOpen={!!previewFile}
        onClose={() => setPreviewFile(null)}
        file={previewFile}
      />
    </div>
  );
}
