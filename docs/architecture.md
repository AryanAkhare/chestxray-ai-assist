# Architecture

The React/Vite interface communicates with a local FastAPI service under `/api/v1`. The API validates file extension and magic bytes, reads PNG/JPEG in memory, and supports DICOM decoding through pydicom. Shared preprocessing converts to grayscale, applies PIL bilinear 224 × 224 resizing, replicates channels, and applies ImageNet normalization.

Trusted `.pt` training artifacts are converted once by `scripts/convert_checkpoints.py`, which uses `torch.load(..., weights_only=True)` and writes only tensor state to safetensors plus JSON metadata. Runtime checks the metadata label order and SHA-256 before opening weights. SQLite stores analysis scores and review feedback but never the uploaded pixels. Audit entries form a SHA-256 chain. The web API accepts unauthenticated requests under a shared guest identity.

This is an IEC 62304-inspired engineering structure only; it does not establish regulatory compliance, certification, safety, or fitness for clinical use. Network isolation is a deployment property, not enforced by the code. The frontend has no runtime API other than the configured local service; font loading uses local system fonts.
