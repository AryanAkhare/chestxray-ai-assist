import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("APP_DATA_DIR", ROOT / "data")).resolve()
BASELINE_DIR = Path(os.getenv("MODEL_BASELINE", ROOT / "output_baseline")).resolve()
GAN_DIR = Path(os.getenv("MODEL_GAN", ROOT / "output_gan")).resolve()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024
LABELS = [
    "Atelectasis", "Cardiomegaly", "Consolidation", "Edema", "Effusion",
    "Emphysema", "Fibrosis", "Hernia", "Infiltration", "Mass", "Nodule",
    "Pleural_Thickening", "Pneumonia", "Pneumothorax",
]
DISCLAIMER = "Research prototype. Not a medical device. Not for diagnosis or clinical decisions. Outputs require review by a qualified clinician."
SCORE_NOTE = "Scores are model outputs, not calibrated probabilities. A score below threshold does not exclude disease; a score above threshold does not confirm it."
GRADCAM_NOTE = "Heat maps indicate image regions that influenced the model output; they are not validated clinical explanations and can highlight irrelevant regions."
