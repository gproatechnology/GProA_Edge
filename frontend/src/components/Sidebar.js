import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { Folders, House, Lightning, SignOut, Moon, Sun } from "@phosphor-icons/react";

export default function Sidebar({ projects, onNavigate, stats }) {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;
  
  const [isDark, setIsDark] = useState(() => {
    return document.documentElement.classList.contains("dark");
  });

  const toggleDarkMode = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    if (newDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
      setIsDark(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("gproa_session");
    window.location.href = "/";
  };

  return (
    <aside
      className="fixed top-0 left-0 w-[260px] h-screen bg-card text-card-foreground border-r border-border flex flex-col z-30 shadow-[4px_0_24px_rgba(0,0,0,0.02)]"
      data-testid="sidebar"
    >
      {/* Logo & Theme Toggle */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-primary rounded-xl flex items-center justify-center shadow-sm">
            <Lightning weight="fill" className="text-primary-foreground w-4 h-4" />
          </div>
          <div>
            <span className="text-sm font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
              EDGE
            </span>
            <span className="text-[10px] uppercase tracking-[0.1em] text-muted-foreground block leading-tight">
              Doc Processor
            </span>
          </div>
        </div>
        
        <button 
          onClick={toggleDarkMode}
          className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground transition-colors"
          title="Cambiar tema"
        >
          {isDark ? <Sun size={18} weight="bold" /> : <Moon size={18} weight="bold" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 overflow-y-auto">
        <div className="mb-6">
          <p className="text-[10px] uppercase tracking-[0.1em] font-bold text-muted-foreground px-3 mb-2">
            Principal
          </p>
          <button
            onClick={() => onNavigate("/")}
            className={`sidebar-link w-full ${isActive("/") ? "active" : ""}`}
            data-testid="nav-dashboard"
          >
            <House weight={isActive("/") ? "fill" : "regular"} className="w-4 h-4" />
            Dashboard
          </button>
        </div>

        {/* Portfolio Summary */}
        <div className="mb-6 px-3">
          <p className="text-[10px] uppercase tracking-[0.1em] font-bold text-muted-foreground mb-2">
            Resumen Portafolio
          </p>
          <div className="bg-muted/30 rounded-2xl p-3 border border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-muted-foreground font-medium">Críticos</span>
              <span className="text-[10px] font-bold text-red-500 bg-red-500/10 px-1.5 rounded">
                {stats?.critical || 0}
              </span>
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-muted-foreground font-medium">Alta Prioridad</span>
              <span className="text-[10px] font-bold text-orange-500 bg-orange-500/10 px-1.5 rounded">
                {stats?.high || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-muted-foreground font-medium">Eficiencia Promedio</span>
              <span className="text-[10px] font-bold text-emerald-500">
                {stats?.efficiency || 0} <span className="text-[8px] opacity-60">kWh/m²</span>
              </span>
            </div>
          </div>
        </div>

        <div>
          <p className="text-[10px] uppercase tracking-[0.1em] font-bold text-muted-foreground px-3 mb-2">
            Proyectos
          </p>
          <div className="space-y-0.5">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => onNavigate(`/projects/${p.id}`)}
                className={`sidebar-link w-full ${
                  location.pathname === `/projects/${p.id}` ? "active" : ""
                }`}
                data-testid={`nav-project-${p.id}`}
              >
                <Folders
                  weight={location.pathname === `/projects/${p.id}` ? "fill" : "regular"}
                  className="w-4 h-4 flex-shrink-0"
                />
                <span className="truncate">{p.name}</span>
              </button>
            ))}
            {projects.length === 0 && (
              <p className="text-xs text-muted-foreground px-4 py-2 italic">Sin proyectos</p>
            )}
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border flex items-center justify-between">
        <p className="text-[10px] text-muted-foreground font-medium">
          EDGE Certification Tool v1.0
        </p>
        <button
          onClick={handleLogout}
          className="text-muted-foreground hover:text-destructive transition-colors p-1.5 rounded-md hover:bg-destructive/10"
          title="Cerrar Sesión"
          data-testid="logout-button"
        >
          <SignOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
