import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = 'ns nd nf entropy la ld lt fix ndev age nuc exp rexp sexp'.split()
OUT = Path(__file__).resolve().parent

def write(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def main(source):
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: (datetime.fromisoformat(r['commit_time']), r['commit_hash']))
    times = [datetime.fromisoformat(r['commit_time']).astimezone(timezone.utc) for r in rows]
    ids = [r['commit_hash'] for r in rows]
    x = np.array([[float(r[k]) for k in FEATURES] for r in rows])
    y = np.array([int(r['is_bug_inducing']) for r in rows])
    effort = x[:,4]+x[:,5]
    assert len(rows) == len(set(ids)) and np.isfinite(x).all() and (x >= 0).all()
    assert set(y) == {0,1} and set(x[:,7]) <= {0,1} and (effort>0).all()
    cuts = []
    for fraction in (.7,.85):
        i = int(len(rows)*fraction)
        while i < len(rows) and times[i-1] == times[i]:
            i += 1
        cuts.append(i)
    a,b = cuts
    parts = {'train':slice(0,a),'validation':slice(a,b),'test':slice(b,len(rows))}
    assert times[a-1]<times[a] and times[b-1]<times[b]
    assert all(set(y[s])=={0,1} for s in parts.values())
    contract = {
      'version':'jit14-v5-preliminary', 'source':source.name,'source_sha256':digest,
      'features':FEATURES,'label':'is_bug_inducing (0/1; use provided values unchanged)',
      'excluded_inputs':['commit_hash','author','commit_time'],
      'provenance':{'sexp':'use provided values unchanged; multi-subsystem aggregation unverified','szz':'source links not supplied','label_cutoff_at':None},
      'split':{'rule':'UTC chronological 70/15/15; keep equal timestamps together; SHA tie order',
               'groups':{k:{'rows':len(y[s]),'positive':int(y[s].sum()),'first_utc':times[s.start].isoformat(),'last_utc':times[s.stop-1].isoformat()} for k,s in parts.items()}},
      'evaluation':{'preprocessing':'StandardScaler fit on train only','seed':42,'solver':'lbfgs','max_iter':5000,
        'grid':{'C':[0.01,0.1,1,10],'class_weight':[None,'balanced']},
        'configuration_selection':'highest validation AP; ties keep grid order',
        'threshold_selection':'maximum validation F1; ties use highest threshold',
        'effort':'la+ld; stable risk-descending prefix within 20% total changed lines',
        'metrics':['ROC-AUC','AP','precision','recall','F1','confusion matrix','Recall@20% effort']},
      'runtime':{'numpy':np.__version__,'scikit_learn':sklearn.__version__,'joblib':joblib.__version__}}
    target=OUT/'contract.json'
    if target.exists() and json.loads(target.read_text(encoding='utf-8')) != contract:
        raise ValueError('Existing frozen contract differs')
    write('contract.json',contract)
    with (OUT/'splits.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['commit_hash','commit_time_utc','split'])
        for k,s in parts.items():
            w.writerows((ids[i],times[i].isoformat(),k) for i in range(s.start,s.stop))
    tr,va,te=parts.values()
    candidates=[]; best=None
    for c in contract['evaluation']['grid']['C']:
        for weight in contract['evaluation']['grid']['class_weight']:
            model=make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight=weight,solver='lbfgs',max_iter=5000,random_state=42))
            model.fit(x[tr],y[tr])
            assert model[-1].n_iter_[0]<5000
            np.testing.assert_allclose(model[0].mean_,x[tr].mean(axis=0))
            score=model.predict_proba(x[va])[:,1]
            ap=float(average_precision_score(y[va],score))
            candidates.append({'C':c,'class_weight':weight,'validation_ap':ap})
            if best is None or ap>best[0]:
                best=(ap,model,score,c,weight)
    _,model,validation,c,weight=best
    p,r,t=precision_recall_curve(y[va],validation)
    f1=np.divide(2*p[:-1]*r[:-1],p[:-1]+r[:-1],out=np.zeros_like(t),where=(p[:-1]+r[:-1])>0)
    threshold=float(t[np.flatnonzero(f1==f1.max())[-1]])
    write('selection.json',{'C':c,'class_weight':weight,'threshold':threshold,'candidates':candidates})
    joblib.dump(model,OUT/'model.joblib')
    report={}
    for name,s in [('validation',va),('test',te)]:
        score=model.predict_proba(x[s])[:,1]
        np.testing.assert_allclose(joblib.load(OUT/'model.joblib').predict_proba(x[s])[:,1],score)
        predicted=score>=threshold
        rank=np.argsort(-score,kind='stable')
        selected=rank[np.cumsum(effort[s][rank])<=.2*effort[s].sum()]
        report[name]={'roc_auc':roc_auc_score(y[s],score),'ap':average_precision_score(y[s],score),
           'precision':precision_score(y[s],predicted,zero_division=0),'recall':recall_score(y[s],predicted),
           'f1':f1_score(y[s],predicted),'confusion_matrix':confusion_matrix(y[s],predicted,labels=[0,1]).tolist(),
           'recall_at_20_percent_effort':float(y[s][selected].sum()/y[s].sum()),
           'actual_effort_fraction':float(effort[s][selected].sum()/effort[s].sum())}
        if name=='test':
            with (OUT/'test_predictions.csv').open('w',encoding='utf-8',newline='') as f:
                w=csv.writer(f);w.writerow(['commit_hash','label','score','prediction','effort'])
                w.writerows(zip(ids[s],y[s],score,predicted.astype(int),effort[s]))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    write('metrics.json',report)
    print(json.dumps({'groups':contract['split']['groups'],'C':c,'weight':weight,'threshold':threshold,'metrics':report}))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    main(parser.parse_args().source)
