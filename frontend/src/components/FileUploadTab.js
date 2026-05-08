import { useState, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import {
  UploadSimple,
  FileText,
  FilePdf,
  Image,
  Trash,
  CheckCircle,
  WarningCircle,
  Clock,
  SpinnerGap,
  Eye,
  PencilRuler,
  Table,
} from "@phosphor-icons/react";

import { toast } from "sonner";

export default function FileUploadTab({ projectId, files, onRefresh, onPreview }) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const ALLOWED_TYPES = [".pdf", ".jpg", ".jpeg", ".png", ".dwg", ".dxf", ".xlsx", ".xls"];

  const handleFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    
    const validFiles = Array.from(fileList).filter(f => 
      ALLOWED_TYPES.some(ext => f.name.toLowerCase().endsWith(ext))
    );

    if (validFiles.length === 0) {
      toast.error("Formato de archivo no soportado (Use PDF, Imágenes, CAD o Excel)");
      return;
    }

    setUploading(true);
    let successCount = 0;
    try {
      for (const file of validFiles) {
        const formData = new FormData();
        formData.append("file", file);
        await axios.post(`${API}/projects/${projectId}/files`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        successCount++;
      }
      if (successCount > 0) {
        toast.success(`${successCount} archivo(s) subido(s) correctamente`);
      }
      await onRefresh();
    } catch (e) {
      console.error("Error uploading files:", e);
      toast.error("Error al subir uno o más archivos");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleDeleteFile = async (fileId) => {
    if (!window.confirm("¿Eliminar este archivo?")) return;
    try {
      await axios.delete(`${API}/files/${fileId}`);
      toast.success("Archivo eliminado");
      await onRefresh();
    } catch (e) {
      console.error("Error deleting file:", e);
      toast.error("Error al eliminar el archivo");
    }
  };

  const getFileIcon = (filename) => {
    const ext = filename.toLowerCase().split('.').pop();
    if (ext === 'pdf') return <FilePdf className="w-5 h-5 text-red-500" />;
    if (['jpg', 'jpeg', 'png'].includes(ext)) return <Image className="w-5 h-5 text-blue-500" />;
    if (['dwg', 'dxf'].includes(ext)) return <PencilRuler className="w-5 h-5 text-emerald-500" />;
    if (['xlsx', 'xls', 'csv'].includes(ext)) return <Table className="w-5 h-5 text-green-600" />;
    return <FileText className="w-5 h-5 text-muted-foreground" />;
  };

  const statusIcon = (status) => {
    switch (status) {
      case "processed":
        return <CheckCircle weight="fill" className="w-4 h-4 text-emerald-500" />;
      case "error":
        return <WarningCircle weight="fill" className="w-4 h-4 text-destructive" />;
      default:
        return <Clock className="w-4 h-4 text-muted-foreground animate-pulse" />;
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

  return (
    <div data-testid="file-upload-tab">
      {/* Upload Zone */}
      <div
        className={`drop-zone mb-6 group ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        data-testid="upload-zone"
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ALLOWED_TYPES.join(",")}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
          data-testid="file-input"
        />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
              <SpinnerGap className="w-6 h-6 text-primary animate-spin" />
            </div>
            <p className="text-sm font-bold animate-pulse">Subiendo documentos...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center text-primary mb-2 transition-all group-hover:scale-110 group-hover:bg-primary group-hover:text-white shadow-sm group-hover:shadow-glow">
              <UploadSimple weight="bold" className="w-7 h-7" />
            </div>
            <p className="text-sm font-bold">
              Arrastra archivos aquí o haz clic para seleccionar
            </p>
            <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground mt-1">
              PDF, Imágenes, CAD (DWG/DXF) o Excel
            </p>
          </div>
        )}
      </div>

      {/* File List */}
      {files.length === 0 ? (
        <div className="bg-card border border-border rounded-2xl p-16 text-center shadow-sm">
          <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4 text-muted-foreground">
            <FileText className="w-8 h-8" />
          </div>
          <p className="text-sm font-bold">No hay archivos subidos</p>
          <p className="text-xs text-muted-foreground mt-1">
            Sube documentos técnicos para clasificarlos automáticamente
          </p>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <table className="w-full data-table" data-testid="files-table">
            <thead>
              <tr className="bg-muted/30 border-b border-border">
                <th className="px-6 py-4 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Documento</th>
                <th className="px-6 py-4 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Estado</th>
                <th className="px-6 py-4 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Categoría</th>
                <th className="px-6 py-4 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Medida</th>
                <th className="px-6 py-4 text-right text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {files.map((f) => (
                <tr key={f.id} className="hover:bg-muted/20 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-muted/50 rounded-xl flex items-center justify-center flex-shrink-0">
                        {getFileIcon(f.filename)}
                      </div>
                      <div className="min-w-0">
                        <p className="truncate max-w-[240px] text-sm font-bold text-foreground leading-none">{f.filename}</p>
                        <p className="text-[10px] text-muted-foreground mt-1.5 font-mono">
                          {f.file_size > 1024 ? `${(f.file_size / 1024).toFixed(1)} KB` : `${f.file_size} B`}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-shrink-0">{statusIcon(f.status)}</div>
                      <span className="text-[10px] font-bold uppercase tracking-tight">
                        {f.status === "pending" ? "Pendiente" : f.status === "processed" ? "Procesado" : "Error"}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {f.category_edge ? (
                      <span className={`edge-badge ${categoryBadgeClass(f.category_edge)}`}>
                        {f.category_edge}
                      </span>
                    ) : (
                      <span className="text-xs opacity-40">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-mono text-xs font-bold text-primary">{f.measure_edge || "-"}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {f.status === "processed" && (
                        <button
                          onClick={() => onPreview && onPreview(f)}
                          className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-xl transition-all"
                          title="Previsualizar datos"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteFile(f.id); }}
                        className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl transition-all"
                        data-testid={`delete-file-${f.id}`}
                      >
                        <Trash className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
