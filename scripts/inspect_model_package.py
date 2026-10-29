"""Safely inspect PyTorch zip checkpoints without importing pickle globals."""
import csv, pathlib, re, zipfile, pickletools
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=[ROOT/'output_baseline/models/best_model.pt',*[ROOT/f'output_gan/models/exp_{x}/best_model.pt' for x in 'ABCD']]
PARAM=re.compile(r'^(conv1|bn1|layer[1-4]\.\d+|fc)')

def inspect(path):
    with zipfile.ZipFile(path) as z:
        member=next(n for n in z.namelist() if n.endswith('/data.pkl'))
        ops=list(pickletools.genops(z.read(member)))
    strings=[a for op,a,_ in ops if op.name in {'BINUNICODE','SHORT_BINUNICODE','UNICODE'} and isinstance(a,str)]
    keys=[]; labels=[]; shapes={}
    for i,(op,arg,_) in enumerate(ops):
        if op.name not in {'BINUNICODE','SHORT_BINUNICODE','UNICODE'} or not isinstance(arg,str):continue
        if PARAM.match(arg) and (arg.endswith(('.weight','.bias','.running_mean','.running_var','.num_batches_tracked'))):
            keys.append(arg)
            tail=ops[i+1:]
            try:
                p=next(j for j,x in enumerate(tail) if x[0].name=='BINPERSID')
                dims=[]
                for x in tail[p+1:]:
                    if x[0].name in {'BININT','BININT1','BININT2','LONG1','LONG4'}:dims.append(int(x[1]))
                    if x[0].name in {'TUPLE','TUPLE1','TUPLE2','TUPLE3'}:
                        shapes[arg]=tuple(dims[1:])
                        break
            except StopIteration:pass
    if 'labels' in strings:
        idx=ops.index(next(x for x in ops if x[0].name in {'BINUNICODE','SHORT_BINUNICODE'} and x[1]=='labels'))
        labels=[x[1] for x in ops[idx+1:] if x[0].name in {'BINUNICODE','SHORT_BINUNICODE'} and x[1] in {'Atelectasis','Cardiomegaly','Consolidation','Edema','Effusion','Emphysema','Fibrosis','Hernia','Infiltration','Mass','Nodule','Pleural_Thickening','Pneumonia','Pneumothorax'}]
        labels=labels[:14]
    return keys,shapes,labels,strings

def main():
    for path in FILES:
        if not path.exists():print('MISSING',path);continue
        keys,shapes,labels,strings=inspect(path)
        top=[s for s in strings if s in {'model','epoch','score','cfg_hash','labels','experiment'}]
        print(f'\n{path.relative_to(ROOT)}\ncheckpoint keys={top}\ntensor shapes ({len(keys)} tensors):')
        for key in keys:print(f'  {key}: {shapes.get(key,"unparsed")!r}')
        print('labels=',labels)
    for p in sorted([ROOT/'output_baseline/results/validation_thresholds.csv',ROOT/'output_baseline/results/test_predictions.csv',ROOT/'output_baseline/results/per_finding_test_metrics.csv',ROOT/'output_gan/results/validation_thresholds_D.csv',ROOT/'output_gan/results/test_predictions_D.csv',ROOT/'output_gan/results/per_finding_test_metrics_D.csv']):
        with p.open(encoding='utf-8-sig',newline='') as f:print(f'CSV {p.relative_to(ROOT)} headers={next(csv.reader(f))}')
if __name__=='__main__':main()
