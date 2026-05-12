import React, { useState } from "react";
import axios from "axios";
import { Lock, Mail, ArrowRight } from "lucide-react";
import logoEosis from "../assets/branding/logo_eosis.png";
import logoEdge from "../assets/branding/logo_edge.png";
import avatarLuis from "../assets/branding/avatar_luis.png";
import avatarJorge from "../assets/branding/avatar_jorge.png";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    // Limpieza de seguridad para asegurar que no hay datos viejos (como el nombre "CEO")
    localStorage.removeItem("gproa_chat_name");
    localStorage.removeItem("gproa_user");
    
    try {
      // Usar localhost explícitamente para evitar problemas de IP privada con Google
      const origin = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? window.location.origin 
        : 'http://localhost:3000';
      
      const redirectUri = `${origin}/google-callback`;
      // Usar 'Luis' como ID para que coincida con el perfil que cargamos después
      const res = await axios.get(`${API}/google-drive/auth-url?user_id=Luis&redirect_uri=${encodeURIComponent(redirectUri)}`);
      
      const authWindow = window.open(res.data.auth_url, "Login con Google", "width=600,height=700");
      
      // Escuchar el mensaje de éxito
      const handleAuthMessage = (event) => {
        if (event.data.type === "GOOGLE_AUTH_SUCCESS") {
          const googleUser = event.data.user || {};
          console.log('DEBUG: Datos de Google ->', JSON.stringify(googleUser, null, 2));
          
          // FORZADO DE IDENTIDAD: Si entramos por Google, asumimos rango de CEO para ti
          const isCEO = googleUser.email?.includes("gproatechnology") || true; 
          
          onLogin({ 
            name: googleUser.name || "CEO GProA", 
            role: isCEO ? "CEO" : "consultant", 
            avatar: googleUser.name ? googleUser.name.charAt(0) : "G", 
            image: googleUser.picture || null, // Si no hay foto, el Sidebar usará la inicial
            email: googleUser.email
          });
          window.removeEventListener("message", handleAuthMessage);
        }
      };
      window.addEventListener("message", handleAuthMessage);
      
    } catch (e) {
      console.error("Google Login Error:", e);
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Identificar perfil basado en el email
    const user = email.toLowerCase().includes("jorge") 
      ? { name: "Jorge", role: "manager", avatar: "J", image: avatarJorge }
      : { name: "Luis", role: "consultant", avatar: "L", image: avatarLuis };

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
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)]"></div>

      {/* Animated Background Logos (Logo Cloud) */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* EOSIS Cluster */}
        <img src={logoEosis} alt="" className="absolute top-[5%] left-[10%] h-48 opacity-[0.02] grayscale brightness-200 animate-float-slow" />
        <img src={logoEosis} alt="" className="absolute top-[60%] left-[5%] h-32 opacity-[0.01] grayscale brightness-200 animate-float-slower" style={{ animationDelay: '-5s' }} />
        <img src={logoEosis} alt="" className="absolute top-[20%] right-[15%] h-40 opacity-[0.015] grayscale brightness-200 animate-float-slow" style={{ animationDelay: '-10s' }} />
        <img src={logoEosis} alt="" className="absolute bottom-[5%] left-[25%] h-56 opacity-[0.02] grayscale brightness-200 animate-float-slower" style={{ animationDelay: '-15s' }} />
        
        {/* EDGE Cluster */}
        <img src={logoEdge} alt="" className="absolute top-[40%] right-[5%] h-32 opacity-[0.02] grayscale brightness-200 animate-float-slower" />
        <img src={logoEdge} alt="" className="absolute top-[15%] left-[20%] h-24 opacity-[0.01] grayscale brightness-200 animate-float-slow" style={{ animationDelay: '-7s' }} />
        <img src={logoEdge} alt="" className="absolute bottom-[20%] right-[10%] h-40 opacity-[0.02] grayscale brightness-200 animate-float-slower" style={{ animationDelay: '-12s' }} />
        <img src={logoEdge} alt="" className="absolute bottom-[40%] left-[40%] h-20 opacity-[0.01] grayscale brightness-200 animate-float-slow" style={{ animationDelay: '-18s' }} />
        <img src={logoEdge} alt="" className="absolute top-[80%] left-[80%] h-36 opacity-[0.015] grayscale brightness-200 animate-float-slower" style={{ animationDelay: '-22s' }} />
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes float-slow {
          0%, 100% { transform: translate(0, 0) rotate(0deg) scale(1); }
          50% { transform: translate(30px, -40px) rotate(8deg) scale(1.05); }
        }
        @keyframes float-slower {
          0%, 100% { transform: translate(0, 0) rotate(0deg) scale(1); }
          50% { transform: translate(-40px, 30px) rotate(-8deg) scale(0.95); }
        }
        .animate-float-slow {
          animation: float-slow 25s ease-in-out infinite;
        }
        .animate-float-slower {
          animation: float-slower 35s ease-in-out infinite;
        }
      `}} />

      <div className="relative z-10 w-full max-w-md p-8 m-4 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl">
        
        {/* Header */}
        <div className="flex flex-col items-center mb-10">
          <div className="flex gap-6 items-center mb-8">
            <img src={logoEosis} alt="EOSIS" className="h-16 object-contain" />
            <div className="h-12 w-[1px] bg-white/20"></div>
            <img src={logoEdge} alt="EDGE" className="h-12 object-contain" />
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
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-in-out z-[-1]"></div>
          </button>
        </form>

        <div className="flex items-center gap-4 my-8">
          <div className="h-[1px] flex-1 bg-white/10"></div>
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">O también</span>
          <div className="h-[1px] flex-1 bg-white/10"></div>
        </div>

        {/* Google Login Button (The new bottom position) */}
        <button
          onClick={handleGoogleLogin}
          disabled={isLoading}
          className="w-full py-3.5 bg-white hover:bg-slate-100 text-slate-900 font-bold text-sm rounded-xl transition-all flex items-center justify-center gap-3 shadow-xl active:scale-95"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continuar con Google
        </button>

        <div className="mt-8 text-center">
          <p className="text-xs text-slate-500">
            *Modo Demo: Puedes ingresar con cualquier credencial para probar el sistema.
          </p>
        </div>
      </div>
    </div>
  );
}
