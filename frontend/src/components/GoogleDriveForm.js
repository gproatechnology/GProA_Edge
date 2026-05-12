import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { GoogleLogo, Folder, File, CheckCircle, Warning, SpinnerGap, ArrowRight, CloudArrowDown } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function GoogleDriveForm({ projectId, user, onComplete }) {
  const [status, setStatus] = useState({ connected: false, credentials_configured: false });
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [files, setFiles] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [syncing, setSyncing] = useState(false);

  const userId = user?.id || user?.name || "default_user";

  useEffect(() => {
    checkStatus();
  }, [userId]);

  const checkStatus = async () => {
    try {
      const res = await axios.get(`${API}/google-drive/status/${userId}`);
      setStatus(res.data);
      if (res.data.connected) {
        fetchFiles();
      }
    } catch (e) {
      console.error("Error checking drive status:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchFiles = async (folderId = 'root') => {
    try {
      const res = await axios.get(`${API}/google-drive/files/${userId}?folder_id=${folderId}`);
      setFiles(res.data.files);
      // If we are jumping to a specific folder (like the CEO shortcut), 
      // we might want to clear the 'selected' state to allow fresh navigation
      if (folderId !== 'root' && !selectedFolder) {
        // Option: we could set a 'currentFolder' state for breadcrumbs
      }
    } catch (e) {
      toast.error("Error al obtener archivos de Drive");
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      localStorage.setItem("google_auth_user_id", userId);
      const redirectUri = `${window.location.origin}/google-callback`;
      const res = await axios.get(`${API}/google-drive/auth-url?user_id=${userId}&redirect_uri=${encodeURIComponent(redirectUri)}`);
      
      const authWindow = window.open(res.data.auth_url, "Connect Google Drive", "width=600,height=700");
      
      // Poll for window closure or success message
      const checkWindow = setInterval(async () => {
        if (authWindow.closed) {
          clearInterval(checkWindow);
          setConnecting(false);
          checkStatus();
        }
      }, 1000);

      // Listen for postMessage from the callback page
      window.addEventListener("message", async (event) => {
        if (event.data.type === "GOOGLE_AUTH_SUCCESS") {
          authWindow.close();
          toast.success("¡Cuenta conectada correctamente!");
          checkStatus();
        }
      }, { once: true });

    } catch (e) {
      toast.error("Error al iniciar la conexión");
      setConnecting(false);
    }
  };

  const handleSync = async () => {
    if (!selectedFolder) return;
    setSyncing(true);
    try {
      toast.info("Sincronizando archivos...");
      const res = await axios.post(`${API}/google-drive/sync/${projectId}?user_id=${userId}&folder_id=${selectedFolder.id}`);
      toast.success(res.data.message);
      if (onComplete) onComplete();
    } catch (e) {
      toast.error("Error en la sincronización");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <SpinnerGap className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center gap-3 p-4 bg-primary/5 rounded-2xl border border-primary/10">
        <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center">
          <GoogleLogo weight="bold" className="w-7 h-7 text-[#4285F4]" />
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-foreground">Tu Google Drive</h3>
          <p className="text-xs text-muted-foreground">
            {status.connected ? `Conectado como ${user?.name || 'usuario'}` : "Conecta cualquier cuenta de Drive"}
          </p>
        </div>
        {status.connected && (
          <CheckCircle weight="fill" className="w-6 h-6 text-emerald-500" />
        )}
      </div>

      {!status.connected ? (
        <div className="space-y-4">
          <div className="p-4 bg-muted/50 rounded-xl border border-border text-sm text-muted-foreground">
            <p className="mb-2">Vincula tu cuenta personal o de empresa para:</p>
            <ul className="space-y-1 list-disc list-inside text-xs">
              <li>Escanear tus archivos privados</li>
              <li>Mantener el control de tus documentos</li>
              <li>Importación instantánea a EDGE</li>
            </ul>
          </div>
          
          <button
            onClick={handleConnect}
            disabled={connecting || !status.credentials_configured}
            className="w-full py-4 bg-primary text-primary-foreground rounded-xl font-bold flex items-center justify-center gap-3 hover:shadow-glow transition-all active:scale-95 disabled:opacity-50"
          >
            {connecting ? (
              <SpinnerGap className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <GoogleLogo weight="bold" className="w-5 h-5" />
                Conectar mi cuenta
              </>
            )}
          </button>
          
          {!status.credentials_configured && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-[10px] text-red-600 font-medium">
              <Warning weight="fill" className="w-4 h-4 shrink-0" />
              Configuración de API pendiente en el servidor.
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Explora y Sincroniza</div>
            <div className="flex gap-2">
              <button 
                onClick={() => fetchFiles('1904H0WB7kpNC4sCP_m4hJD4zg6ixbfCQ')} 
                className="text-[10px] bg-primary/10 text-primary px-2 py-1 rounded hover:bg-primary/20 font-bold transition-all"
              >
                📁 Proyectos GProA
              </button>
              {selectedFolder && (
                <button onClick={() => setSelectedFolder(null)} className="text-[10px] text-primary font-bold hover:underline">Volver</button>
              )}
            </div>
          </div>
          
          <div className="max-h-[250px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
            {!selectedFolder ? (
              // List Folders
              files.filter(f => f.mimeType === 'application/vnd.google-apps.folder').map(folder => (
                <button
                  key={folder.id}
                  onClick={() => { setSelectedFolder(folder); fetchFiles(folder.id); }}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border bg-card border-border hover:border-primary/30 text-muted-foreground transition-all group"
                >
                  <Folder weight="fill" className="w-5 h-5 text-amber-500 group-hover:scale-110 transition-transform" />
                  <span className="flex-1 text-left text-sm font-medium truncate">{folder.name}</span>
                  <ArrowRight weight="bold" className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))
            ) : (
              // List Files in selected folder
              <div className="space-y-2">
                <div className="p-2 bg-primary/5 border border-primary/10 rounded-lg mb-4">
                  <div className="text-[10px] font-bold text-primary uppercase">Carpeta Seleccionada</div>
                  <div className="text-sm font-bold truncate">{selectedFolder.name}</div>
                </div>
                
                {files.filter(f => f.mimeType !== 'application/vnd.google-apps.folder').map(file => (
                  <div
                    key={file.id}
                    className="flex items-center gap-3 p-3 rounded-xl border bg-card border-border"
                  >
                    <div className={`p-2 rounded-lg ${
                      file.suggested_category === 'Plano CAD' ? 'bg-blue-500/10 text-blue-500' : 
                      file.suggested_category === 'Cálculo' ? 'bg-emerald-500/10 text-emerald-500' : 
                      'bg-muted text-muted-foreground'
                    }`}>
                      {file.suggested_category === 'Plano CAD' ? <File weight="fill" /> : <File weight="bold" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold truncate">{file.name}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[9px] px-1.5 py-0.5 bg-muted rounded text-muted-foreground font-bold uppercase">{file.suggested_category}</span>
                        <span className="text-[9px] text-primary font-bold">{file.edge_resource}</span>
                      </div>
                    </div>
                  </div>
                ))}
                
                {files.filter(f => f.mimeType !== 'application/vnd.google-apps.folder').length === 0 && (
                  <p className="text-center py-6 text-xs text-muted-foreground italic">No hay archivos compatibles en esta carpeta.</p>
                )}
              </div>
            )}
          </div>

          {selectedFolder && (
            <button
              onClick={handleSync}
              disabled={syncing}
              className="w-full py-4 bg-primary text-primary-foreground rounded-xl font-bold flex items-center justify-center gap-3 hover:shadow-glow transition-all active:scale-95 disabled:opacity-50"
            >
              {syncing ? (
                <SpinnerGap className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <CloudArrowDown weight="fill" className="w-5 h-5" />
                  Sincronizar esta carpeta
                </>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
