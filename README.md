# GProA EDGE — Plataforma de Certificación Inteligente

[![Tests](https://github.com/gproatechnology/GProA_Edge/workflows/CI/badge.svg)](https://github.com/gproatechnology/GProA_Edge/actions)
[![Backend](https://img.shields.io/badge/Backend-100%25-brightgreen.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-95%25-brightgreen.svg)]()
[![Version](https://img.shields.io/badge/Version-2.0.0-blue.svg)]()

> **Outcome**: Reducción del tiempo de documentación para certificación EDGE en hasta **80%**, con mayor confiabilidad de auditoría y velocidad de cumplimiento.

**GProA EDGE** es una plataforma profesional que transforma datos de construcción no estructurados en entradas de certificación estructuradas y auditables. Combina inteligencia artificial, integración con Google Drive y un dashboard ejecutivo en tiempo real para equipos de consultoría de edificios verdes.

---

## ✨ Funcionalidades Principales

- 📋 **Gestión de Proyectos**: Administración centralizada de proyectos y tipologías de certificación EDGE.
- 🧠 **Procesamiento con IA**: Clasificación y extracción técnica ultrarrápida con Gemini Flash (Watts, Lúmenes, áreas, equipos HVAC).
- 🔗 **Sincronización con Google Drive**: Descarga automática de archivos desde carpetas del Drive del usuario mediante OAuth2.
- 🤖 **Motor de Auditoría Automática**: Al sincronizar, cada archivo es clasificado, parseado y analizado sin intervención manual.
- 📊 **Dashboard en Tiempo Real**: KPIs de CO2, archivos procesados y eficiencia energética actualizados automáticamente.
- 🔐 **SSO con Google**: Autenticación con cuenta de Google, detección automática de rol (CEO / Consultor).
- 🎨 **Identidad de Marca Premium**: Logo Cloud animado en login, branding EOSIS y EDGE integrado.
- 📤 **Exportación Enterprise**: Generación de Excel estructurado listo para entrega a certificadores.
- 💬 **Asistente IA Contextual**: Consultor experto integrado con reglas estrictas y directas, alimentado por el estado real de cada proyecto en base de datos.

---

## 🛠 Stack Tecnológico

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite)
![MongoDB](https://img.shields.io/badge/MongoDB-4DB33D?style=for-the-badge&logo=mongodb)
![Gemini](https://img.shields.io/badge/Google-Gemini-blue?style=for-the-badge&logo=google)
![Google Drive](https://img.shields.io/badge/Google_Drive-4285F4?style=for-the-badge&logo=googledrive)

| Capa | Tecnología |
|------|------------|
| **Backend** | FastAPI + Uvicorn + Python 3.12+ |
| **Frontend** | React 18 + Tailwind CSS + Radix UI |
| **Base de Datos** | SQLite (local) / MongoDB Atlas (producción) |
| **IA** | Google Gemini Flash 1.5 |
| **Drive API** | Google Drive API v3 + OAuth2 |
| **Parsers** | pdfplumber, ezdxf, openpyxl |

---

## 🏗️ Arquitectura del Sistema

### Vista General de Componentes

```mermaid
graph TB
    subgraph FRONTEND["Frontend (React 18 + Tailwind)"]
        UI[Componentes UI]
        ST[State Management]
        AX[Axios Client]
    end
    
    subgraph BACKEND["Backend (FastAPI + Python)"]
        API[API Router]
        MID[Middleware Auth]
        SV[Servicios]
    end
    
    subgraph EXTERNAL["Servicios Externos"]
        GD[Google Drive API]
        GM[Gemini AI]
    end
    
    subgraph DATA["Capa de Datos"]
        UDB[UnifiedDB]
        SQL[(SQLite)]
        MON[(MongoDB Atlas)]
    end
    
    FRONTEND -->|HTTP/REST| BACKEND
    BACKEND --> EXTERNAL
    BACKEND --> DATA
    
    classDef frontend fill:#e3f2fd,stroke:#1565c0
    classDef backend fill:#e8f5e9,stroke:#2e7d32
    classDef external fill:#fff3e0,stroke:#f57c00
    classDef data fill:#f3e5f5,stroke:#7b1fa2
    class FRONTEND,BACKEND,EXTERNAL,DATA frontend
```

### Flujo de Datos: Drive → Dashboard

```mermaid
flowchart TD
    subgraph INPUT["Entrada de Datos"]
        A[Usuario sincroniza carpeta Google Drive]
    end
    
    subgraph SYNC["Capa de Sincronización"]
        B[GoogleDriveService descarga archivos]
        C[Registro en DB: status='pending']
    end
    
    subgraph AUDIT["Motor de Auditoría"]
        D[AuditService detecta medida EDGE]
        E{Tipo de archivo}
        E -->|PDF| F[PDF Parser extrae texto]
        E -->|DXF/DWG| G[CAD Parser extrae geometría]
        E -->|XLSX| H[Excel Parser extrae tablas]
    end
    
    subgraph AI["Procesamiento IA"]
        F & G & H --> I[EdgeProcessor analiza con Gemini]
        I --> J[Actualiza DB: watts, lumens, COP]
    end
    
    subgraph OUTPUT["Salida"]
        K[Recalcula métricas proyecto]
        L[Dashboard tiempo real]
    end
    
    A --> B --> C --> D --> E
    E --> F
    E --> G
    E --> H
    F --> I
    G --> I
    H --> I
    I --> J --> K --> L
    
    classDef startEnd fill:#e1f5fe,stroke:#01579b
    classDef process fill:#fff3e0,stroke:#e65100
    classDef ai fill:#ffebee,stroke:#c62828
    classDef db fill:#f3e5f5,stroke:#4a148c
    class A,L startEnd
    class B,C,D,K process
    class I ai
    class J db
```

### Arquitectura de API Endpoints

```mermaid
graph LR
    subgraph CLIENT["Cliente Frontend"]
        REQ[React App]
    end
    
    subgraph API["FastAPI Router"]
        ROUTER[api_router.py]
    end
    
    subgraph ENDPOINTS["Endpoints"]
        PRO[projects.py]
        FIL[files.py]
        PROC[processing.py]
        GD[google_drive.py]
        EXP[exports.py]
        ASST[assistant.py]
        ANL[analysis.py]
        RUL[rules.py]
    end
    
    REQ --> ROUTER
    ROUTER --> PRO
    ROUTER --> FIL
    ROUTER --> PROC
    ROUTER --> GD
    ROUTER --> EXP
    ROUTER --> ASST
    ROUTER --> ANL
    ROUTER --> RUL
    
    classDef client fill:#e3f2fd,stroke:#1565c0
    classDef router fill:#e8f5e9,stroke:#2e7d32
    classDef endpoint fill:#fff8e1,stroke:#f9a825
    class REQ client
    class ROUTER router
    class PRO,FIL,PROC,GD,EXP,ASST,ANL,RUL endpoint
```

### Flujo de Autenticación SSO con Google

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as Backend
    participant GD as Google OAuth
    participant DB as UnifiedDB
    
    U->>FE: Click "Iniciar con Google"
    FE->>API: GET /api/google-drive/auth-url
    API->>GD: Solicitar auth URL
    GD-->>API: Return auth URL
    API-->>FE: Redirect a Google
    
    FE->>GD: Redirigir a Google Login
    GD->>U: Mostrar login Google
    U->>GD: Ingresar credenciales
    GD-->>FE: Callback with code
    
    FE->>API: POST /api/google-drive/callback
    API->>GD: Exchange code por tokens
    GD-->>API: Return access_token
    
    API->>DB: Save google_tokens
    API->>FE: Return user info + role
    
    FE->>U: Mostrar Dashboard
```

### Arquitectura de Base de Datos Unificada

```mermaid
erDiagram
    PROJECTS ||--o{ FILES : contains
    PROJECTS {
        string id PK
        string name
        string typology
        datetime created_at
        int file_count
        int processed_count
        string priority
        float square_meters
        float annual_consumption_kwh
        float efficiency
        float co2_reduction
        float energy_savings
    }
    
    FILES {
        string id PK
        string project_id FK
        string filename
        int file_size
        string content_text
        string status
        string category_edge
        string measure_edge
        string doc_type
        float confidence
        float watts
        float lumens
        string tipo_equipo
        string marca
        string modelo
        json areas
        json specialized_data
        datetime uploaded_at
        float cost
        float consumption_kwh
        string file_path
    }
    
    GOOGLE_TOKENS {
        string user_id PK
        string token_json
        datetime updated_at
    }
    
    SYNC_LOGS {
        string id PK
        string project_id FK
        string user_id
        datetime timestamp
        json files_synced
        string status
    }
```

### Flujo de Procesamiento de Archivos

```mermaid
flowchart TB
    subgraph DETECT["1. Detección de Medida"]
        A[Nombre archivo] --> B[AuditService.detect_measure]
        B --> C{EEM22?}
        C -->|Yes| D[process_eem22_luminaires]
        C -->|No| E{EEM09?}
        E -->|Yes| F[process_eem09_hvac]
        E -->|No| G{EEM16?}
        G -->|Yes| H[process_eem16_renewables]
        G -->|No| I{WEM01?}
        I -->|Yes| J[process_water_fixtures]
        I -->|No| K{Unifilar?}
        K -->|Yes| L[process_unifilar_diagram]
        K -->|No| M[Procesador General]
    end
    
    subgraph PARSE["2. Parsing"]
        D --> N[PDF/DXF Parser]
        F --> N
        H --> N
        J --> N
        L --> N
        M --> N
    end
    
    subgraph AI["3. Análisis IA"]
        N --> O[Gemini Flash 1.5]
        O --> P[JSON estructurado]
    end
    
    subgraph SAVE["4. Persistencia"]
        P --> Q[files_update_one]
        Q --> R[recalculate_project_metrics]
    end
    
    classDef detect fill:#e8f5e9,stroke:#2e7d32
    classDef parse fill:#e3f2fd,stroke:#1565c0
    classDef ai fill:#fff3e0,stroke:#f57c00
    classDef save fill:#f3e5f5,stroke:#7b1fa2
    class A,B,C,D,E,F,G,H,I,J,K,L,M detect
    class N parse
    class O,P ai
    class Q,R save
```

### Componentes del Frontend

```mermaid
graph TD
    subgraph APP["App.js"]
        ROOT[Root Component]
    end
    
    subgraph AUTH["Autenticación"]
        LOG[Login.js]
        SPL[SplashScreen.js]
        GCB[GoogleCallback.js]
    end
    
    subgraph LAYOUT["Layout"]
        SID[Sidebar.js]
    end
    
    subgraph DASHBOARD["Dashboard"]
        PD[ProjectDashboard.js]
        PA[ProjectAnalytics.js]
    end
    
    subgraph PROJECT["Proyecto"]
        PRD[ProjectDetail.js]
        FUP[FileUploadTab.js]
        EDT[ExtractedDataTab.js]
        ECT[EdgeComplianceTab.js]
        LFT[LoadFlowTab.js]
    end
    
    subgraph AI["Inteligencia"]
        CHA[ChatAssistant.js]
    end
    
    ROOT --> LOG
    ROOT --> SPL
    SPL --> GCB
    ROOT --> SID
    SID --> PD
    PD --> PA
    PD --> PRD
    PRD --> FUP
    PRD --> EDT
    PRD --> ECT
    PRD --> LFT
    PRD --> CHA
    
    classDef auth fill:#ffebee,stroke:#c62828
    classDef layout fill:#e8f5e9,stroke:#2e7d32
    classDef dashboard fill:#e3f2fd,stroke:#1565c0
    classDef project fill:#fff8e1,stroke:#f9a825
    classDef ai fill:#f3e5f5,stroke:#7b1fa2
    class LOG,SPL,GCB auth
    class SID layout
    class PD,PA dashboard
    class PRD,FUP,EDT,ECT,LFT project
    class CHA ai
```

### Servicios del Backend

```mermaid
graph TB
    subgraph CORE["Servicios Core"]
        AS[audit_service.py]
        GDS[google_drive_service.py]
        AIS[ai_service.py]
        ASST[assistant_service.py]
    end
    
    subgraph PROCESSORS["Procesadores IA"]
        EP[edge_processors.py]
        E22[process_eem22_luminaires]
        E09[process_eem09_hvac]
        E16[process_eem16_renewables]
        WF[process_water_fixtures]
        UN[process_unifilar_diagram]
    end
    
    subgraph PARSERS["Parsers"]
        PDF[pdf_parser.py]
        CAD[cad_parser.py]
        XLS[xls_parser.py]
    end
    
    subgraph RULES["Reglas"]
        ER[edge_rules.py]
    end
    
    AS --> EP
    AS --> PDF
    AS --> CAD
    AS --> XLS
    EP --> E22
    EP --> E09
    EP --> E16
    EP --> WF
    EP --> UN
    
    classDef core fill:#e8f5e9,stroke:#2e7d32
    classDef processor fill:#fff3e0,stroke:#f57c00
    classDef parser fill:#e3f2fd,stroke:#1565c0
    classDef rules fill:#f3e5f5,stroke:#7b1fa2
    class AS,GDS,AIS,ASST core
    class EP,E22,E09,E16,WF,UN processor
    class PDF,CAD,XLS parser
    class ER rules
```

### Ciclo de Vida de un Proyecto

```mermaid
stateDiagram-v2
    [*] --> CREADO: Crear proyecto
    CREADO --> SIN_ARCHIVOS: Sin archivos
    SIN_ARCHIVOS --> SUBIENDO: Subir archivos
    SUBIENDO --> PROCESANDO: Auto-audit
    PROCESANDO --> COMPLETO: Archivos procesados
    COMPLETO --> EXPORTABLE: Listo para exportar
    EXPORTABLE --> [*]
    
    state CREADO {
        [*] --> NAME: Nombre
        NAME --> TYPOLOGY: Tipología
        TYPOLOGY --> [*]
    }
    
    state SIN_ARCHIVOS {
        [*] --> EMPTY: Dashboard vacío
    }
    
    state SUBIENDO {
        [*] --> UPLOAD: Upload / Drive Sync
    }
    
    state PROCESANDO {
        [*] --> DETECT: Detectar medida
        DETECT --> PARSE: Parsear archivo
        PARSE --> AI: Análisis Gemini
        AI --> SAVE: Guardar resultados
    }
    
    state COMPLETO {
        [*] --> METRICS: Métricas calculadas
        METRICS --> DASHBOARD: Dashboard actualizado
    }
    
    state EXPORTABLE {
        [*] --> EXPORT: Exportar Excel
    }
```

### Métricas del Dashboard en Tiempo Real

```mermaid
flowchart LR
    subgraph INPUTS["Entradas"]
        P[Proyectos]
        F[Archivos]
    end
    
    subgraph CALC["Cálculos"]
        FC[files_count_documents]
        PC[processed_count]
        CR[co2_reduction]
        EF[efficiency]
    end
    
    subgraph OUTPUTS["KPIs Dashboard"]
        TP[Total Proyectos]
        TA[Archivos Totales]
        AP[Archivos Procesados]
        CO[Reducción CO2]
        EF[Eficiencia Energética]
    end
    
    P --> TP
    F --> FC --> TA
    F --> PC --> AP
    CR --> CO
    EF --> EF
    
    classDef input fill:#e3f2fd,stroke:#1565c0
    classDef calc fill:#fff8e1,stroke:#f9a825
    classDef output fill:#e8f5e9,stroke:#2e7d32
    class P,F input
    class FC,PC,CR,EF calc
    class TP,TA,AP,CO,EF output
```

---

## 📁 Estructura del Proyecto

```
GProA_EOSIS_Edge/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   ├── projects.py      # CRUD de proyectos
│   │   │   │   ├── files.py        # Gestión de archivos
│   │   │   │   ├── processing.py   # Procesamiento de archivos
│   │   │   │   ├── google_drive.py  # Sync con Drive
│   │   │   │   ├── analysis.py     # Análisis y métricas
│   │   │   │   ├── exports.py      # Exportación Excel
│   │   │   │   ├── assistant.py   # Chat IA
│   │   │   │   └── rules.py        # Reglas EDGE
│   │   │   └── api_router.py       # Router principal
│   │   ├── services/
│   │   │   ├── audit_service.py           # Motor de auditoría automática
│   │   │   ├── google_drive_service.py  # Sync OAuth2 Drive
│   │   │   ├── edge_processors.py        # Procesadores IA por medida
│   │   │   ├── parsers/                 # PDF, CAD, Excel
│   │   │   ├── ai_service.py            # Servicio de IA
│   │   │   ├── assistant_service.py     # Chat contextual
│   │   │   └── spatial_reasoning/       # Topological Precision Initiative
│   │   │       ├── contour_tracer.py    # Precise polygon reconstruction
│   │   │       ├── hole_detector.py     # Nested polygon detection
│   │   │       ├── topology_validator.py # Geometry integrity validation
│   │   │       ├── polygon_simplifier.py # Douglas-Peucker simplification
│   │   │       ├── boundary_semantics.py  # Shared edge detection
│   │   │       └── precision_metrics.py  # Contour fidelity metrics
│   │   ├── db/
│   │   │   └── database.py         # UnifiedDB (SQLite/MongoDB)
│   │   ├── core/
│   │   │   └── config.py        # Configuración centralizada
│   │   └── main.py             # Entry point FastAPI
│   ├── data/
│   │   ├── credentials.json    # OAuth2 (no incluido en repo)
│   │   └── gproa_edge.db       # SQLite local
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.js              # SSO Google + Logo Cloud
│   │   │   ├── Sidebar.js            # Navegación + Avatar
│   │   │   ├── ProjectDashboard.js  # Dashboard principal
│   │   │   ├── ProjectDetail.js     # Detalle de proyecto
│   │   │   ├── FileUploadTab.js      # Upload de archivos
│   │   │   ├── ExtractedDataTab.js  # Datos extraídos
│   │   │   ├── ChatAssistant.js     # Chat IA contextual
│   │   │   └── ui/                  # Componentes Radix UI
│   │   ├── hooks/                    # Custom hooks
│   │   ├── lib/                      # Utilidades (axios, etc.)
│   │   └── App.js                    # Componente principal
│   ├── package.json
│   └── tailwind.config.js
├── docs/
│   ├── GProA_EDGE_Launcher.ps1      # Launcher interactivo
│   ├── LOCAL_DEPLOYMENT.md           # Guía de despliegue
│   └── TESTING_CHECKLIST.md         # Lista de pruebas
├── .env.example
├── render.yaml                      # Configuración Render.com
└── README.md
```

---

## 🔐 Autenticación SSO

- **OAuth2 con Google**: Flujo completo con scopes `drive.readonly`, `userinfo.profile`, `userinfo.email`, `openid`.
- **Detección de Rol Automática**: Si el email contiene `gproatechnology` → rol **CEO** con permisos de administrador. Otros emails → rol **Consultant**.
- **Limpieza de Sesión**: `localStorage.clear()` en logout garantiza que no persistan datos de sesión anteriores.
- **Fallback de Avatar**: Si Google no entrega foto de perfil, se muestra una inicial dinámica basada en el nombre real del usuario.

---

## 📊 Métricas del Dashboard (Tiempo Real)

| Métrica | Fuente |
|---|---|
| **Total Proyectos** | Conteo real de la base de datos |
| **Archivos Totales** | `files_count_documents()` por proyecto |
| **Archivos Procesados** | Archivos con `status = 'processed'` |
| **Reducción CO2** | Calculado por `AuditService.recalculate_project_metrics()` |
| **Eficiencia Energética** | Promedio de ahorros EEM detectados |

---

## 🤖 Motor de Auditoría (AuditService)

Servicio en `backend/app/services/audit_service.py` que orquesta:

1. **Detección de Medida**: Identifica EEM22, EEM09, WEM01, WEM02, EEM16 por nombre de archivo.
2. **Parseo Multihilo**: Ejecuta `PDFParser` y `CADParser` mediante `asyncio.to_thread` en segundo plano para evitar congelar la interfaz de usuario.
3. **Procesamiento Especializado**: Llama al `EdgeProcessor` correcto (luminarias, HVAC, agua, diseño/planos).
4. **Persistencia**: Actualiza el registro del archivo con `watts`, `lumens`, `specialized_data`.
5. **Recalculo de Proyecto**: Agrega métricas de CO2 y eficiencia al proyecto padre.

### Medidas EDGE Soportadas

| Medida | Descripción | Procesador |
|--------|-------------|------------|
| **EEM22** | Iluminación Eficiente | `process_eem22_luminaires()` |
| **EEM09** | HVAC | `process_eem09_hvac()` |
| **EEM16** | Energías Renovables | `process_eem16_renewables()` |
| **WEM01** | Aparatos de Agua (Griferías) | `process_water_fixtures()` |
| **WEM02** | Sanitarios | `process_water_fixtures()` |
| **Unifilar** | Diagrama Unifilar / Cuadro de Cargas | `process_unifilar_diagram()` |

### Flujo Detallado de Procesamiento por Medida EDGE

```mermaid
flowchart TB
    subgraph INPUT["Entrada"]
        FILE[Archivo PDF/DXF/XLSX]
        NAME[Nombre del archivo]
    end
    
    subgraph DETECT["Detección de Medida"]
        UP[Uppercase filename]
        CHECK{Keywords}
        CHECK -->|EEM22| LUM[LUM, LIGHT, EL1-EL7]
        CHECK -->|EEM01| WWR[WWR, WINDOW]
        CHECK -->|EEM09| HVAC[HVAC, AIRE]
        CHECK -->|EEM16| SOL[SOLAR, RENEW]
        CHECK -->|WEM01| GRIF[GRIF, SHOWER]
        CHECK -->|WEM02| WC[WC, TOILET]
        CHECK -->|DEF| GEN[GENERAL]
    end
    
    subgraph PARSE["Parsers"]
        LUM --> PDFP[PDFParser]
        HVAC --> PDFP
        SOL --> PDFP
        GRIF --> PDFP
        WC --> PDFP
        GEN --> PDFP
        UP --> CADP[CADParser]
    end
    
    subgraph PROCESS["Procesamiento IA"]
        PDFP --> GM[Gemini Flash 1.5]
        CADP --> GM
        GM --> JSON[JSON estructurado]
    end
    
    subgraph EXTRACT["Extracción de Datos"]
        JSON --> EXT{Por Medida}
        EXT -->|EEM22| WL[Watts, Lumens, Eficacia]
        EXT -->|EEM09| HV[COP, EER, SEER, BTU]
        EXT -->|EEM16| RN[Capacidad kW, Paneles]
        EXT -->|WEM01| WF[Flujo LPM, Ahorro%]
        EXT -->|WEM02| SF[Flujo LPF]
        EXT -->|UN| LD[Carga Watts]
    end
    
    subgraph SAVE["Persistencia"]
        WL --> UF[files_update_one]
        HV --> UF
        RN --> UF
        WF --> UF
        SF --> UF
        LD --> UF
        UF --> RPM[recalculate_project_metrics]
    end
    
    classDef input fill:#e3f2fd,stroke:#1565c0
    classDef detect fill:#fff8e1,stroke:#f9a825
    classDef parse fill:#e8f5e9,stroke:#2e7d32
    classDef process fill:#fff3e0,stroke:#f57c00
    classDef extract fill:#fce4ec,stroke:#ad1457
    classDef save fill:#f3e5f5,stroke:#7b1fa2
    class FILE,NAME input
    class UP,CHECK,DETECT detect
    class PDFP,CADP parse
    class GM,JSON process
    class EXT,WL,HV,RN,WF,SF,LD extract
    class UF,RPM save
```

### Comparación: Modo Demo vs Producción

```mermaid
graph LR
    subgraph DEMO["Modo Demo"]
        D1[SQLite Local]
        D2[Mock Data]
        D3[Sin Google Drive]
        D4[Gratis]
    end
    
    subgraph PROD["Modo Producción"]
        P1[MongoDB Atlas]
        P2[Gemini Flash 1.5]
        P3[OAuth2 Drive]
        P4[Por uso]
    end
    
    DEMO -.->|Config| PROD
    D1 -->|MONGO_URL| P1
    D2 -->|GEMINI_API_KEY| P2
    D3 -->|credentials.json| P3
    D4 -->|Config| P4
    
    classDef demo fill:#e8f5e9,stroke:#2e7d32
    classDef prod fill:#ffebee,stroke:#c62828
    class D1,D2,D3,D4 demo
    class P1,P2,P3,P4 prod
```

### Manejo de Errores en el Pipeline

```mermaid
flowchart TB
    START[Inicio proceso] --> FILE{Archivo existe?}
    FILE -->|No| ERR1[Log error: archivo no encontrado]
    FILE -->|Yes| PATH{Path válido?}
    PATH -->|No| ERR2[Log error: path inválido]
    PATH -->|Yes| EXT{Extensión soportada?}
    EXT -->|No| ERR3[Warning: sin parser]
    EXT -->|Yes| PARSE[Ejecutar parser]
    PARSE --> PERR{Parser error?}
    PERR -->|Yes| ERR4[Log error parsing]
    PERR -->|No| AI[Ejecutar EdgeProcessor]
    AI --> AIERR{AI error?}
    AIERR -->|Yes| ERR5[Log error AI]
    AIERR -->|No| SAVE[Guardar resultados]
    SAVE --> SERR{DB error?}
    SERR -->|Yes| ERR6[Log error DB]
    SERR -->|No| OK[Proceso exitoso]
    
    ERR1 --> END[Fin]
    ERR2 --> END
    ERR3 --> END
    ERR4 --> END
    ERR5 --> END
    ERR6 --> END
    OK --> END
    
    classDef start fill:#e3f2fd,stroke:#1565c0
    classDef error fill:#ffebee,stroke:#c62828
    classDef success fill:#e8f5e9,stroke:#2e7d32
    class START start
    class ERR1,ERR2,ERR3,ERR4,ERR5,ERR6 error
    class OK,SAVE success
```

### Integración con Servicios Externos

```mermaid
flowchart LR
    subgraph FRONTEND["React Frontend"]
        REQ[Axios Requests]
    end
    
    subgraph BACKEND["FastAPI Backend"]
        MID[Middleware]
        END[Endpoints]
        SVC[Services]
    end
    
    subgraph GOOGLE["Google Cloud"]
        AUTH[OAuth2]
        DRIVE[Drive API v3]
    end
    
    subgraph GEMINI["Google AI Studio"]
        FLASH[Gemini Flash 1.5]
        PRO[Gemini 1.5 Pro]
    end
    
    REQ --> MID
    MID --> END
    END --> SVC
    SVC --> AUTH
    SVC --> DRIVE
    SVC --> FLASH
    SVC --> PRO
    
    classDef frontend fill:#e3f2fd,stroke:#1565c0
    classDef backend fill:#e8f5e9,stroke:#2e7d32
    classDef external fill:#fff3e0,stroke:#f57c00
    class REQ,MID,END,SVC frontend
    class AUTH,DRIVE external
    class FLASH,PRO external
```

### Estructura de Archivos del Proyecto

```mermaid
graph TD
    subgraph ROOT["GProA_EOSIS_Edge/"]
        BACK[backend/]
        FRONT[frontend/]
        DOCS[docs/]
    end
    
    subgraph BACKEND["backend/"]
        APP[app/]
        DATA[data/]
        UPL[uploads/]
    end
    
    subgraph APP["app/"]
        API[api/]
        SVC[services/]
        DB[db/]
        CORE[core/]
    end
    
    subgraph API["api/"]
        END[endpoints/]
        ROUT[api_router.py]
    end
    
    subgraph SVC["services/"]
        AUD[audit_service.py]
        GD[google_drive_service.py]
        EP[edge_processors.py]
        PR[parsers/]
        AI[ai_service.py]
        ASST[assistant_service.py]
    end
    
    ROOT --> BACK
    ROOT --> FRONT
    ROOT --> DOCS
    BACK --> APP
    BACK --> DATA
    BACK --> UPL
    APP --> API
    APP --> SVC
    APP --> DB
    APP --> CORE
    API --> END
    API --> ROUT
    SVC --> AUD
    SVC --> GD
    SVC --> EP
    SVC --> PR
    SVC --> AI
    SVC --> ASST
    
    classDef root fill:#e3f2fd,stroke:#1565c0
    classDef backend fill:#e8f5e9,stroke:#2e7d32
    classDef module fill:#fff8e1,stroke:#f9a825
    class ROOT root
    class BACK,FRONT,DOCS root
    class APP,DATA,UPL backend
    class API,SVC,DB,CORE module
    class END,AUD,GD,EP,PR,AI,ASST module
```

### Flujo de Exportación a Excel

```mermaid
flowchart TD
    START[Usuario solicita exportación] --> PRJ{Seleccionar proyecto?}
    PRJ -->|Sí| GET[Obtener datos proyecto]
    PRJ -->|No| ERR[Error: seleccione proyecto]
    GET --> FIL[Obtener archivos procesados]
    FIL --> DATA[Agregar datos]
    DATA --> EXCEL[Generar Excel con openpyxl]
    EXCEL --> FMT{Formatear hojas?}
    FMT -->|Sí| STYLE[Aplicar estilos]
    FMT -->|No| SAVE[Guardar archivo]
    STYLE --> SAVE
    SAVE --> DOWNLOAD[Descargar archivo]
    DOWNLOAD --> END[Fin]
    ERR --> END
    
    classDef start fill:#e3f2fd,stroke:#1565c0
    classDef process fill:#fff8e1,stroke:#f9a825
    classDef error fill:#ffebee,stroke:#c62828
    classDef success fill:#e8f5e9,stroke:#2e7d32
    class START,PRJ start
    class GET,FIL,DATA,EXCEL,FMT,STYLE,SAVE process
    class ERR error
    class DOWNLOAD,END success
```

### Chat IA - Flujo de Conversación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as Backend
    participant AS as AssistantService
    participant DB as UnifiedDB
    participant GM as Gemini

    U->>FE: Enviar mensaje
    FE->>API: POST /api/assistant/chat
    
    API->>DB: Obtener contexto del proyecto
    DB-->>API: Datos del proyecto
    
    API->>AS: Generar prompt contextual
    AS->>GM: Enviar prompt + contexto
    GM-->>AS: Respuesta IA
    
    AS-->>API: Respuesta formateada
    API-->>FE: JSON respuesta
    FE-->>U: Mostrar mensaje
    
    Note over U,GM: El chat siempre tiene acceso al estado real del proyecto
```

### Configuración de Variables de Entorno

```mermaid
flowchart LR
    subgraph ENV["backend/.env"]
        REQ["GEMINI_API_KEY (requerido)"]
        OPT1["MONGO_URL (opcional)"]
        OPT2["DB_NAME (opcional)"]
        OPT3["DEMO_MODE (opcional)"]
        OPT4["GOOGLE_OAUTH_CLIENT_ID (opcional)"]
        OPT5["CORS_ORIGINS (opcional)"]
    end
    
    subgraph EFFECT["Efecto"]
        AI[Activa IA real]
        PROD[Activa MongoDB]
        NAME[Nombre DB]
        DEMO[Activa modo demo]
        SSO[Activa SSO]
        CORS[Config CORS]
    end
    
    REQ --> AI
    OPT1 --> PROD
    OPT2 --> NAME
    OPT3 --> DEMO
    OPT4 --> SSO
    OPT5 --> CORS
    
    classDef env fill:#e8f5e9,stroke:#2e7d32
    classDef effect fill:#fff3e0,stroke:#f57c00
    class REQ,OPT1,OPT2,OPT3,OPT4,OPT5 env
    class AI,PROD,NAME,DEMO,SSO,CORS effect
```

### Despliegue en Render.com

```mermaid
flowchart TD
    subgraph PREP["Preparación"]
        PUSH[Push a GitHub]
        RENDER[Crear cuenta Render]
    end
    
    subgraph DEPLOY["Despliegue"]
        BACK[Deploy Backend]
        FRONT[Deploy Frontend]
    end
    
    subgraph CONFIG["Configuración"]
        ENV[Configurar variables]
        BUILD[Build command]
        START[Start command]
    end
    
    subgraph VERIFY["Verificación"]
        TEST[Tests]
        LOGS[Revisar logs]
        READY[¡Listo!]
    end
    
    PUSH --> RENDER
    RENDER --> BACK
    RENDER --> FRONT
    BACK --> ENV
    FRONT --> ENV
    ENV --> BUILD
    BUILD --> START
    START --> TEST
    TEST --> LOGS
    LOGS --> READY
    
    classDef prep fill:#e3f2fd,stroke:#1565c0
    classDef deploy fill:#e8f5e9,stroke:#2e7d32
    classDef config fill:#fff8e1,stroke:#f9a825
    classDef verify fill:#f3e5f5,stroke:#7b1fa2
    class PUSH,RENDER prep
    class BACK,FRONT deploy
    class ENV,BUILD,START config
    class TEST,LOGS,READY verify
```

---

## 🎨 Identidad Visual (v2.0)

- **Login Screen**: Fondo animado con "Logo Cloud" — múltiples logos de EOSIS y EDGE flotando con efectos de paralaje y opacidades dinámicas.
- **Sidebar**: Avatar dinámico con foto de perfil de Google o inicial corporativa como respaldo.
- **Branding**: Paleta de colores unificada entre GProA, EOSIS y EDGE.

---

## 🚀 Despliegue Local

### Prerequisitos

- Python 3.12+
- Node 18+
- Cuenta de Google con acceso a `credentials.json` de OAuth2

### Inicio Rápido (Windows)

```powershell
# Desde la carpeta docs/
.\GProA_EDGE_Launcher.ps1

# Opciones del Launcher:
# [2] Iniciar Backend + Frontend
# [6] Reiniciar Backend (después de cambios en Python)
```

### Inicio Manual

```powershell
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm start
```

### Configuración de Variables de Entorno

Crear archivo `backend/.env`:

```env
# Required for AI processing (get from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: MongoDB Atlas for production
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/gproa_edge
DB_NAME=gproa_edge

# Optional: Demo mode (mock AI responses)
DEMO_MODE=false
```

### Configuración de Google OAuth2

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto → APIs y servicios → Credenciales
3. Crear ID de cliente OAuth2 para aplicación web
4. Agregar URI de redirección: `http://localhost:8000/api/google-drive/callback`
5. Descargar `credentials.json` y colocar en `backend/data/`

---

## 🗺️ Roadmap

### ✅ v2.0 — Completado (Mayo 2026)

- [x] SSO con Google OAuth2 (Drive + Profile)
- [x] Sincronización automática de archivos desde Google Drive
- [x] Motor de Auditoría Automática (`AuditService`)
- [x] Dashboard con métricas reales (CO2, archivos, eficiencia)
- [x] Identidad de marca premium (Logo Cloud, avatar dinámico)
- [x] Detección de rol CEO / Consultor por email
- [x] Chat Asistente con contexto real del proyecto
- [x] Procesadores especializados para EEM22, EEM09, EEM16, WEM01, WEM02
- [x] Soporte Unifilar / Cuadro de Cargas
- [x] Spatial Reasoning Engine (reconstrucción geometría implícita)
- [x] Topological Precision Initiative (contour tracing, holes, validation)

### 🔜 v2.1 — Próximos Pasos

- [ ] Validación de imagen de perfil de Google en Sidebar
- [x] Procesamiento en background (asyncio tasks & to_thread) para parseo de archivos pesados
- [ ] Panel de auditoría detallado por medida EDGE
- [ ] Exportación a formato EDGE App (.xlsx certificador)
- [ ] RBAC completo (Admin, Auditor, Consultor, Cliente)

### 🏗️ Phase 8.2 — Topological Precision Initiative (SDD)

**Objetivo:** Transformar polígonos "bounding box" en geometría topológicamente precisa desde planos arquitectónicos reales.

- [x] `contour_tracer.py` — Reconstrucción de contornos reales desde vector linework
- [x] `hole_detector.py` — Detección de voids, courtyards y polígonos anidados  
- [x] `topology_validator.py` — Validación de self-intersections y winding order
- [x] `polygon_simplifier.py` — Simplificación Douglas-Peucker con preservación de topología
- [x] `boundary_semantics.py` — Detección de shared edges sin inferencia arquitectónica
- [x] `precision_metrics.py` — Métricas de fidelidad geométrica (Hausdorff, area preservation)

**Logros actuales (Mayo 2026):**
- PDF: 777 polígonos → 777 nodos → 597 edges (74,738 vector drawings)
- Adjacency O(n²) → O(n*k): 14.6x speedup (4761ms → 327ms)
- Sistema sobrevive planos reales sin inferencia semántica arquitectónica

### 🏢 v3.0 — Enterprise

- [ ] Multi-tenant con aislamiento de datos por organización
- [ ] Integración Computer Vision para CAD determinístico
- [ ] **API pública para integraciones ERP / BIM/IFC** (Topología precisa disponible)
- [ ] SharePoint Sync

---

## 🧪 Modos de Operación

| Feature | **Demo** (Default) | **Producción** |
|---|---|---|
| **Base de datos** | SQLite local | MongoDB Atlas |
| **Motor IA** | Mock data | Google Gemini Flash |
| **Google Drive** | Sin sync | Sync completo OAuth2 |
| **Costo** | $0 | Por token Gemini |

---

## 📄 Variables de Entorno

| Variable | Descripción | Requerido |
|---|---|---|
| `GEMINI_API_KEY` | Clave API de Google AI (Gemini Flash) | Para IA real |
| `MONGO_URL` | Connection string MongoDB Atlas | Para prod |
| `DB_NAME` | Nombre de la base de datos | No |
| `DEMO_MODE` | `true` para usar mock data | No |
| `GOOGLE_OAUTH_CLIENT_ID` | Client ID de Google Cloud Console | Para SSO |
| `CORS_ORIGINS` | Orígenes permitidos | En producción |

---

## 🤝 Contribución

1. Fork & clone
2. Branch desde `submain`
3. PR a `submain` → revisión → merge a `main`

---

## 📄 Licencia

MIT — GProA Technology © 2026

---

## 🙏 Créditos

- [EDGE Buildings](https://edgebuildings.com/) — Estándar de certificación
- [IFC EDGE](https://ifc.org/our-work/edge/) — Software oficial de certificación
- [Google Cloud](https://cloud.google.com/) — OAuth2 & Drive API
- [Google DeepMind](https://deepmind.google/) — Gemini 1.5 Pro

---

⭐ ¡Dale una estrella en GitHub si este proyecto te es útil!