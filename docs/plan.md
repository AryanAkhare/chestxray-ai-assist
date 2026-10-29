# Implementation plan and assumptions

## Scope

Deliver Phase 1 as a local research and education prototype. The supplied model artifacts are in `output_baseline/` and `output_gan/`, so code reads those locations directly instead of copying or modifying them. Checkpoints are treated as trusted local inputs only during one-time conversion; the running service accepts only converted `safetensors` weights and checks their SHA-256 metadata before inference. Uploaded pixels stay in memory; saved records contain scores, a case identifier, feedback, and a SHA-256 of the input bytes.

## Work sequence

1. Inventory model files, read configuration and result schemas, and confirm the recorded label order. Inspect checkpoint archives without executing their pickle payloads; use `weights_only=True` only in the conversion utility.
2. Write parity and threshold verification paths before enabling inference in the application. The provided workspace has no parity images and the current runtime has no PyTorch, so parity is implemented as a gated acceptance check and reported as unverified until the user supplies the test images and dependencies.
3. Implement shared image preprocessing, a local FastAPI service, password-based first-run setup, score persistence without pixels, audit hash chain, hash-verified model loading, and a React reviewer workspace.
4. Document intended use, hazards, requirements traceability, architecture, limitations, verification state, and operating instructions.

## Assumptions and constraints

- The existing `output_*` folders are the model-package source of truth and are read-only inputs.
- Baseline and A/B/C/D result CSVs are authoritative for thresholds and metrics; no performance numbers are embedded in the UI.
- CPU is the default; CUDA is selected only when available.
- API sessions expire after eight hours and restart invalidates sessions. Passwords are hashed with Argon2.
- Production claims are out of scope. This work does not make a certified product, and incomplete acceptance checks are disclosed.
