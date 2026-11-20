"""Freeze saved candidates before reading held-out features/labels; no fitting."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil

import joblib
import numpy as np
import sklearn
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix

from budget_metrics import evaluate

BASE = Path(__file__).resolve().parent
NAMES = ['logistic_regression','decision_tree','gaussian_nb','knn','rbf_svm',
         'random_forest','gradient_boosting','deep_mlp']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n',encoding='utf-8')


def run(source, output):
    contract = json.loads((BASE/'contract.json').read_text(encoding='utf-8'))
    if sha(source) != contract['source_sha256']:
        raise ValueError('Dataset differs from frozen source')
    split_path = BASE/'splits.csv'
    split_hash = sha(split_path)
    with split_path.open(encoding='utf-8',newline='') as f:
        splits = list(csv.DictReader(f))
    if len({r['commit_hash'] for r in splits}) != len(splits):
        raise ValueError('Duplicate split identities')
    if set(r['split'] for r in splits) != {'train','validation','test'}:
        raise ValueError('Invalid split labels')
    grouped = {k:[r for r in splits if r['split']==k] for k in ('train','validation','test')}
    windows = []
    for k, rows in grouped.items():
        if len(rows) != contract['split']['groups'][k]['rows']:
            raise ValueError('Split count differs from contract')
        times = [datetime.fromisoformat(r['commit_time_utc']) for r in rows]
        if times != sorted(times):
            raise ValueError('Unsorted split')
        windows.append((min(times),max(times)))
    if not (windows[0][1] < windows[1][0] and windows[1][1] < windows[2][0]):
        raise ValueError('Time overlap')
    snapshots = {}
    for name in NAMES:
        folder = BASE/'unified_validation'/name
        report = json.loads((folder/'report.json').read_text(encoding='utf-8'))
        if (report['source_sha256'] != contract['source_sha256']
            or report['splits_sha256'] != split_hash
            or report['feature_order'] != contract['features']
            or report['test_evaluated'] is not False):
            raise ValueError('Incompatible validation metadata: '+name)
        snapshots[name] = dict(parameters=report['parameters'],threshold=report['threshold'],
                               model_sha256=sha(folder/'model.joblib'),
                               report_sha256=sha(folder/'report.json'),
                               validation_ap=report['metrics']['ap'],
                               validation_budget_recall=report['metrics']['budget']['results']['skip_over_budget']['recall'])
    chosen = max(NAMES,key=lambda n:(snapshots[n]['validation_budget_recall'],snapshots[n]['validation_ap']))
    if chosen != 'random_forest':
        raise ValueError('Validation-selected candidate changed; review protocol before evaluation')
    # Fail on existing output, preserving the completed evaluation.
    output.mkdir(parents=True, exist_ok=False)
    protocol = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                    source_sha256=contract['source_sha256'],splits_sha256=split_hash,
                    feature_order=contract['features'],candidates=snapshots,
                    primary_candidate=chosen,
                    selection='Validation skip-over-budget recall, then validation AP; no test-driven reselection',
                    ranking='Risk descending, ties retain frozen split order; whole commits, 20% la+ld budget',
                    thresholds='Frozen per-model validation F1 threshold',
                    no_retraining=True,
                    limitations=['The test set has already been inspected for the early LR baseline; this is not a pristine blind confirmation set.',
                      '675 samples, 27 test positives; small-sample uncertainty.',
                      'Feature extraction/SZZ provenance and label-time availability remain unverified.',
                      'Search budgets differ by model; extensive repeated validation selection.',
                      'MLP seed 42 configuration was selected on validation; other seeds were sensitivity checks.'],
                    runtime=dict(numpy=np.__version__,sklearn=sklearn.__version__,joblib=joblib.__version__))
    for name in NAMES:
        dst=output/name
        dst.mkdir()
        src=BASE/'unified_validation'/name
        shutil.copyfile(src/'model.joblib',dst/'model.joblib')
        shutil.copyfile(src/'report.json',dst/'validation_report.json')
        if sha(dst/'model.joblib') != snapshots[name]['model_sha256']:
            raise ValueError('Snapshot mismatch')
    shutil.copyfile(split_path,output/'splits.csv')
    shutil.copyfile(BASE/'contract.json',output/'source_contract.json')
    save(output/'frozen_protocol.json',protocol)

    # Only now access test feature/label values. Fit is never called.
    with source.open(encoding='utf-8-sig',newline='') as f:
        raw=list(csv.DictReader(f))
    data={r['commit_hash']:r for r in raw}
    if len(data)!=len(raw) or set(data)!={r['commit_hash'] for r in splits}:
        raise ValueError('Identity coverage mismatch')
    test=[data[r['commit_hash']] for r in grouped['test']]
    x=np.array([[float(r[k]) for k in contract['features']] for r in test])
    y=np.array([int(r['is_bug_inducing']) for r in test])
    effort=np.array([int(r['la'])+int(r['ld']) for r in test])
    if not (np.isfinite(x).all() and (x>=0).all() and (effort>0).all() and set(y)=={0,1}):
        raise ValueError('Invalid test data')
    results=[]
    for name in NAMES:
        model=joblib.load(output/name/'model.joblib')
        if model.n_features_in_!=len(contract['features']):
            raise ValueError('Model dimension mismatch')
        scores=model.predict_proba(x)[:,list(model.classes_).index(1)]
        if not (np.isfinite(scores).all() and (scores>=0).all() and (scores<=1).all()):
            raise ValueError('Invalid scores')
        threshold=snapshots[name]['threshold']
        predicted=(scores>=threshold).astype(int)
        records=[dict(commit_hash=r['commit_hash'],label=int(label),score=float(score),
                      prediction=int(pred),effort=int(cost))
                 for r,label,score,pred,cost in zip(test,y,scores,predicted,effort)]
        with (output/name/'test_predictions.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        result=dict(model=name,threshold=threshold,ap=float(average_precision_score(y,scores)),
                    roc_auc=float(roc_auc_score(y,scores)),
                    precision=float(precision_score(y,predicted,zero_division=0)),
                    recall=float(recall_score(y,predicted)),f1=float(f1_score(y,predicted)),
                    confusion_matrix=confusion_matrix(y,predicted,labels=[0,1]).tolist(),
                    budget=evaluate(records))
        save(output/name/'test_metrics.json',result)
        results.append(result)
    baselines={name:evaluate([dict(score=str(s),label=str(label),effort=str(cost))
                             for s,label,cost in zip(order,y,effort)])
               for name,order in [('smallest_first',-effort),('chronological',np.arange(len(y),0,-1))]}
    save(output/'comparison.json',dict(test_rows=len(y),test_positive=int(y.sum()),
          primary_candidate=chosen,models=results,baselines=baselines,limitations=protocol['limitations']))
    lines=['# 八类模型固定方案测试报告','',
           '预选候选：随机森林（仅由验证集选出，不按本表重新选模）。',
           f'测试集 {len(y)} 条，正例 {int(y.sum())} 条；无重训练、无调阈值。','',
           '| 模型 | AP | ROC-AUC | Precision | Recall | F1 | 预算停止 | 预算跳过 |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in results:
        b=r['budget']['results']
        values=[r[k] for k in ('ap','roc_auc','precision','recall','f1')]+[b['strict_prefix']['recall'],b['skip_over_budget']['recall']]
        lines.append('| '+r['model']+' | '+' | '.join(f'{v:.4f}' for v in values)+' |')
    lines+=['','简单策略对照（相同预算和测试样本）：']
    for name,b in baselines.items():
        v=b['results']['skip_over_budget']
        lines.append(f"- {name}：审查 {v['reviewed']} 条、找到 {v['found']} 个正例，召回率 {v['recall']:.4f}。")
    lines+=['','限制：',*[f'- {v}' for v in protocol['limitations']]]
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if sha(source)!=contract['source_sha256'] or sha(split_path)!=split_hash:
        raise ValueError('Inputs changed during evaluation')
    print(json.dumps(dict(primary_candidate=chosen,models=results,baselines=baselines),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,default=BASE/'frozen_test_evaluation_v1')
    args=parser.parse_args()
    run(args.source,args.output)
