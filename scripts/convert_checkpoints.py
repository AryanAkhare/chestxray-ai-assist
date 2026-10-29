"""Convert trusted local training checkpoints into runtime-only safetensors files."""
import hashlib, json
from pathlib import Path
import torch
from safetensors.torch import save_file

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"baseline": ROOT/"output_baseline/models/best_model.pt", **{x:ROOT/f"output_gan/models/exp_{x}/best_model.pt" for x in "ABCD"}}
LABELS = ["Atelectasis","Cardiomegaly","Consolidation","Edema","Effusion","Emphysema","Fibrosis","Hernia","Infiltration","Mass","Nodule","Pleural_Thickening","Pneumonia","Pneumothorax"]

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    for name, source in SOURCES.items():
        if not source.is_file(): raise SystemExit(f"Missing checkpoint: {source}")
        # Only run this against trusted, locally supplied model checkpoints.
        checkpoint=torch.load(source,map_location="cpu",weights_only=True)
        if not isinstance(checkpoint,dict) or "model" not in checkpoint or "labels" not in checkpoint: raise SystemExit(f"Unexpected checkpoint format: {source}")
        labels=list(checkpoint["labels"])
        if labels != LABELS: raise SystemExit(f"Checkpoint label order mismatch: {name}: {labels}")
        state={k.removeprefix("module."):v.detach().cpu().contiguous() for k,v in checkpoint["model"].items()}
        if tuple(state.get("fc.weight",torch.empty(0)).shape)!=(14,512): raise SystemExit(f"Unexpected fc.weight shape in {source}")
        out=ROOT/"data/converted"/name
        out.mkdir(parents=True,exist_ok=True)
        target=out/"best_model.safetensors"
        save_file(state,str(target))
        metadata={"name":name,"architecture":"torchvision ResNet18 + Linear(512,14)","labels":labels,"source_sha256":digest(source),"weights_sha256":digest(target),"source_file":str(source.relative_to(ROOT))}
        (out/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
        print(f"{name}: {len(state)} tensors; keys={list(checkpoint.keys())}; fc.weight={tuple(state['fc.weight'].shape)}; {target}")

if __name__=="__main__": main()
