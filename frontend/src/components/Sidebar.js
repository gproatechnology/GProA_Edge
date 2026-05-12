import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { Folders, House, SignOut, Moon, Sun } from "@phosphor-icons/react";
import logoEosis from "../assets/branding/logo_eosis.png";
import logoEdge from "../assets/branding/logo_edge.png";

export default function Sidebar({ projects, onNavigate, stats, user }) {
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

  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("gproa_session");
    localStorage.removeItem("gproa_user");
    localStorage.removeItem("gproa_chat_name");
    window.location.href = "/";
  };

  // Debugging user prop
  useEffect(() => {
    console.log("SIDEBAR USER DATA:", user);
  }, [user]);

  return (
    <aside
      className="fixed top-0 left-0 w-[260px] h-screen bg-card text-card-foreground border-r border-border flex flex-col z-30 shadow-[4px_0_24px_rgba(0,0,0,0.02)]"
      data-testid="sidebar"
    >
      {/* Logo & Theme Toggle */}
      <div className="h-20 flex items-center justify-between px-5 border-b border-border bg-muted/20">
        <div className="flex flex-col gap-1">
          <img src={logoEosis} alt="EOSIS" className="h-6 object-contain" />
          <div className="flex items-center gap-1.5 mt-1">
            <img src={logoEdge} alt="EDGE" className="h-4 object-contain opacity-80" />
            <span className="text-[8px] uppercase tracking-widest font-bold text-muted-foreground">
              Assistant
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

        {/* Portfolio Summary - Only for Managers */}
        {user?.role === "manager" && (
          <div className="mb-6 px-3">
            <p className="text-[10px] uppercase tracking-[0.1em] font-bold text-muted-foreground mb-2">
              KPIs Gerencia
            </p>
            <div className="bg-primary/5 rounded-2xl p-3 border border-primary/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] text-muted-foreground font-medium">Proyectos Críticos</span>
                <span className="text-[10px] font-bold text-red-500 bg-red-500/10 px-1.5 rounded">
                  {stats?.critical || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground font-medium">Eficiencia Media</span>
                <span className="text-[10px] font-bold text-emerald-500">
                  {stats?.efficiency || 0}
                </span>
              </div>
            </div>
          </div>
        )}

        <div>
          <p className="text-[10px] uppercase tracking-[0.1em] font-bold text-muted-foreground px-3 mb-2">
            {user?.role === "consultant" ? "Mis Proyectos EDGE" : "Proyectos"}
          </p>
          <div className="space-y-0.5">
            {Array.isArray(projects) && projects.map((p) => (
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
          </div>
        </div>
      </nav>

      {/* Footer / User Profile with Menu */}
      <div className="px-3 py-4 border-t border-border bg-muted/10 relative">
        {/* User Popover Menu */}
        {showUserMenu && (
          <div className="absolute bottom-[calc(100%-8px)] left-3 right-3 mb-2 bg-card border border-border rounded-2xl shadow-xl z-50 py-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <div className="px-3 py-2 mb-1 border-b border-border/50">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Opciones Especiales</p>
            </div>
            <button className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-muted text-foreground transition-colors text-left">
              <div className="w-5 h-5 rounded bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                <Folders size={12} weight="bold" />
              </div>
              <span>Panel de Auditoría</span>
            </button>
            <button className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-muted text-foreground transition-colors text-left">
              <div className="w-5 h-5 rounded bg-blue-500/10 text-blue-500 flex items-center justify-center">
                <House size={12} weight="bold" />
              </div>
              <span>Configuración EDGE</span>
            </button>
            <div className="h-px bg-border/50 my-1"></div>
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-destructive/10 text-destructive transition-colors font-medium text-left"
            >
              <div className="w-5 h-5 rounded bg-destructive/10 flex items-center justify-center">
                <SignOut size={12} weight="bold" />
              </div>
              <span>Cerrar Sesión</span>
            </button>
          </div>
        )}

        <button 
          onClick={() => setShowUserMenu(!showUserMenu)}
          className={`w-full flex items-center gap-3 px-2 py-2 rounded-xl transition-all ${showUserMenu ? 'bg-muted ring-1 ring-border' : 'hover:bg-muted/50'}`}
        >
          {/* Avatar: Google photo or styled initial */}
          <div className="w-8 h-8 rounded-full overflow-hidden border border-primary/20 bg-primary/10 flex items-center justify-center shadow-sm flex-shrink-0">
            {user?.image && user.image.startsWith("http") ? (
              <img 
                src={user.image} 
                alt={user.name} 
                className="w-full h-full object-cover"
                onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
              />
            ) : null}
            <span 
              className="text-primary font-bold text-xs"
              style={{ display: user?.image && user.image.startsWith("http") ? 'none' : 'flex' }}
            >
              {user?.name ? user.name.charAt(0).toUpperCase() : "G"}
            </span>
          </div>
          <div className="flex-1 min-w-0 text-left">
            <p className="text-xs font-bold truncate">{user?.name || "Usuario"}</p>
            <p className="text-[10px] text-muted-foreground leading-none mt-0.5 truncate">
              {user?.email || user?.role || "Invitado"}
            </p>
          </div>
          <div className={`transition-transform duration-300 ${showUserMenu ? 'rotate-180' : ''}`}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-muted-foreground">
              <path d="M2.5 4.5L6 8L9.5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </button>
      </div>
    </aside>
  );
}
