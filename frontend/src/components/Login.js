import React, { useState } from "react";
import { Lock, Mail, ArrowRight } from "lucide-react";
import logoEosis from "../assets/branding/logo_eosis.png";
import logoEdge from "../assets/branding/logo_edge.png";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Identificar perfil basado en el email
    const user = email.toLowerCase().includes("jorge") 
      ? { name: "Jorge", role: "manager", avatar: "J" }
      : { name: "Luis", role: "consultant", avatar: "L" };

    setTimeout(() => {
      setIsLoading(false);
      onLogin(user); 
    }, 1200);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-slate-900">
      {/* Background ambient light effects */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-600/20 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600/20 blur-[120px] pointer-events-none"></div>
      
      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)]"></div>

      <div className="relative z-10 w-full max-w-md p-8 m-4 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl">
        
        {/* Header */}
        <div className="flex flex-col items-center mb-10">
          <div className="flex gap-4 items-center mb-6">
            <img src={logoEosis} alt="EOSIS" className="h-10 object-contain" />
            <div className="h-8 w-[1px] bg-white/20"></div>
            <img src={logoEdge} alt="EDGE" className="h-8 object-contain" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Assistant Pro
          </h2>
          <p className="text-slate-400 text-sm">GProA EDGE Certification System</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 ml-1">Email</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
                <Mail size={18} />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="usuario@gproa.com"
                className="w-full bg-slate-900/50 border border-slate-700/50 text-white text-sm rounded-xl py-3 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 ml-1">Contraseña</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
                <Lock size={18} />
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900/50 border border-slate-700/50 text-white text-sm rounded-xl py-3 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full relative group bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold text-sm py-3.5 rounded-xl transition-all disabled:opacity-70 flex items-center justify-center overflow-hidden mt-8"
          >
            {isLoading ? (
              <div className="h-5 w-5 rounded-full border-2 border-slate-900 border-t-transparent animate-spin"></div>
            ) : (
              <>
                <span>Iniciar Sesión</span>
                <ArrowRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />
              </>
            )}
            
            {/* Button hover effect */}
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-in-out z-[-1]"></div>
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-xs text-slate-500">
            *Modo Demo: Puedes ingresar con cualquier credencial para probar el sistema.
          </p>
        </div>
      </div>
    </div>
  );
}
