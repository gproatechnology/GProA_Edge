import React from "react";
import logoEosis from "../assets/branding/logo_eosis.png";
import logoEdge from "../assets/branding/logo_edge.png";

export default function DemoScreen({ onLogout }) {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center relative overflow-hidden bg-slate-900">
      
      {/* Ambient background */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-600/10 blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600/10 blur-[140px] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)]" />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center text-center px-8 max-w-lg">
        
        {/* Logos */}
        <div className="flex gap-6 items-center mb-12">
          <img src={logoEosis} alt="EOSIS" className="h-14 object-contain opacity-90" />
          <div className="h-10 w-[1px] bg-white/20" />
          <img src={logoEdge} alt="EDGE" className="h-10 object-contain opacity-90" />
        </div>

        {/* Badge */}
        <div className="px-4 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 mb-6">
          <span className="text-emerald-400 text-xs font-semibold tracking-widest uppercase">Próximamente</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl font-bold text-white mb-4 leading-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
          GProA EDGE
        </h1>
        <p className="text-slate-400 text-base leading-relaxed mb-3">
          Plataforma de Inteligencia para Certificación de Edificios Verdes
        </p>
        <p className="text-slate-600 text-sm leading-relaxed mb-10">
          Esta plataforma es de uso exclusivo para el equipo GProA y sus clientes certificados.<br/>
          El acceso completo estará disponible próximamente.
        </p>

        {/* Features preview */}
        <div className="grid grid-cols-3 gap-4 mb-12 w-full">
          {[
            { icon: "🏗️", label: "Gestión de Proyectos EDGE" },
            { icon: "🤖", label: "Análisis IA de Documentos" },
            { icon: "📊", label: "Dashboard de Métricas" },
          ].map((f) => (
            <div key={f.label} className="flex flex-col items-center gap-2 p-4 rounded-xl border border-white/5 bg-white/3">
              <span className="text-2xl">{f.icon}</span>
              <span className="text-slate-500 text-xs text-center leading-snug">{f.label}</span>
            </div>
          ))}
        </div>

        {/* CTA GProA */}
        <div className="w-full rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 mb-6 text-center">
          <p className="text-slate-300 text-sm font-semibold mb-1">
            ¿Quieres una plataforma como esta para tu organización?
          </p>
          <p className="text-slate-500 text-xs leading-relaxed mb-4">
            GProA Technology desarrolla soluciones digitales personalizadas para consultoría de edificios verdes, automatización de certificaciones y análisis con IA.
          </p>
          <a
            href="https://gproatechnology.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-900 text-sm font-bold transition-all shadow-lg shadow-emerald-500/20 active:scale-95"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
            Solicitar desarrollo en gproatechnology.com
          </a>
        </div>

        {/* Contact / back */}
        <p className="text-slate-600 text-xs mb-4">
          ¿Tienes acceso autorizado?
        </p>
        <button
          onClick={onLogout}
          className="px-6 py-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 text-sm font-medium transition-all"
        >
          ← Volver al Inicio de Sesión
        </button>
      </div>

      {/* Bottom bar */}
      <div className="absolute bottom-6 text-center">
        <p className="text-slate-700 text-xs">GProA Technology © 2026 · Certificación EDGE</p>
      </div>
    </div>
  );
}
