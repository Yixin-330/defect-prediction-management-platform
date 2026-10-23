# OpenStack / Qt 真实数据基线

独立于模拟实验的11维离线基线；不替换原定生产14维契约，不改写原始CSV，不接管现有后端预测接口。

从项目根目录运行：

```powershell
& ./backen/.venv/Scripts/python.exe -m pip install -r backen/experiments/jit_lr/requirements.txt
& ./backen/.venv/Scripts/python.exe backen/experiments/jit_lr/pipeline.py
& ./backen/.venv/Scripts/python.exe -m unittest discover -s backen/experiments/jit_lr -p test_pipeline.py
```

默认分别处理 `data/openstack.csv` 与 `data/qt.csv`，各自训练一个模型；可用 `--project openstack` 或 `--project qt` 只运行一个项目。
默认种子42。`--source-dir`指定原数据目录，`--output`指定实验结果目录。同名实验结果会被覆盖。

## 四项处理

1. **标签**：按作者脚本，将 `bugcount>0` 转为 `is_bug_inducing=1`；空值或0转为0。
   保留 `label_was_blank` 审计标记，不进入模型。空白的含义是该数据集的否定标签约定，不能证明没有缺陷。
   `fixcount>0` 派生 `fix_audit_only`；它不参与训练，避免把缺陷引入与缺陷修复混为一谈。
   对拟保留记录，非法计数、NaN、无穷大、负数、缺单元格、重复身份会明确失败，不转换为默认标签。
2. **字段**：固定输入 `la,ld,nf,nd,ns,ent,ndev,age,nuc,aexp,asexp`。
   `aexp`是作者经验，`asexp`是作者子系统经验。缺少`lt`，不伪造补零；
   `rexp`在源数据中表示审查者经验，排除。`arexp`命名存在relative/recent差异，此轮也排除。
   不使用审查字段、未来修复信息、标签、时间、身份或工作量作为输入。
3. **缺失与尺度**：源历史特征空白保留在清洗结果中。模型Pipeline使用训练集中位数填补，
   为训练时出现过空白的列加缺失指示器，再做训练集标准化；验证/测试集只transform。
   这与作者脚本全局补零有意不同，避免把未知历史直接视为没有历史。
   `age`原始单位未获得充分证据，明确保留源尺度；不自动除以86400、不声称已经换算成天。
   `ent`保留源文件0–1尺度，只将1以上且不超过1e-12的浮点误差截为1，其余越界报错。
   作者和模拟数据的熵/年龄尺度不混用，StandardScaler参数随模型保存。
   源数据部分`ns>nd`可能来自不同分组口径，保留并计数，不强行修成假定层级。
4. **筛选和时间**：按作者时间窗口、`la>0`、`la+ld<=10000`、`nf<=100`筛选。
   排除原因按先后顺序只记录一个，所有被筛除提交可追溯。
   按Unix时间与完整SHA排序，近似70/15/15切分；同一时间戳不跨集合。
   每个项目独立训练，不混合数据或对测试集重采样；每个划分要求正负类都存在。

## 输出

位于 `artifacts/openstack/` 与 `artifacts/qt/`：

- `samples.csv`：筛选后数据，保留空特征及标签审计标记，含split。
- `excluded_rows.csv`：源文件行号、提交ID、筛除原因。
- `splits.csv`：提交身份、时间与划分。
- `feature_schema.json`：独立契约版本、输入白名单、尺度及排除字段说明。
- `dataset_manifest.json`：原文件SHA256、筛选统计、来源、标签口径和限制。
- `model.joblib`：填补、缺失标记、标准化、逻辑回归的完整Pipeline。
- `model_metadata.json`：特征顺序、训练配置、依赖版本、填补参数及产物校验值。
- `metrics.json`、`report.md`、`test_predictions.csv`：各划分指标、报告、测试集逐条预测。

分类阈值固定0.5，不调参；`C=1.0, solver=lbfgs, max_iter=5000`。
工作量感知召回使用`la+ld`，按风险分数降序排列，以不超过总工作量20%的完整提交前缀计算。
这不同于按风险/工作量密度排序或允许部分检查的口径，不能未经对齐直接对比论文数值。

## 使用限制

源CSV没有修复发现日期或每条标签何时可用的记录，时间划分只约束提交，不能证明训练标签当时已经可获得。
这是归档数据上的离线基线，不是严格历史回放，也不能独立验证特征提取未读取未来信息。
不得将文件中最新提交时间当作标签观察截止时间；元数据的`label_cutoff_at`保留null。

接入线上前仍须核实`age`单位、熵公式、身份和路径处理及as-of提取逻辑。
线上输入必须对齐本次版本，不能把14维模拟模型的字段直接喂给本模型。
数据特征的仓库提取、SZZ复现、14维生产模型、SHAP及系统联调不在本实验中宣称完成。

来源：

- https://github.com/software-rebels/JITMovingTarget/blob/master/scripts/load_data.r
- https://github.com/software-rebels/JITMovingTarget/blob/master/scripts/experimental_settings.r
- https://posl.ait.kyushu-u.ac.jp/~kamei/publications/McIntosh_TSE2017.pdf
