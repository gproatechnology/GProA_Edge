import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { SpinnerGap, CheckCircle, Warning } from "@phosphor-icons/react";

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const calledRef = useRef(false); // Guard against React StrictMode double-execution

  useEffect(() => {
    if (calledRef.current) return; // Already called, skip
    calledRef.current = true;

    const processCallback = async () => {
      if (code) {
        try {
          const userId = localStorage.getItem("google_auth_user_id") || "gproatechnology";
          const origin = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? window.location.origin 
            : 'http://localhost:3000';
          const redirectUri = `${origin}/google-callback`;
          
          console.log("GoogleCallback: calling backend with user_id=", userId);
          const res = await axios.get(`${API}/google-drive/callback?code=${code}&state=${state}&user_id=${userId}&redirect_uri=${encodeURIComponent(redirectUri)}`);
          
          console.log("GoogleCallback: backend response =", JSON.stringify(res.data));
          
          if (window.opener) {
            window.opener.postMessage({ 
              type: "GOOGLE_AUTH_SUCCESS",
              user: res.data.user || {}
            }, "*");
          }
          
          setTimeout(() => { window.close(); }, 500);
        } catch (e) {
          console.error("Error in callback processing:", e);
          if (window.opener) {
            window.opener.postMessage({ type: "GOOGLE_AUTH_SUCCESS", user: {} }, "*");
          }
          setTimeout(() => { window.close(); }, 1000);
        }
      }
    };
    processCallback();
  }, [code]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background p-8 text-center">
      {!code ? (
        <div className="space-y-4">
          <Warning className="w-16 h-16 text-amber-500 mx-auto" />
          <h1 className="text-2xl font-bold">Error de Autenticación</h1>
          <p className="text-muted-foreground">No se recibió un código válido de Google.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="relative">
             <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
             <SpinnerGap className="w-20 h-20 text-primary animate-spin relative" />
          </div>
          <h1 className="text-2xl font-bold">Conectando con Google Drive</h1>
          <p className="text-muted-foreground">Estamos procesando tu autorización. Esta ventana se cerrará automáticamente.</p>
        </div>
      )}
    </div>
  );
}
