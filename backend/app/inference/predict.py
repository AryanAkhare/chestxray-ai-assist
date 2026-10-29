import json
from pathlib import Path
import torch
import torch.nn.functional as F
import io
import numpy as np
from PIL import Image
from torchvision.models import resnet18
from safetensors.torch import load_file
from .registry import MODELS, model_files, card, sha256
from .preprocess import preprocess
from ..core.config import LABELS

_cache={}

def load_model(name):
    weights,_,_=model_files(name)
    meta_path=weights.parent/"metadata.json"
    if not weights.is_file() or not meta_path.is_file(): raise RuntimeError("Model weights are not converted. Run python scripts/convert_checkpoints.py first.")
    meta=json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("labels") != LABELS or meta.get("weights_sha256") != sha256(weights): raise RuntimeError("Model metadata or SHA-256 verification failed; refusing to load weights.")
    if name not in _cache:
        with torch.inference_mode(False):
            model=resnet18(weights=None); model.fc=torch.nn.Linear(512,14)
            model.load_state_dict(load_file(str(weights),device="cpu"),strict=True)
            device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device).eval()
        _cache[name]=(model,device,meta)
    return _cache[name]

@torch.inference_mode()
def predict(image,name):
    model,device,meta=load_model(name)
    x=torch.from_numpy(preprocess(image)).unsqueeze(0).to(device)
    scores=torch.sigmoid(model(x))[0].detach().cpu().tolist()
    c=card(name)
    findings=[]
    for row,score in zip(c["findings"],scores):
        threshold=row["threshold"]
        findings.append({**row,"score":score,"above_threshold":score>=threshold if threshold is not None else False})
    findings.sort(key=lambda r:r["score"],reverse=True)
    return {"model":name,"model_sha256":meta["weights_sha256"],"findings":findings}

def gradcam(image,name,finding,output_size=None):
    if finding not in LABELS: raise ValueError("Unknown finding.")
    model,device,_=load_model(name)
    activations=[]; gradients=[]
    def capture(_module,_inputs,output):
        activations.append(output)
        output.register_hook(lambda grad: gradients.append(grad))
    handle=model.layer4[-1].register_forward_hook(capture)
    try:
        model.zero_grad(set_to_none=True)
        x=torch.from_numpy(preprocess(image)).unsqueeze(0).to(device)
        logits=model(x)
        logits[0,LABELS.index(finding)].backward()
        if not activations or not gradients: raise RuntimeError("Could not calculate heat map gradients.")
        weights=gradients[0].mean(dim=(2,3),keepdim=True)
        signed=(weights*activations[0]).sum(dim=1,keepdim=True)
        cam=torch.relu(signed)
        # Some class/layer combinations have no positive Grad-CAM contribution;
        # retain an absolute influence map in that case instead of returning blank.
        if float(cam.max()) <= 1e-12: cam=torch.abs(signed)
        output_width,output_height=output_size or image.size
        cam=F.interpolate(cam,size=(output_height,output_width),mode="bilinear",align_corners=False)[0,0]
        lo,hi=cam.min(),cam.max()
        cam=(cam-lo)/(hi-lo).clamp_min(1e-12)
        values=cam.detach().cpu().numpy()
        red=np.clip(1.5*values-0.25,0,1)
        green=np.clip(1.5-np.abs(2*values-1)*1.5,0,1)
        blue=np.clip(1.0-1.5*values,0,1)
        rgb=(np.stack([red,green,blue],axis=-1)*255).astype(np.uint8)
        out=io.BytesIO(); Image.fromarray(rgb,mode="RGB").save(out,format="PNG")
        return out.getvalue()
    finally:
        handle.remove(); model.zero_grad(set_to_none=True)
