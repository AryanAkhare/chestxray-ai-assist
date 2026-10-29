"""Parity acceptance check. Requires user-provided NIH test images and converted models."""
import csv, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.app.inference.preprocess import load_image
from backend.app.inference.predict import predict

MODELS={'baseline':(ROOT/'output_baseline/results/test_predictions.csv',ROOT/'output_baseline/results/validation_thresholds.csv')}
for x in 'ABCD': MODELS[x]=(ROOT/f'output_gan/results/test_predictions_{x}.csv',ROOT/f'output_gan/results/validation_thresholds_{x}.csv')

def test_parity_at_least_50_images():
    images=sorted((ROOT/'tests/parity_images').glob('*'))
    assert len(images)>=50, 'Provide at least 50 NIH test images in tests/parity_images/ before parity can be verified.'
    image_ids={p.name for p in images}
    for model,(csv_path,_) in MODELS.items():
        with csv_path.open(encoding='utf-8-sig',newline='') as f: rows={r['image_id']:r for r in csv.DictReader(f)}
        matched=[p for p in images if p.name in rows]
        assert len(matched)>=50, f'{model}: fewer than 50 image IDs match saved test predictions.'
        for path in matched[:50]:
            image,_=load_image(path.read_bytes(),path.name)
            scores={f['finding']:f['score'] for f in predict(image,model)['findings']}
            for label,score in scores.items():
                expected=float(rows[path.name][f'prob_{label}'])
                assert abs(score-expected)<1e-4, f'{model}/{path.name}/{label}: {score} != {expected}'
