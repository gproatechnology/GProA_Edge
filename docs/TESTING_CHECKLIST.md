# Deployment Verification Test Plan for GProA EDGE

## Environment Setup Test

### 1. Backend Environment Variables
- [ ] `OPENAI_API_KEY` is set in Render backend service (marked as Secret)
- [ ] `MONGO_URL` is set (marked as Secret)
- [ ] `DB_NAME` is set to `gproa_edge`
- [ ] `CORS_ORIGINS` is set (start with `*`, later restrict)

**How to check:** Render Dashboard → backend service → Settings → Environment Variables

### 2. Frontend Environment Variables
- [ ] `REACT_APP_BACKEND_URL` is set to backend hostname (without https://)

**How to check:** Render Dashboard → frontend service → Settings → Environment Variables

---

## Service Health Checks

### Backend
- [ ] Service status shows **Live** (yellow/green dot)
- [ ] Health check endpoint responds:
  ```bash
  curl https://gproa-edge-backend.onrender.com/api/
  # Expected: {"message":"EDGE Document Processor API v2"}
  ```
- [ ] OpenAPI docs accessible: `https://.../docs`
- [ ] No errors in Logs tab (check for "STARTING" and "Uvicorn running on")

### Frontend
- [ ] Service status shows **Live**
- [ ] Frontend URL loads React app (no blank page)
- [ ] No console errors in browser DevTools (F12)
- [ ] Bundled JS loads successfully (Network tab shows 200 for main.*.js)

---

## Functionality Tests

### Project Management
- [ ] Click "Create Project" button → dialog opens
- [ ] Create project with name and typology → success toast appears
- [ ] Project appears in dashboard grid/list
- [ ] Click project → navigates to detail view

### File Upload
- [ ] Tab "Archivos" displays file upload zone
- [ ] Click upload → file picker opens
- [ ] Select `.txt` file with sample data → file appears in list
- [ ] File status initially "pending"
- [ ] File metadata shown: filename, size, upload date

### AI Processing
- [ ] "Procesar Proyecto EDGE" button visible (only when files exist)
- [ ] Click button → modal opens with progress bar
- [ ] Progress updates in real-time (0% → 100%)
- [ ] Current filename and step displayed
- [ ] After completion: modal shows "Completado"
- [ ] File status changes to "processed"

### Data Extraction Verification
Go to "Datos Extraídos" tab:
- [ ] Table displays list of files
- [ ] Columns: Filename, Category, Measure, Type, Watts, Lumens, Equipment, Brand, Model, Status
- [ ] Numeric values use monospace font (IBM Plex Mono)
- [ ] Data matches uploaded sample (e.g., watts=30, lumens=3000 for test luminaire)

### EDGE Compliance (WBS Validation)
Go to "Compliance EDGE" tab:
- [ ] Coverage percentage displayed (e.g., "25%")
- [ ] Missing documents list appears for incomplete measures
- [ ] Category badges (ENERGY, WATER, MATERIALS) with counts
- [ ] Progress bars show completion per measure

### Export Functions
- [ ] "Export Excel" button present in UI (usually in "Datos Extraídos" or toolbar)
- [ ] Click → downloads `.xlsx` file
- [ ] Open Excel file:
  - [ ] Sheet 1: "Clasificacion EDGE" with all files
  - [ ] Sheet 2: "Validacion WBS" with measures and gaps
  - [ ] Sheet 3: "EEM22 Luminarias" (if LED data uploaded)
  - [ ] Sheet 4: "Areas" (if plano files uploaded)
- [ ] **ZIP Organization (Prompt 1 Output)**:
  - [ ] ZIP contains folders: DESIGN, ENERGY, WATER, MATERIALS
  - [ ] Files are correctly moved into their corresponding measure subfolders
- [ ] **Area Table (Prompt 2 Output)**:
  - [ ] "Resumen" or "Areas" tab shows table with space name and m2

### Tab Navigation
- [ ] All 4 tabs present: Archivos, Datos Extraídos, Compliance EDGE, Resumen
- [ ] Click each tab → content switches smoothly
- [ ] Active tab has underline indicator (2px border-bottom)

---

## API Endpoint Tests (using curl)

```bash
# Set your backend URL
BACKEND="https://gproa-edge-backend.onrender.com/api"

# 1. Root
curl $BACKEND/ | jq

# 2. Edge Rules
curl $BACKEND/edge-rules | jq '.EM22'  # Should show EEM22 definition

# 3. Create Project
curl -X POST $BACKEND/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"API Test","typology":"residential"}' | jq

# 4. Get Project
curl $BACKEND/projects/<project_id> | jq

# 5. Upload File
curl -X POST $BACKEND/projects/<project_id>/files \
  -F "file=@sample.txt;type=text/plain"

# 6. List Files
curl $BACKEND/projects/<project_id>/files | jq

# 7. Process Edge (batch)
curl -X POST $BACKEND/projects/<project_id}/process-edge | jq

# 8. WBS Validation
curl $BACKEND/projects/<project_id>/wbs-validation | jq

# 9. KPIs
curl $BACKEND/projects/<project_id}/kpis | jq

# 10. Excel Export
curl $BACKEND/projects/<project_id}/export-excel -o edge_export.xlsx
file edge_export.xlsx  # Should be a valid ZIP (XLSX) file
```

---

## Error Scenarios

Test that the platform handles errors gracefully:

- [ ] Upload non-text file (PDF) → should still store (text extraction may fail)
- [ ] Process project with no files → shows "No hay archivos" error
- [ ] Delete project → files cascade-deleted
- [ ] Invalid project ID → 404 error with message

---

## Performance Benchmarks

Measure (on Free tier):
- [ ] API root response < 2 seconds
- [ ] File upload < 3 seconds
- [ ] Batch processing 2 files: ~15-30 seconds
- [ ] Excel export generation < 5 seconds
- [ ] Frontend initial load < 10 seconds

---

## Render-Specific Checks

### Backend Service
- [ ] Build logs show: `Successfully built` and `Launched`
- [ ] No "ModuleNotFoundError" in logs
- [ ] MongoDB connection: `MongoClient connected` or similar
- [ ] Emergent LLM initialized: no auth errors

### Frontend Service
- [ ] Build completes without error (exit code 0)
- [ ] "serve" package installed automatically by Render
- [ ] Static files served from `/build` directory

### Cost Monitoring
- [ ] Backend hours: not exceeding 750/month
- [ ] Frontend hours: not exceeding 750/month
- [ ] No unexpected spikes in usage (Render billing → Metrics)

---

## Security Checklist

- [ ] `CORS_ORIGINS` is NOT `*` in production (changed to specific frontend URL)
- [ ] Environment variables marked as **Secret** in Render (show as "• • • •")
- [ ] No `.env` file committed to repository (check `.gitignore`)
- [ ] MongoDB Atlas user has only `readWrite` role (not `root`)
- [ ] (Optional) MongoDB Atlas whitelists Render IP ranges or 0.0.0.0/0 for testing

---

## Post-Deployment Documentation

- [ ] README.md updated with deployed URLs
- [ ] Team members added as collaborators on Render
- (Optional) Custom DNS configured:
  - [ ] Backend custom domain (e.g., `api.gproa.com`)
  - [ ] Frontend custom domain (e.g., `app.gproa.com`)
  - [ ] SSL certificates auto-provisioned by Render
  - [ ] `CORS_ORIGINS` updated to custom domains

---

## Rollback Plan

If deployment fails:

1. **Backend rollback:**
   - Render → backend service → Manual Deploy → "Clear Build Cache & Deploy"
   - Or: revert git commit → push (Auto-Deploy triggers)
   
2. **Frontend rollback:**
   - Same as above

3. **Database rollback:**
   - MongoDB Atlas → Data Services → Restore from backup (if needed)

---

## Sign-Off

| Checklist Item | Owner | Date | Signed |
|----------------|-------|------|--------|
| Backend deployed & healthy | | | |
| Frontend deployed & healthy | | | |
| Full user flow tested | | | |
| Export functions verified | | | |
| CORS configured correctly | | | |
| Security review complete | | | |

---

## Need Help?

- Check logs: Render Dashboard → Services → Logs tab
- Read: [RENDER_STEP_BY_STEP.md](RENDER_STEP_BY_STEP.md)
- Issues: https://github.com/gproatechnology/GProA_EOSIS_Edge/issues
