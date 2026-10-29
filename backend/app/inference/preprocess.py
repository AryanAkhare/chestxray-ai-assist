from io import BytesIO
from PIL import Image, ImageStat
import numpy as np

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None]
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None]
MAX_PIXELS = 100_000_000

def load_image(content: bytes, filename: str):
    if len(content) > 50 * 1024 * 1024:
        raise ValueError("File exceeds the 50 MB upload limit.")
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix not in {"png", "jpg", "jpeg", "dcm", "dicom"}:
        raise ValueError("Use a PNG, JPEG, or DICOM image.")
    if suffix in {"dcm", "dicom"}:
        try:
            import pydicom
            ds = pydicom.dcmread(BytesIO(content), force=False)
            pixels = ds.pixel_array
            if pixels.ndim == 3:
                pixels = pixels[0]
            if pixels.ndim != 2:
                raise ValueError("Only two-dimensional images are supported.")
            pixels = pixels.astype(np.float32)
            pixels = pixels * float(getattr(ds, "RescaleSlope", 1)) + float(getattr(ds, "RescaleIntercept", 0))
            try:
                from pydicom.pixels import apply_voi_lut
                pixels = apply_voi_lut(pixels, ds).astype(np.float32)
            except Exception:
                pass
            lo, hi = np.percentile(pixels, [0.5, 99.5])
            if hi <= lo: hi = lo + 1
            pixels = np.clip((pixels - lo) * 255 / (hi - lo), 0, 255).astype(np.uint8)
            if str(getattr(ds, "PhotometricInterpretation", "")) == "MONOCHROME1":
                pixels = 255 - pixels
            image = Image.fromarray(pixels, mode="L")
            warnings = []
            if getattr(ds, "Modality", "") not in {"CR", "DX"}: warnings.append("DICOM modality is not CR or DX.")
            if "LAT" in str(getattr(ds, "ViewPosition", "")).upper(): warnings.append("Lateral view; model training used frontal images.")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("DICOM could not be decoded.") from exc
    else:
        signature = content[:8]
        if suffix == "png" and signature != b"\x89PNG\r\n\x1a\n": raise ValueError("File extension does not match PNG content.")
        if suffix in {"jpg", "jpeg"} and not content.startswith(b"\xff\xd8\xff"): raise ValueError("File extension does not match JPEG content.")
        try:
            image = Image.open(BytesIO(content))
            image.verify()
            image = Image.open(BytesIO(content)).convert("L")
        except Exception as exc:
            raise ValueError("Image is corrupt or unsupported.") from exc
        warnings = []
    if image.width * image.height > MAX_PIXELS:
        raise ValueError("Image dimensions exceed the safe pixel limit.")
    w, h = image.size
    if min(w, h) < 256: warnings.append("Low input resolution may reduce useful detail.")
    if max(w, h) / max(1, min(w, h)) > 2.0: warnings.append("Unusual aspect ratio; input will be resized without preserving aspect ratio.")
    if ImageStat.Stat(image).stddev[0] < 4: warnings.append("Image intensity is nearly uniform.")
    return image, warnings

def preprocess(image):
    resized = image.convert("L").resize((224, 224), Image.Resampling.BILINEAR)
    gray = np.asarray(resized, dtype=np.uint8).astype(np.float32) / 255.0
    rgb = np.repeat(gray[None, :, :], 3, axis=0)
    return (rgb - MEAN) / STD
