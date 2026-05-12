import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { ChatCircleDots, PaperPlaneTilt, X, Minus, Robot, User, SpinnerGap, GoogleLogo } from "@phosphor-icons/react";
import GoogleDriveForm from "./GoogleDriveForm";

export default function ChatAssistant({ projectId, user }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState([
    { role: "assistant", content: "¡Hola! Soy tu asistente experto de GProA EDGE. ¿En qué puedo ayudarte con este proyecto?" }
  ]);
  const [loading, setLoading] = useState(false);
  const [showDriveForm, setShowDriveForm] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userMsg = { role: "user", content: message };
    setHistory(prev => [...prev, userMsg]);
    setMessage("");

    // Magic Word Check
    if (message.toLowerCase().trim() === "google drive") {
      setShowDriveForm(true);
      setHistory(prev => [...prev, { role: "assistant", content: "¡Excelente! He activado el módulo de conexión con Google Drive. Por favor, completa la configuración a continuación:" }]);
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/projects/${projectId}/chat`, {
        message: userMsg.content,
        history: history.slice(-5) // Send some history for context
      });

      setHistory(prev => [...prev, { role: "assistant", content: res.data.response }]);
    } catch (e) {
      console.error("Chat error:", e);
      setHistory(prev => [...prev, { role: "assistant", content: "Lo siento, hubo un error al procesar tu mensaje. Verifica tu conexión." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary text-primary-foreground rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-all z-50 animate-bounce-subtle"
      >
        <ChatCircleDots weight="fill" className="w-7 h-7" />
      </button>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 w-[380px] bg-card border border-border rounded-2xl shadow-2xl z-50 flex flex-col transition-all overflow-hidden ${isMinimized ? 'h-14' : 'h-[550px]'}`}>
      {/* Header */}
      <div className="p-4 bg-primary text-primary-foreground flex items-center justify-between cursor-pointer" onClick={() => setIsMinimized(!isMinimized)}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
            <Robot weight="fill" className="w-5 h-5" />
          </div>
          <span className="font-bold text-sm">Asistente Experto EDGE</span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }} className="p-1 hover:bg-white/10 rounded-md">
            <Minus weight="bold" className="w-4 h-4" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); setIsOpen(false); }} className="p-1 hover:bg-white/10 rounded-md">
            <X weight="bold" className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/20">
            {history.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex gap-2 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-1 ${msg.role === 'user' ? 'bg-secondary' : 'bg-primary/10 text-primary'}`}>
                    {msg.role === 'user' ? <User weight="bold" className="w-4 h-4" /> : <Robot weight="fill" className="w-4 h-4" />}
                  </div>
                  <div className={`p-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user' 
                      ? 'bg-primary text-primary-foreground rounded-tr-none' 
                      : 'bg-card border border-border rounded-tl-none shadow-sm'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start animate-pulse">
                <div className="bg-card border border-border p-3 rounded-2xl rounded-tl-none flex items-center gap-2">
                  <SpinnerGap className="w-4 h-4 animate-spin text-primary" />
                  <span className="text-xs text-muted-foreground">Pensando...</span>
                </div>
              </div>
            {showDriveForm && (
              <div className="flex justify-start">
                <div className="bg-card border border-primary/20 p-4 rounded-2xl rounded-tl-none shadow-xl w-full max-w-[95%]">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-xs font-bold text-primary flex items-center gap-2">
                      <GoogleLogo weight="bold" /> Google Drive Integration
                    </span>
                    <button onClick={() => setShowDriveForm(false)} className="p-1 hover:bg-muted rounded-md text-muted-foreground">
                      <X weight="bold" className="w-3 h-3" />
                    </button>
                  </div>
                  <GoogleDriveForm projectId={projectId} user={user} onComplete={() => setShowDriveForm(false)} />
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSend} className="p-4 border-t border-border bg-card">
            <div className="relative">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Escribe tu duda aquí..."
                className="w-full bg-muted border-none rounded-xl py-3 pl-4 pr-12 text-sm focus:ring-2 focus:ring-primary/20 transition-all"
              />
              <button
                type="submit"
                disabled={!message.trim() || loading}
                className="absolute right-2 top-1.5 p-1.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-all"
              >
                <PaperPlaneTilt weight="fill" className="w-5 h-5" />
              </button>
            </div>
            <p className="text-[10px] text-center text-muted-foreground mt-3">
              ConsultorÍA EDGE v2.0 - IA asistida por contexto real
            </p>
          </form>
        </>
      )}
    </div>
  );
}
