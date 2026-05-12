import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { SpinnerGap, CheckCircle, Warning } from "@phosphor-icons/react";

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const code = searchParams.get("code");
  const state = searchParams.get("state"); // Optional: verify state if needed

  useEffect(() => {
    const processCallback = async () => {
      if (code) {
        try {
          // Get user_id from the state or local storage if we passed it
          const userId = localStorage.getItem("google_auth_user_id");
          const origin = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? window.location.origin 
            : 'http://localhost:3000';
          const redirectUri = `${origin}/google-callback`;
          
          const res = await axios.get(`${API}/google-drive/callback?code=${code}&state=${state}&user_id=${userId}&redirect_uri=${encodeURIComponent(redirectUri)}`);
          
          // Notify the opener window using a more permissive origin for dev
          if (window.opener) {
            window.opener.postMessage({ 
              type: "GOOGLE_AUTH_SUCCESS",
              user: res.data.user
            }, "*");
          }
          
          // Explicitly close the window from within
          setTimeout(() => {
            window.close();
          }, 500);
        } catch (e) {
          console.error("Error in callback processing:", e);
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
