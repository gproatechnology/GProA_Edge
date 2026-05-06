import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

export default function ProjectAnalytics({ projects }) {
  const [isReady, setIsReady] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    // Un retraso mayor asegura que incluso en sistemas lentos el layout esté listo
    const timer = setTimeout(() => {
      setIsReady(true);
      // Forzamos un evento de resize para que Recharts recalcule dimensiones
      window.dispatchEvent(new Event('resize'));
    }, 800);
    
    return () => clearTimeout(timer);
  }, []);

  // Filtrar proyectos que tienen datos suficientes para calcular el ratio
  const data = projects
    .filter(p => p.square_meters > 0 && p.annual_consumption_kwh > 0)
    .map(p => ({
      name: p.name.length > 12 ? p.name.substring(0, 12) + '...' : p.name,
      ratio: parseFloat((p.annual_consumption_kwh / p.square_meters).toFixed(1)),
      priority: p.priority || 'Baja',
      fullName: p.name
    }))
    .sort((a, b) => b.ratio - a.ratio); // Ordenar de mayor a menor consumo

  if (data.length === 0) return null;

  const getBarColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'crítica':
      case 'critica': return '#ef4444'; // red-500
      case 'alta': return '#f97316';    // orange-500
      case 'media': return '#3b82f6';    // blue-500
      default: return '#6366f1';        // Indigo 500 (Primary)
    }
  };

  return (
    <div className="bg-card border border-border rounded-3xl p-6 mb-8 animate-fadeIn shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Intensidad Energética
          </h2>
          <p className="text-xs text-muted-foreground mt-1">Comparativa de consumo por metro cuadrado (kWh/m²)</p>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Crítica</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Eficiente</span>
          </div>
        </div>
      </div>

      <div 
        ref={containerRef}
        className="relative w-full overflow-hidden"
        style={{ minHeight: '280px' }}
      >
        {isReady ? (
          <div className="w-full h-full" style={{ minWidth: 0, minHeight: '280px' }}>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="opacity-10" />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fill: 'currentColor' }}
                  className="text-muted-foreground"
                  interval={0}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fill: 'currentColor' }}
                  className="text-muted-foreground"
                />
                <Tooltip 
                  cursor={{ fill: 'currentColor', opacity: 0.05 }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-popover text-popover-foreground border border-border p-3 rounded-xl shadow-xl backdrop-blur-md">
                          <p className="text-xs font-bold mb-1">{payload[0].payload.fullName}</p>
                          <p className="text-sm font-mono text-primary font-bold">
                            {payload[0].value} <span className="text-[10px] opacity-60">kWh/m²</span>
                          </p>
                          <p className="text-[10px] opacity-60 mt-1 uppercase tracking-wider font-bold">Prioridad: {payload[0].payload.priority}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="ratio" radius={[6, 6, 0, 0]} barSize={32}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getBarColor(entry.priority)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="w-full h-[280px] animate-skeleton rounded-2xl flex items-center justify-center bg-muted/20">
             <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin opacity-20" />
          </div>
        )}
      </div>
    </div>
  );
}
