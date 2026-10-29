import csv, hashlib, json
from functools import lru_cache
from pathlib import Path
from ..core.config import BASELINE_DIR, GAN_DIR, LABELS, DATA_DIR

MODELS = {
    "baseline": (DATA_DIR / "converted" / "baseline" / "best_model.safetensors", BASELINE_DIR / "results", ""),
    **{f"{x}": (DATA_DIR / "converted" / x / "best_model.safetensors", GAN_DIR / "results", f"_{x}") for x in "ABCD"},
}

def model_files(name):
    if name not in MODELS: raise ValueError("Unknown model.")
    weights, results, suffix = MODELS[name]
    thresholds = results / f"validation_thresholds{suffix}.csv"
    metrics = results / ("per_finding_test_metrics.csv" if name == "baseline" else f"per_finding_test_metrics{suffix}.csv")
    return weights, thresholds, metrics

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def card(name):
    weights, thresholds_path, metrics_path = model_files(name)
    thresholds={r["finding"]:float(r["threshold"]) for r in read_rows(thresholds_path)}
    metrics={r["finding"]:r for r in read_rows(metrics_path)}
    results=MODELS[name][1]
    ci_path=(BASELINE_DIR/"results"/"bootstrap_confidence_intervals.csv") if name=="baseline" else results/"bootstrap_confidence_intervals_all_experiments.csv"
    ci={}
    if ci_path.exists():
        for row in read_rows(ci_path):
            if name=="baseline": ci[(row["scope"],row["metric"])]=row
            elif row.get("experiment")==name: ci[(row["scope"],row["metric"])]=row
    rows=[]
    for label in LABELS:
        m=metrics.get(label,{})
        auroc_ci=ci.get((label,"auroc"),{})
        ap_ci=ci.get((label,"average_precision"),{})
        low=float(m.get("auroc_ci_low") or auroc_ci.get("ci_low") or 0); high=float(m.get("auroc_ci_high") or auroc_ci.get("ci_high") or 0)
        ap=float(m.get("average_precision", 0) or 0); n=int(float(m.get("n_test_pos", 0) or 0))
        reliability="Low reliability" if low<.75 or ap<.10 or n<100 else "Moderate reliability"
        rows.append({"finding":label,"threshold":thresholds.get(label),"reliability":reliability,"auroc":m.get("auroc"),"average_precision":m.get("average_precision"),"n_test_pos":n,"auroc_ci_low":m.get("auroc_ci_low") or auroc_ci.get("ci_low"),"auroc_ci_high":m.get("auroc_ci_high") or auroc_ci.get("ci_high"),"ap_ci_low":m.get("ap_ci_low") or ap_ci.get("ci_low"),"ap_ci_high":m.get("ap_ci_high") or ap_ci.get("ci_high")})
    return {"name":name,"weights_ready":weights.exists(),"sha256":sha256(weights) if weights.exists() else None,"findings":rows}
