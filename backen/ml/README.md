# JIT 模型训练与实验交付

本目录保存八类模型的可复现训练入口，以及供后端进程内调用的实验模型包。
与仓库根目录的既有训练脚本及在线模型保持独立；本次上传不会自动切换在线服务。

## 安装

在仓库根目录使用 Python 3.11：

```powershell
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r backen/ml/requirements.txt
```

固定依赖与模型产物生成环境见requirements.txt和handoff_v1/manifest.json。
SVM使用当前固定环境中的概率输出接口，该接口有未来弃用提示；依赖升级应重新验证，不要直接跨版本加载。

## 数据准备

原始CSV不在仓库内。由数据负责人提供冻结版本，示例保存到本地data/local/feature_dataset.csv。
SHA256必须为：

```text
833e016630cbc09d042f45597f4c4f3241d47162cfe16c7c3ab7be569943e198
```

该版本有675条记录，字段为commit_hash、author、commit_time、14维特征及is_bug_inducing。
输入字段、数据来源限制和标签状态见training/contract.json；固定划分见training/splits.csv。
缺少文件或哈希不匹配会失败，不会自动下载未知来源数据或悄悄重新划分。
数据来源仍需补齐仓库快照、提取代码、sexp口径和SZZ观察截止信息；现有模型仅用于实验联调。
文件编码或换行变化也会改变哈希，应由数据负责人发布可追溯版本而非绕过校验。

## 训练与验证

```powershell
# 运行全部八类模型；默认输出在training/unified_validation（已忽略）
& ./.venv/Scripts/python.exe backen/ml/training/train_validation.py data/local/feature_dataset.csv

# 只新增或重跑指定模型
& ./.venv/Scripts/python.exe backen/ml/training/train_validation.py data/local/feature_dataset.csv --models gaussian_nb

# 已完成MLP训练后检查固定种子的稳定性
& ./.venv/Scripts/python.exe backen/ml/training/check_mlp_stability.py data/local/feature_dataset.csv
```

模型注册名：logistic_regression、decision_tree、gaussian_nb、knn、rbf_svm、random_forest、gradient_boosting、deep_mlp。
472条训练、101条验证、102条测试；默认训练入口不评估测试集。
参数选择：验证AP；阈值选择：验证F1，相同时保留较高阈值。
各模型搜索范围及预处理不同，试验预算不同，不能称为等预算最优搜索。
统计预处理只在训练集拟合；MLP以训练损失停止，不随机从时间划分中另抽验证数据。

如使用自定义--output，模型稳定性检查默认路径需保持training/unified_validation。
历史报告位于experiments/reports/jit14-v5，记录的是已完成实验，不会因重新训练自动覆盖。

## 固定方案测试

先完成八模型验证，评估程序会复制模型快照并冻结配置，然后才读取测试特征/标签：

```powershell
& ./.venv/Scripts/python.exe backen/ml/training/freeze_and_evaluate.py data/local/feature_dataset.csv
```

已有输出不会被覆盖。此版本历史上已查看早期逻辑回归测试结果，不属于全盲确认集。
评估后不再根据测试成绩调整参数或挑选模型。历史随机森林预选由验证预算指标确定，
但测试时未超过小提交优先，不能把交付包理解为生产效果承诺。

## 后端联调

后端从handoff_v1/adapter.py导入Predictor。提供包路径，调用predict_batch，详见handoff_v1/README.md。
默认逻辑回归仅服务首条MVP链路，可切换八模型；输入是原始具名14维特征，不传标准化结果。
SHAP、行级定位和修复建议未实现。后端负责运行状态、模型/数据版本关联和持久化。

```powershell
& ./.venv/Scripts/python.exe backen/ml/handoff_v1/adapter.py backen/ml/handoff_v1/sample_request.json
& ./.venv/Scripts/python.exe -m unittest discover -s backen/ml/handoff_v1 -p test_adapter.py
```

只加载仓库中可信模型文件；joblib不是安全的用户上传格式。
不要提交虚拟环境、缓存、原始数据、密钥或本地训练中间文件。
