# EDGE Document Processor

[![Tests](https://github.com/gproatechnology/GProA_Edge/workflows/CI/badge.svg)](https://github.com/gproatechnology/GProA_Edge/actions)
[![Backend Tests](https://img.shields.io/badge/Backend-100%25-brightgreen.svg)]()
[![Frontend Tests](https://img.shields.io/badge/Frontend-95%25-brightgreen.svg)]()

## 🚀 AI-Powered Document Intelligence for EDGE Certification

> **Outcome**: Reduce certification documentation time by up to **80%** while increasing audit reliability and compliance speed.

**EDGE Document Processor** is a professional-grade platform designed to streamline the complex documentation required for EDGE certification. It acts as an **intelligent document engine** that transforms unstructured construction data into structured, auditable certification inputs.

- **Intelligent Classification**: Automatically categorizes documents into EDGE categories (ENERGY, WATER, MATERIALS).
- **Assisted Data Extraction**: High-precision extraction of technical parameters (watts, lumens, U-values, brands/models).
- **AI-Assisted Area Estimation**: Interactive tools to assist in spatial data extraction from floor plans, ensuring user-verifiable results (not a final authority).
- **Compliance Validation**: Real-time detection of missing documentation per measure.
- **Auditable Exports**: Structured Excel outputs ready for certification submission.

---

## ✨ Features
- 📋 **Project Governance**: Centralized management of certification projects and typologies.
- 📂 **Multi-Source Pipeline**: Upload and process various file types (PDF, Images, Excel).
- 🧠 **Context-Aware Processing**: GPT-4o powered classification and technical extraction.
- ⚖️ **Confidence & Traceability**: Integrated confidence scoring per extraction and source referencing.
- 📊 **Executive Dashboard**: Real-time monitoring of project status, documentation gaps, and EDGE metrics.
- 🎨 **Premium UI**: Modern, responsive interface built with React 19, Tailwind, and Shadcn UI.
- 📤 **Enterprise Export**: Advanced Excel generation with detailed data sheets.
- ⚡ **AI Toolset**: Integrated "Prompts" for classification (ConsultorÍA) and area calculation (Areas & Loads).

---

## 🛠 Tech Stack
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-19-blue?style=for-the-badge&logo=react)
![MongoDB](https://img.shields.io/badge/MongoDB-4DB33D?style=for-the-badge&logo=mongodb)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-38B2AC?style=for-the-badge&logo=tailwind-css)
![GPT-4o](https://img.shields.io/badge/OpenAI-GPT--4o-orange?style=for-the-badge&logo=openai)

---

## 🏗️ Architecture

```mermaid
graph TB
    FE[React Frontend] -->|REST API| API[FastAPI Server]
    API -->|Persist| DB[MongoDB / SQLite]
    API -->|Classify/Extract/Validate| LLM[GPT-4o]
    LLM -->|JSON| API
    DB -->|Query| API
    API -->|Data/Status/Export| FE
```

---

## 🔄 Document Processing Flow

```mermaid
flowchart TD
    A[File Upload] --> B[Text/Image Extraction]
    B --> C[AI Classify<br/>Category + Measure]
    C --> D[AI Extract<br/>Technical Parameters]
    D --> E{doc_type == 'blueprint' ?}
    E -->|Yes| F[AI-Assisted<br/>Area Estimation]
    E -->|No| G[Validation Layer<br/>Confidence + Gaps]
    F --> G
    G --> H[Persistence<br/>MongoDB / SQLite]
    H --> I[Audit Ready Dashboard<br/>+ Excel Export]

    classDef startEnd fill:#e1f5fe,stroke:#01579b
    classDef ai fill:#fff3e0,stroke:#e65100
    classDef db fill:#f3e5f5,stroke:#4a148c
    class A,I startEnd
    class C,D,F,G ai
    class H db
```

---

## 🛡️ Trust & Reliability Layer (Auditor Ready)

Unlike generic extraction tools, this processor is built for the high-stakes environment of green building certification:

- **Confidence Scoring**: Every extracted value is accompanied by an AI-generated confidence score (0-1). Low-confidence values are flagged for human review.
- **Initial Traceability**: Every data point is directly linked to its source document, ensuring a clear audit trail from the start.
- **Human-in-the-Loop Validation**: Built-in workflow for human verification, ensuring that AI-driven insights are always validated by experts before final submission.
- **Hybrid Validation**: Combines Large Language Models with deterministic business rules for EDGE measures.

---

## 🎯 Screenshots
![Dashboard](./screenshots/dashboard.png)
![File Upload](./screenshots/upload.png)
![EDGE Status](./screenshots/status.png)
*(Run locally to generate screenshots)*

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (Windows/Mac) or **Docker + Docker Compose** (Linux)
- **Node 18+** (optional, for frontend dev without Docker)
- **Python 3.12+** (optional, for backend dev without Docker)

---

## 🐳 **Option 1: Docker Compose (Recommended)**

La forma más fácil de iniciar todo el stack (backend + frontend) con un solo comando.

### **Desarrollo (Hot-Reload)**
```bash
# 1. Clona el repo y checkout a submain
git clone https://github.com/gproatechnology/GProA_EOSIS_Edge.git
cd GProA_EOSIS_Edge
git checkout submain

# 2. Inicia todos los servicios
docker-compose up
```

---

## 🧪 Demo Mode vs 🏭 Production Mode

| Feature | **Demo Mode** (Default) | **Production Mode** |
|---------|-------------------------|---------------------|
| **Database** | SQLite (Local/Ephemeral) | MongoDB Atlas (Cloud/Persistent) |
| **AI Engine** | Mock AI (Hardcoded logic) | OpenAI GPT-4o (Real-time Analysis) |
| **Cost** | $0 (No API Keys needed) | Pay-per-token (OpenAI API Key) |
| **Accuracy** | Simulation only | Real Document Processing |
| **Use Case** | UX Review & Feature Demos | Real Project Certification |

---

### 🔧 **Advanced: Production Mode (with MongoDB + OpenAI)**

For real AI processing and cloud database:

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGO_URL` | MongoDB Atlas connection string | ✅ Yes |
| `OPENAI_API_KEY` | OpenAI API key (GPT-4o) | ✅ Yes |
| `DEMO_MODE` | Set to `false` | No |
| `CORS_ORIGINS` | Allowed origins (e.g., `https://yourdomain.com`) | ✅ Yes |
| `GOOGLE_DRIVE_CREDENTIALS` | Service Account JSON (Placeholder for future sync) | ⏳ Optional |

Setup guide: **[ENV_SETUP.md](docs/ENV_SETUP.md)**.

---

## 🗺️ Roadmap (Enterprise Readiness)
### 🚀 Phase 2 (P1: Professionalization)
- **Visual Traceability**: Highlight extracted data directly on PDF source pages for instant verification.
- **Enhanced OCR**: Advanced pre-processing for low-quality PDF scans and handwritten notes.
- **Google Drive / Sharepoint**: Direct synchronization to eliminate manual upload limits. [IN PROGRESS]
- **Progress Tracking**: Real-time progress bars for batch document processing.

### 🏢 Phase 3 (P2: Enterprise & Security)
- **RBAC Security**: Role-Based Access Control (Admin, Auditor, Consultant).
- **Multi-Tenant Architecture**: Complete data isolation for different client organizations.
- **Advanced CV Integration**: Computer Vision for deterministic area calculation from CAD/PDF.
- **API for Integrations**: Connect with existing ERP or Project Management tools.

---

## 📁 Project Structure
```
GProA_Edge/
├── backend/          # FastAPI + MongoDB + GPT-4o
├── frontend/         # React + Tailwind + Shadcn UI
├── docs/             # Technical documentation & guides
├── memory/PRD.md     # Product Requirements
└── README.md         # This file
```

---

## 🤝 Contributing
1. Fork & clone
2. Create feature branch
3. PR to `main`

## 📄 License
MIT

## 🙏 Acknowledgments
- [EDGE Certification](https://edgebuildings.com/)
- [Emergent Integrations](https://emergent.sh)
- [Shadcn UI](https://ui.shadcn.com/)

---
⭐ Star us on GitHub!
