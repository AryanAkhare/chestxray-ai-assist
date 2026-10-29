# ChestX-ray AI Assist

Local research and education prototype for reviewing the supplied NIH ChestX-ray14 model outputs. This is not a medical device, does not provide a diagnosis, and must not be used to make or delay clinical decisions. All outputs require review by a qualified clinician.

The app includes model comparison, Grad-CAM, PDF/JSON/CSV report exports, multiple-image batch upload, a searchable case worklist with score trends, and pan/zoom/window/level/invert/reset viewer controls. Acceptance testing is incomplete; see [verification report](docs/verification_report.md). Detailed deployment options are available in the [Deployment Guide](docs/deployment.md).

## Quick Start with Docker (Recommended)

Run both the frontend and backend in a unified production container:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and launch container
docker compose up --build -d
```

Open [http://localhost:8000](http://localhost:8000) to go directly to the workspace.

## Start on Windows (Local Development)

1. Install Python 3.11 and Node.js 20 or later.
2. Create and activate a virtual environment, then install `backend/requirements.txt`.
3. Run `python scripts/convert_checkpoints.py` once. It converts the trusted local checkpoint files to `data/converted/`. The app loads only safetensors weights and verifies their hashes.
4. In one terminal, run `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`.
5. In a second terminal, `cd frontend`, run `npm install`, then `npm run dev`.
6. Open the local Vite URL to go directly to the workspace. The default server binds to loopback.

The original `output_baseline/` and `output_gan/` folders are read-only model/result inputs. No Kaggle credential file is read or copied; matching credential patterns are ignored by Git.

## Linux/macOS

Use Python 3.11 and Node.js, install the same pinned dependencies, convert checkpoints, then start the API and frontend with the commands above. Shell helper scripts are provided for convenience.

## Runtime and privacy notes

The workspace is open without sign-in. Anyone who can reach the deployment can upload studies, create analyses, and view the shared analysis history. Restrict access at the hosting or network layer if the deployment should not be public.

Uploads are processed in memory. The database stores scores, reviewer feedback, timestamps, case IDs, and the source-file hash; it does not store image pixels or patient tags. A 50 MB size limit applies by default. Converted model weights and the local SQLite database are ignored by Git.

## Verification

Run `python scripts/inspect_model_package.py` and `python scripts/check_thresholds.py` to inspect artifact metadata and recalculate threshold flags from saved scores. Run `python -m pytest tests/test_thresholds.py tests/test_preprocessing.py tests/test_gradcam.py` for the available unit checks. The parity acceptance test requires at least 50 NIH test images in `tests/parity_images/` and converted weights. Model inference and Grad-CAM were smoke-checked on synthetic images; test-set parity and full API/browser workflows remain unverified.
