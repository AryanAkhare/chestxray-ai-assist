# User manual

1. Install Python 3.11 and the pinned packages in `backend/requirements.txt`; install Node.js and packages in `frontend/package.json`.
2. From the repository root run `python scripts/convert_checkpoints.py` once to convert the trusted local checkpoints. Converted model files are written under ignored `data/converted/` folders.
3. Start the API using `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` and the web interface with `npm install` then `npm run dev` from `frontend/`.
4. On first launch, create a local administrator password. Later sessions authenticate through the local login screen.
5. Select a model, upload a PNG, JPEG, or DICOM study, review score/threshold pairs and input warnings, then record reviewer agreement, disagreement, or uncertainty.
6. Images are processed in memory and are not stored. Analysis scores, timestamps, model hashes, input hashes, case IDs, and feedback are stored in local SQLite. DICOM patient tags and pixel data are not returned to the interface.

The tool is for research and education only. It is not a medical device, does not provide a diagnosis, and must not be used to make or delay clinical decisions. All output requires qualified clinician review.
