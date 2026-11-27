# 用户数据集训练适配 v1

新增training/user_training.py，与675条冻结历史入口相互独立。
这是可由后端调用的离线训练服务和CLI，不包含文件上传HTTP接口、任务调度或数据库。
CSV来源和标签语义仍需数据验收，输入检查不等同于SZZ真实性验收。

## 数据要求

列名：project_id、commit_hash、commit_time、is_bug_inducing，以及固定14维：
ns、nd、nf、entropy、la、ld、lt、fix、ndev、age、nuc、exp、rexp、sexp。
可有author等审计列，不进入模型。唯一键为project_id+commit_hash，跨项目同SHA不覆盖。
SHA为完整小写40位；时间带时区；特征为原始数值、非负有限，计数为整数。
缺失特征或未知标签明确拒绝，不自动填零，不将无标签视作负例。
工作量评估要求la+ld>0。训练和验证整体均须包含两个类别；测试可以单类别，但本入口不评估测试。

先在根目录安装backen/ml/requirements.txt。只预览而不训练：

```powershell
& ./.venv/Scripts/python.exe backen/ml/training/user_training.py data/local/input.csv --preview-only
```

## 划分

- 默认per_project：在每个项目内按UTC时间70/15/15划分，同一时间戳不拆开；各项目均需有非空的三个集合。
- global：整个数据集按统一时间划分，适合全局历史时点约束；各项目未必每段都有样本。
- --boundaries提供两个含时区的时间：train < 第一个边界；validation位于两个边界之间；test >= 第二个边界。与比率选项同时出现时，时间边界决定实际划分。
- per_project的不同项目可能存在跨项目日期重叠，不可宣称严格全局历史回放；使用global并额外核对标签可用时间，才能进一步评估该问题。
- 清洗输入改变时必须新建数据版本和运行目录。输出目录不可覆盖。

## 训练

```powershell
& ./.venv/Scripts/python.exe backen/ml/training/user_training.py data/local/input.csv --output backen/ml/user_runs/run001 --dataset-version user-clean-v1 --feature-schema-version team-kamei14-v1 --models logistic_regression decision_tree --transform log1p --split-mode per_project
```

八类算法复用现有注册表：logistic_regression、decision_tree、gaussian_nb、knn、rbf_svm、random_forest、gradient_boosting、deep_mlp。
用户入口默认只训练logistic_regression，使用注册表首组参数，不自动搜索；与历史最优配置不能混称。
统计预处理只拟合train；验证选择F1阈值；不读取测试预测或在测试集调参。
选择raw或log1p后，对LR/NB/KNN/SVM/MLP标准化，树模型不标准化。
版本字符串由调用者声明；特征公式、单位、清洗是否合法仍需外部核验。整表提前标准化的数据不能按原始尺度提交。

用--parameters指定JSON，格式：

```json
{"logistic_regression":{"C":0.1,"class_weight":"balanced"},"decision_tree":{"max_depth":4,"min_samples_leaf":5}}
```

种子固定42，MLP禁用随机抽取holdout早停，SVM保留概率输出供接口评分。
参数需符合各算法约束，未知参数明确失败，不承诺任意参数均能收敛。

## 后端调用

将training目录加入服务的模块路径后：

```python
from user_training import train_dataset, TrainingError

result = train_dataset(csv_path, output_dir,
    dataset_version="clean-v1", feature_schema_version="team-kamei14-v1",
    models=("logistic_regression",), mode="per_project")
```

生产接入时由后端生成安全的独立输出目录，安排后台任务，不接受客户端任意服务器路径。
用户上传文件先存到后端管理的目录，校验和预览确认后再调用训练。

产物：run.json、splits.csv、status.json、models/、metrics.json、manifest.json、feature_schema.json。
run.json记录来源哈希、数据版本、特征版本、划分配置、各项目类别统计和标签语义限制。
失败保留status=failed和错误信息，未发布manifest的目录不应注册成可用模型。
成功产物可直接通过handoff_v1.adapter.Predictor(output_dir)加载、批量预测；无需复制旧的八模型清单。
解释始终显式不可用，未实现SHAP；此接口不产生高/中/低业务优先级或更新模型库数据库。

运行验收测试：

```powershell
& ./.venv/Scripts/python.exe -m unittest discover -s backen/ml/training -p test_user_training.py
```
