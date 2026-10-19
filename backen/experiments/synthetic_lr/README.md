# 模拟数据逻辑回归实验

使用 14 维原始数值字段，运行 `StandardScaler → LogisticRegression`。
这是独立实验，不代表已确认生产技术栈或最终特征契约。

从项目根目录运行（PowerShell）：

```powershell
python -m venv backen/.venv
& ./backen/.venv/Scripts/python.exe -m pip install -r backen/experiments/synthetic_lr/requirements.txt
& ./backen/.venv/Scripts/python.exe backen/experiments/synthetic_lr/train.py
```

默认生成 2000 条记录，种子 42，按合成提交时间先后划分为 1400/300/300。
使用 `--samples`、`--seed`、`--output` 可修改参数；同名输出会被覆盖。
训练集用于拟合，验证集和测试集独立评估；当前没有参数选择，分类阈值固定 0.5。
标准化只在训练集拟合，随模型一起保存；标签、身份、时间、工作量不进入特征。

输出位于 `artifacts/`：

- `samples.csv`：原始模拟数据，标签名为 `is_bug_inducing`。
- `splits.csv`：固定划分及提交身份。
- `model.joblib`：标准化和逻辑回归组成的完整 Pipeline。
- `metadata.json`：字段顺序、模拟契约版本、依赖版本、种子、参数和文件校验值。
- `metrics.json`、`report.md`：分类指标和工作量感知指标。
- `test_predictions.csv`：测试集逐条预测。
- `sample_prediction.json`：不含标签的单条输入及预测输出。

特征固定顺序：`ns, nd, nf, entropy, la, ld, lt, fix, ndev, age, nuc, exp, rexp, sexp`。
计数为非负整数，`fix` 为 0/1；`entropy` 是模拟文件变更行数分布的以 2 为底的熵，
`age` 单位为天，`rexp` 是模拟的近期经验权重。范围和变量关系仅为模拟，
没有从真实 Git 历史提取，不支持据此验证真实提取算法。

标签使用带噪声的人工概率规则采样，不是 SZZ，也不是由 `fix` 直接复制。
没有真实标签观察截止时间，不能把这份数据用作 SZZ 标签验收。
生成器各记录间不构成完整、一致的仓库历史。

所有指标仅衡量对模拟规则的拟合，不能用于声称真实缺陷预测效果。
本实验不提供 SHAP、生产推理接口或高/中/低优先级阈值。
完整 OpenSpec 任务中的真实数据、特征契约、模型对比与系统联调仍未完成。

加载与预测示例（在已安装上述依赖的 Python 中）：

```python
import json
import joblib
from pathlib import Path

folder = Path("backen/experiments/synthetic_lr/artifacts")
metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
sample = json.loads((folder / "sample_prediction.json").read_text(encoding="utf-8"))
assert sample["feature_schema_version"] == metadata["feature_schema_version"]
features = sample["input"]["features"]
assert set(features) == set(metadata["feature_order"])
x = [[features[name] for name in metadata["feature_order"]]]
pipeline = joblib.load(folder / "model.joblib")
print(pipeline.predict_proba(x)[0, list(pipeline.classes_).index(1)])
```
