# Product Requirements Document (PRD) - GProA EDGE Document Processor

## 🎯 Vision
Transform the manual, fragmented process of EDGE certification documentation into an automated, AI-driven workflow that eliminates technical bottlenecks (like file limits) and ensures a high-quality audit trail.

## 🚀 Core Features (The "Two Prompts" Philosophy)

### 1. ConsultorÍA EDGE (Prompt 1)
**Goal**: Automate the classification and data extraction of multi-source project files.
- **Input**: Project metadata (Name, Typology) and bulk file uploads (PDF, JPG, DWG, RVT).
- **Process**:
    - Automatic classification by EDGE Category (DESIGN, ENERGY, WATER, MATERIALS).
    - Sub-classification by specific EDGE Measure (e.g., EEM22, WEM01).
    - Technical data extraction (Watts, Lumens, Brand, Model, etc.).
- **Output**: 
    - A structured ZIP file with organized folders.
    - A summary table with key data to populate EDGE calculators.

### 2. Areas and Loads Breakdown (Prompt 2)
**Goal**: Automate spatial data extraction from architectural floor plans.
- **Input**: Architectural plans (.pdf, .dwg, .rvt).
- **Process**: Analysis of dimensions, labels, and nomenclature to calculate individual room/space areas.
- **Output**: A precise table of spaces with their corresponding square meters (m2).

## 🛠 Strategic EDGE Measures
The system must support and prioritize the following strategies:
- **Design**: DESIGN (General areas/loads).
- **Energy**: EEM01, EEM02, EEM03, EEM05, EEM06, EEM08, EEM09, EEM13, EEM16, EEM22, EEM23.
- **Water**: WEM01, WEM02, WEM04, WEM07, WEM08.
- **Materials**: MEM01, MEM02, MEM03, MEM04, MEM05, MEM06, MEM07, MEM08, MEM09, MEM10.

## ☁️ Infrastructure & Integrations
- **Google Drive Integration**:
    - Eliminate the manual 10-file upload limit of standard LLM interfaces.
    - Direct connection to project folders in Drive.
    - Automatic synchronization of processed files back to Drive.
- **Audit-Ready Layer**:
    - Confidence scoring (0-1) for AI extractions.
    - Human-in-the-loop verification workflow.
    - Direct linkage between extracted data and source document page.

## 📈 Success Metrics
- **Time Reduction**: 80% reduction in documentation time.
- **Accuracy**: >95% precision in classification and numeric extraction.
- **Scalability**: Support for hundreds of files per project without performance degradation.
