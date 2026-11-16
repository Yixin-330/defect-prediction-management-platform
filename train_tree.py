import csv, json, hashlib, argparse
from pathlib import Path
from datetime import datetime
import numpy as np
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (average_precision_score, roc_auc_score, precision_recall_curve,
                             precision_score, recall_score, f1_score, confusion_matrix)
from budget_metrics import evaluate

def main(source):
    base = Path(__file__).resolve().parent
    contract = json.loads((base/'contract.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != contract['source_sha256']:
        raise ValueError('Dataset differs from frozen contract')
    with source.open(encoding='utf-8-sig', newline='') as f:
        data = {r['commit_hash']: r for r in csv.DictReader(f)}
    with (base/'splits.csv').open(encoding='utf-8', newline='') as f:
        split = list(csv.DictReader(f))
    ids = [r['commit_hash'] for r in split]
    assert len(set(ids)) == len(ids) == len(data) and set(ids) == set(data)
    assert all(datetime.fromisoformat(r['commit_time_utc']) == datetime.fromisoformat(data[r['commit_hash']]['commit_time']) for r in split)
    groups = {k: [r['commit_hash'] for r in split if r['split']==k] for k in ('train','validation','test')}
    assert sum(map(len,groups.values())) == len(split)
    assert all(len(v) == contract['split']['groups'][k]['rows'] for k,v in groups.items())
    features = contract['features']
    def arrays(group):
        rows = [data[i] for i in groups[group]]
        x = np.array([[float(r[k]) for k in features] for r in rows])
        y = np.array([int(r['is_bug_inducing']) for r in rows])
        assert np.isfinite(x).all() and set(y) == {0,1}
        return x,y
    xt,yt = arrays('train')
    xv,yv = arrays('validation')
    out = base/'decision_tree'
    out.mkdir(exist_ok=True)
    config = {'source_sha256':digest, 'contract_version':contract['version'],
              'splits_sha256':hashlib.sha256((base/'splits.csv').read_bytes()).hexdigest(),
              'features':features,'preprocessing':'none','seed':42,
              'grid':{'max_depth':[2,4,6,None],'min_samples_leaf':[5,15,30],'class_weight':[None,'balanced']},
              'selection':'validation AP; ties use first grid entry',
              'threshold':'maximize validation F1; ties use highest threshold',
              'test_evaluated':False}
    def write(name, obj):
        (out/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    old = out/'protocol.json'
    if old.exists() and json.loads(old.read_text(encoding='utf-8')) != config:
        raise ValueError('Existing tree protocol differs')
    write('protocol.json',config)
    trials=[]; best=None
    for depth in config['grid']['max_depth']:
        for leaf in config['grid']['min_samples_leaf']:
            for weight in config['grid']['class_weight']:
                params=dict(max_depth=depth,min_samples_leaf=leaf,class_weight=weight)
                tree=DecisionTreeClassifier(**params,random_state=42).fit(xt,yt)
                score=tree.predict_proba(xv)[:,1]
                ap=float(average_precision_score(yv,score))
                trials.append(dict(params,validation_ap=ap))
                if best is None or ap>best[0]:
                    best=(ap,tree,score,params)
    ap,tree,score,params=best
    p,r,t=precision_recall_curve(yv,score)
    f=np.divide(2*p[:-1]*r[:-1],p[:-1]+r[:-1],out=np.zeros_like(t),where=(p[:-1]+r[:-1])>0)
    threshold=float(t[np.flatnonzero(f==f.max())[-1]])
    predicted=score>=threshold
    rows=[dict(commit_hash=i,label=int(y),score=float(s),prediction=int(z),
               effort=int(data[i]['la'])+int(data[i]['ld'])) for i,y,s,z in zip(groups['validation'],yv,score,predicted)]
    with (out/'validation_predictions.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    budget=evaluate(rows)
    metrics=dict(samples=len(yv), positives=int(yv.sum()), roc_auc=float(roc_auc_score(yv,score)), ap=ap,
                 precision=float(precision_score(yv,predicted,zero_division=0)), recall=float(recall_score(yv,predicted)),
                 f1=float(f1_score(yv,predicted)), confusion_matrix=confusion_matrix(yv,predicted,labels=[0,1]).tolist(),
                 budget=budget)
    joblib.dump(tree,out/'model.joblib')
    np.testing.assert_array_equal(joblib.load(out/'model.joblib').predict_proba(xv)[:,1],score)
    write('selection.json',dict(parameters=params,threshold=threshold,trials=trials))
    write('validation_metrics.json',metrics)
    print(json.dumps(dict(parameters=params,threshold=threshold,validation=metrics)))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    main(parser.parse_args().source)
