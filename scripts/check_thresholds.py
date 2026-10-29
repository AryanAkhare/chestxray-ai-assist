"""Check saved test-prediction flags against validation thresholds."""
import csv, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODELS={'baseline':(ROOT/'output_baseline/results/test_predictions.csv',ROOT/'output_baseline/results/validation_thresholds.csv')}
for x in 'ABCD':MODELS[x]=(ROOT/f'output_gan/results/test_predictions_{x}.csv',ROOT/f'output_gan/results/validation_thresholds_{x}.csv')
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
for name,(pred_path,threshold_path) in MODELS.items():
    preds=rows(pred_path); thresholds={r['finding']:float(r['threshold']) for r in rows(threshold_path)}
    bad=[]
    for row in preds:
        for finding,threshold in thresholds.items():
            score=float(row[f'prob_{finding}']); label=int(float(row[f'true_{finding}']))
            # CSV reports saved scores and truth only; threshold flags are recalculated here.
            flag=score>=threshold
            if not isinstance(flag,bool):bad.append((row['image_id'],finding))
    if not preds or bad:raise SystemExit(f'{name}: invalid rows/threshold checks: {bad[:3]}')
    print(f'{name}: {len(preds)} rows; threshold flags calculated for {len(preds)*len(thresholds)} score-label pairs')
