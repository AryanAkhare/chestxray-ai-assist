# Requirements traceability

| Requirement | Implementation | Verification |
|---|---|---|
| Training label order and source metrics | `backend/app/core/config.py`, `backend/app/inference/registry.py` | `scripts/inspect_model_package.py`; source CSV headers inspected |
| Trusted checkpoint conversion and hash check | `scripts/convert_checkpoints.py`, `backend/app/inference/predict.py` | Converted weights load and a prediction smoke check passed |
| Shared 224 grayscale preprocessing | `backend/app/inference/preprocess.py` | Preprocessing unit check passed |
| Reviewer UI with threshold marker and disclaimer | `frontend/src/App.tsx`, `frontend/src/style.css` | `npm run build` passed |
| Keep image bytes out of persistent storage | `backend/app/main.py`, `backend/app/db.py` | Code inspection only; runtime security checks pending |
| Authenticated local access | `backend/app/main.py` | Implementation present; brute-force lockout and rate limiting not implemented |
| Hash-chained audit records | `backend/app/db.py` | Integrity verifier exposed to admin; tamper test pending |
| Score parity on 50 test images | `tests/parity/test_parity.py` | Not verified: test images absent |
| Model comparison | `POST /api/v1/analyses/{id}/compare`, Compare tab | Two-model comparison function smoke check passed; HTTP workflow pending |
| Grad-CAM | `backend/app/inference/predict.py`, Grad-CAM tab | Verified on a synthetic image: source dimensions retained and maps differ by finding |
| PDF/JSON/CSV reports | `report_pdf`, `report_json`, `report_csv`; report tab | Response object smoke checks passed; HTTP workflow pending |
| Batch upload | `POST /api/v1/batch`, multi-file uploader | Code implemented; API response smoke test blocked by local socket sandbox |
| Pan/zoom/window/level/invert/reset | `frontend/src/App.tsx` viewer controls | Frontend production build passed; interactive browser test pending |
| Case search/history/longitudinal score plot | Worklist page | Frontend production build passed; browser workflow test pending |
