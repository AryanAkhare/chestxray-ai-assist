# Verification report

## Verified from supplied artifacts

- Five best checkpoints exist: baseline and experiments A, B, C, D. Each has the expected ResNet18 state-dictionary names and final fully connected layer serialized as 14 outputs over 512 input features. Checkpoint metadata contains `model`, `epoch`, `score`, `cfg_hash`, `labels`, and for GAN runs `experiment`.
- All five checkpoints carry the expected alphabetical 14-label order. The threshold, prediction, and metric CSV headers have been inspected; saved prediction columns contain `true_<finding>` and `prob_<finding>` for every label.
- Baseline and GAN model configuration JSON files agree on the 14 labels and 224 × 224 grayscale preprocessing description.
- The model configuration JSON only names ImageNet mean/std; the numeric values were confirmed in the supplied notebooks (`MEAN=[0.485,0.456,0.406]`, `STD=[0.229,0.224,0.225]`).
- The safe checkpoint archive scanner parsed all 122 tensor names and shapes in each of the five checkpoints; `fc.weight` is `(14, 512)` throughout.
- `python scripts/check_thresholds.py` read all 25,596 test prediction rows for each model and calculated 358,344 per-finding threshold flags per model. `python -m pytest tests/test_thresholds.py -q` passed (1 test).
- `python -m compileall -q backend scripts tests` completed successfully.
- No checkpoint was unpickled for inspection. The provided safetensors converted models load and produce model outputs.

## Verified after feature additions

- Frontend production bundle builds successfully with `npm run build`.
- Three Python tests pass for threshold data, preprocessing, and Grad-CAM.
- A synthetic image produces a Grad-CAM map at the image's dimensions; changing the finding changes the map.
- API routes for comparison, batch, reports, heat maps, and preview retrieval are registered.
- Direct function smoke checks passed for two-model comparison and JSON/CSV/PDF report response creation.

## Not verified

- Score parity on 50 test images: `tests/parity_images/` contains no supplied images.
- End-to-end API requests: local socket access is blocked in this execution sandbox, and the direct Windows asyncio test loop hangs while creating its self-pipe.
- Frontend interactions in a browser: no UI browser test or screenshot was captured.
- API end-to-end requests, screenshot capture, dependency audit, coverage, accessibility scan, PDF output, batch processing, model comparison endpoint, and performance benchmarks.
- The repository has not been validated on clinical data, external data, or any intended clinical workflow.

## Known gaps in this delivery

This remains a research prototype, not an acceptance-tested release. API deletion, lockout/rate limiting, and exhaustive security tests remain unimplemented. Score parity still requires at least 50 supplied test images. See `docs/requirements_traceability.md` for exact status. The local service must not be used for diagnosis or clinical decisions.
