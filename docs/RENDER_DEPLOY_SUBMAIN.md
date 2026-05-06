# 🚀 Despliegue Automático en Render – Rama `submain`

## **📋 Información General**

Este archivo contiene instrucciones específicas para desplegar la rama **`submain`** del proyecto **GProA_Edge** en Render.com.

### **✨ Novedades en `submain`**
- ✅ **Modo Demo Automático:** No requiere MongoDB Atlas ni OpenAI API key
- ✅ **SQLite integrado:** Base de datos local en `backend/data/gproa_edge.db`
- ✅ **Respuestas Mock AI:** Clasificación, extracción y cálculo de áreas simulados
- ✅ **Zero-Config:** Todo preconfigurado en `render.yaml`
- ✅ **Dependencias limpias:** Solo lo necesario (sin paquetes Google/Emergent conflictivos)

---

## **🔧 Configuración Automática (render.yaml)**

El archivo `render.yaml` ya está configurado para despliegue automático. Solo necesitas:

### **Backend Service Variables (AUTOMÁTICAS)**
| Variable | Valor | Estado |
|----------|-------|--------|
| `MONGO_URL` | *(vacío)* | **Sin configurar** → Usa SQLite |
| `OPENAI_API_KEY` | *(vacío)* | **Sin configurar** → Usa Mock AI |
| `DEMO_MODE` | `true` | ✅ Fijado en blueprint |
| `DB_NAME` | `gproa_edge` | ✅ Fijado en blueprint |
| `CORS_ORIGINS` | `*` | ✅ Fijado en blueprint |
| `FRONTEND_URL` | Auto-detectado | ✅ Vinculado al frontend |

### **Frontend Service Variables (AUTOMÁTICAS)**
| Variable | Valor | Estado |
|----------|-------|--------|
| `REACT_APP_BACKEND_URL` | Auto-detectado | ✅ Vinculado al backend |

---

## **🔄 Pasos de Despliegue (Muy Sencillo)**

### **1. Pre-requisitos**
- Cuenta en [Render.com](https://render.com)
- Repositorio GitHub conectado a Render (ya debe estar)
- Rama `submain` disponible en GitHub

### **2. Crear Servicios en Render**

#### **Opción A: Usar Blueprint (RECOMENDADO)**
1. En Render Dashboard → **New** → **Blueprint**
2. Conecta tu repositorio `gproatechnology/GProA_EOSIS_Edge`
3. Selecciona la rama **`submain`**
4. Render detectará automáticamente el `render.yaml`
5. Haz clic en **"Apply Blueprint"**
6. ⚡ ¡Listo! Render creará ambos servicios (backend + frontend) con toda la configuración

#### **Opción B: Manual (si Blueprint no está disponible)**
##### **Backend:**
1. **New** → **Web Service**
2. Conecta repo → rama `submain`
3. Nombre: `gproa-edge-backend`
4. Environment: **Python 3**
5. Build Command:
   ```bash
   cd backend && pip install -r requirements.txt
   ```
6. Start Command:
   ```bash
   cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
7. **Environment Variables:**
   ```
   DEMO_MODE=true
   DB_NAME=gproa_edge
   CORS_ORIGINS=*
   # (NO agregues MONGO_URL ni OPENAI_API_KEY)
   ```
8. Create Web Service

##### **Frontend:**
1. **New** → **Web Service**
2. Conecta repo → rama `submain` (mismo repo)
3. Nombre: `gproa-edge-frontend`
4. Environment: **Node**
5. Build Command:
   ```bash
   cd frontend && npm install && npm run build
   ```
6. Start Command:
   ```bash
   npx serve -s build -l $PORT
   ```
7. **Environment Variables:**
   ```
   REACT_APP_BACKEND_URL=https://gproa-edge-backend.onrender.com
   ```
   *(Reemplaza con tu URL real después de crear el backend)*
8. Create Web Service

---

## **🧪 Verificación Post-Despliegue**

### **1. Backend Health Check**
```bash
# Reemplaza <backend-url> con la URL de tu servicio backend
curl https://<backend-url>.onrender.com/api/
```

**Respuesta esperada:**
```json
{
  "message": "EDGE Document Processor API v2"
}
```

### **2. Test Completo (Demo Mode)**
1. Abre el frontend: `https://<frontend-url>.onrender.com`
2. **Crear Proyecto:**
   - Nombre: "Demo Project"
   - Tipología: "Oficina"
3. **Subir Archivo:**
   - Crea un archivo .txt con contenido de ejemplo:
     ```
     Luminaria LED Philips 36W 3600 lumens
     Modelo: LED-36W-4000K
     ```
   - Úsalo como "ficha técnica"
4. **Procesar** → Verás datos clasificados como EEM22 (energía, iluminación)
5. **Exportar Excel/PDF** → Descarga exitosa

### **3. Logs en Render**
- Backend logs: Render Dashboard → Service → Logs
- Deberías ver: `>>> Initializing SQLite connection...` y `>>> SQLite database ready`
- Esto confirma que SQLite está funcionando (sin MongoDB)

---

## **🔍 Troubleshooting**

### **Error: "No module named 'aiosqlite'"**
```bash
# En Render, el build command ya instala requirements.txt
# Si falla, verifica que aiosqlite==0.20.0 esté en backend/requirements.txt
```

### **Error: "threads can only be started once"**
❌ **No debería ocurrir** – Ya lo corregimos con conexión persistente.
Si ves este error:
1. Verifica que el código en `backend/server.py` tenga el método `_ensure_sqlite()`
2. Asegúrate de que `UnifiedDB` tenga `self.conn` como atributo lazy-init

### **Backend no arranca (puerto)**
El start command usa `$PORT` (variable de entorno de Render). ✅ Correcto.

### **CORS errors**
- En demo: `CORS_ORIGINS=*` → Permite todo
- En producción: Cambia a tu dominio frontend específico

### **Archivos no se suben / procesan**
1. Verifica que `backend/data/` es writable (debería serlo por defecto)
2. Revisa logs en Render → busca errores de permisos
3. En demo mode, el archivo `data/gproa_edge.db` se crea automáticamente

---

## **📊 Comportamiento Esperado en Demo Mode**

### **Sin API Keys (Config Actual)**
| Componente | Comportamiento |
|------------|----------------|
| **Base de Datos** | SQLite local → archivo en filesystem |
| **Clasificación** | Mock basado en palabras clave (luminaria→EEM22, hvac→EEM09, plano→DESIGN) |
| **Extracción Watts/Lumens** | Regex simple, extrae números encontrados |
| **Procesadores Especializados** | Datos de ejemplo hardcodeados (luminarias, equipos HVAC, paneles solares) |
| **Cálculo de Áreas** | Lista predefinida de espacios (Oficina A, Sala, etc.) |
| **Validación WBS** | Funciona normalmente (determinística, no AI) |
| **KPIs** | Calculados con datos mock |
| **Exportación** | Excel y PDF funcionan con datos mock |

### **Con API Keys (cuando se configure)**
1. Set `OPENAI_API_KEY` en Render Environment Variables
2. Set `MONGO_URL` (MongoDB Atlas) si se quiere BD real
3. Comportamiento cambia automáticamente a OpenAI GPT-4o + MongoDB

---

## **🔄 Cambios en Rama `submain` vs `main`**

| Aspecto | `main` | `submain` |
|---------|--------|-----------|
| Base de datos | Solo MongoDB | SQLite (fallback) + MongoDB (si configurado) |
| IA | Solo OpenAI GPT-4o | Mock AI (demo) + OpenAI (si configurado) |
| Dependencias | motor, pymongo, openai | + aiosqlite (ya estaba) |
| Configuración | Requiere secrets | Zero-config (demo) |
| Deploy en Render | Con secrets | Sin secrets |

---

## **🛠️ Para Producción Real (no demo)**

Cuando estés listo para producción:

1. **Configurar MongoDB Atlas:**
   ```
   MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/gproa_edge?retryWrites=true&w=majority
   ```

2. **Configurar OpenAI:**
   ```
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
   ```

3. **Deshabilitar Demo Mode (opcional):**
   ```
   DEMO_MODE=false
   ```

4. **Actualizar CORS:**
   ```
   CORS_ORIGINS=https://tudominio.com
   ```

5. **Redeployar** en Render (mismo servicio, solo cambian env vars)

---

## **📁 Archivos Modificados en `submain`**

```
backend/server.py          → UnifiedDB, SQLite lazy init, demo mode, mock AI
backend/edge_processors.py  → Procesadores mock para EEM22, EEM09, EEM16, WEM01/02
backend/requirements.txt    → Ya incluía aiosqlite, sin cambios
.env.example               → Actualizado con DEMO_MODE
render.yaml                → Actualizado para demo auto (OPENAI vacío, DEMO_MODE=true)
```

---

## **✅ Checklist de Despliegue**

- [ ] Rama `submain` pusheada a GitHub ✓
- [ ] Render Blueprint aplicado (o servicios creados manualmente)
- [ ] Backend service: Python 3, build/start commands correctos
- [ ] Frontend service: Node, build/start commands correctos
- [ ] Variables de entorno: **NO** configurar `MONGO_URL` ni `OPENAI_API_KEY`
- [ ] Backend health check: `GET /api/` responde 200
- [ ] Frontend carga correctamente
- [ ] Flujo completo: crear proyecto → subir archivo → procesar → exportar

---

## **🎯 Resultado**

Una vez desplegado, tendrás una **aplicación EDGE fully funcional** funcionando en Render sin haber configurado ninguna API key ni base de datos externa. Perfecta para demos, pruebas o conceptos de validación.

**¿Dudas?** Revisa los logs en Render Dashboard → cada servicio tiene su propia sección de logs en tiempo real.
