import React, { useEffect, useState } from "react";
import logoEdge from "../assets/branding/logo_edge.png";

export default function SplashScreen({ onFinish }) {
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    // Start fade out after 2 seconds
    const timer1 = setTimeout(() => {
      setFadeOut(true);
    }, 2000);

    // Call onFinish after fade out animation completes (2.5s total)
    const timer2 = setTimeout(() => {
      if (onFinish) onFinish();
    }, 2500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, [onFinish]);

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-900 text-white transition-opacity duration-500 ${
        fadeOut ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className="flex flex-col items-center">
        <div className="h-24 w-auto mb-8 animate-fadeIn">
          <img src={logoEdge} alt="EDGE Logo" className="h-full object-contain" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
          Assistant Pro
        </h1>
        <p className="text-slate-400 tracking-widest uppercase text-xs font-bold">
          GProA EDGE Certification
        </p>
      </div>
      
      <div className="absolute bottom-12 flex flex-col items-center">
        <div className="w-48 h-1 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-emerald-500 rounded-full animate-[loading_2s_ease-in-out]"></div>
        </div>
        <p className="mt-4 text-xs text-slate-500 font-mono">Inicializando entorno...</p>
      </div>

    </div>
  );
}
