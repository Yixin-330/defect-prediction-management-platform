# JIT 实验模型后端交付包 v1

用于 Web MVP 的进程内批量推理联调；不启动 HTTP 服务，不修改数据库或现有后端代码。
包含八个冻结模型，默认 `logistic_regression`，可通过 `model_id` 切换。
默认选择依据是首条 MVP 链路使用逻辑回归，不是测试集最优结论。
验证阶段预选候选为随机森林，但测试预算表现没有超过小提交优先，不能据此声称适合真实审查上线。

## 运行

在本目录使用 Python 3.11 创建独立环境，安装固定版本：

```powershell
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
& ./.venv/Scripts/python.exe adapter.py sample_request.json
& ./.venv/Scripts/python.exe -m unittest discover -s . -p test_adapter.py
```

后端进程内接入：

```python
from adapter import Predictor, ModelError

predictor = Predictor("/absolute/path/to/jit-model-handoff-v1")
# 服务启动后复用该实例，模型按需加载；输入和预处理均不执行fit。
result = predictor.predict_batch(request_body)
```

只加载本包可信模型文件。joblib模型不是安全的用户上传交换格式；文件SHA256用于检测意外变更，不提供身份签名。
运行依赖版本见requirements.txt和manifest.json，跨版本加载不能视为已验证。

## 请求与响应

示例见sample_request.json、sample_response.json。
根对象：`feature_schema_version`必填，`model_id`可选，`records`为1–1000项。
记录：`project_id`、完整小写40位`commit_sha`、包含全部14个字段的`features`。
联调样例来自归档验证样本，不含标签；project_id是占位值，不表示生产仓库映射。

- 输入必须是原始数值，禁止预先标准化或手动log转换；模型包中已包含适用的预处理。
- 空值、字符串数值、布尔值、无穷大、非整数计数、额外特征和缺字段均拒绝。
- 所有字段非负，ns/nd/nf为正整数，fix只能是0或1；语义与单位见feature_schema.json。
- 字段名顺序可变，内部按契约组装。新在线提取器须先核对公式与历史边界，名字一致不代表兼容。
- 批量允许部分成功：逐条返回status和index。失败项不带risk_score；单条错误不伪造评分。
- 整批版本不匹配、模型缺失或模型不可加载抛ModelError；后端按code转换HTTP响应。
- `predicted_label = int(risk_score >= threshold)`。阈值是分类阈值，不是高/中/低优先级阈值。
- explanation始终显式available=false；SHAP、其他解释、行级定位及修复建议未实现。
- 此接口不返回模型准确率承诺，不把分数解释为经过真实场景校准的缺陷概率。

## 错误与后端职责

| code | 建议HTTP状态 | 处理 |
| --- | --- | --- |
| INVALID_REQUEST / INVALID_RECORD / INVALID_FEATURES | 400或422 | 提示具体输入错误；单条错误在批结果中返回 |
| FEATURE_SCHEMA_MISMATCH | 409或422 | 选择兼容模型或重建数据 |
| MODEL_NOT_FOUND | 404 | 使用模型库白名单 |
| MODEL_UNAVAILABLE | 503 | 检查模型包完整性与运行环境 |
| DUPLICATE_RECORD | 409或422 | 批内提交身份去重 |
| INFERENCE_FAILED | 500或422 | 保存失败原因，允许重跑 |

后端负责run_id、数据集版本、预测记录ID、UTC预测时间、工作区配置、任务状态与数据库事务。
结果需关联本包package_version、model_id、model_version及数据集版本；adapter不替代运行管理层。
模型没有规定业务优先级分档。按risk_score降序展示时应固定同分顺序。
审查预算评估的两个口径见reports/report.md，不能把分类Recall与预算Recall混同。

## 交付文件

- manifest.json：八模型注册、固定阈值、模型校验值、运行版本和实验限制。
- feature_schema.json：输入白名单、字段类型、契约版本及已知单位/聚合限制。
- models/：八个模型及预处理产物。
- reports/：固定测试评估、冻结协议及限制；测试结果不能再用于挑配置。
- adapter.py：进程内预测接口与命令行入口。
- test_adapter.py：八模型预测、样例一致性和错误路径测试。
- package_checksums.json：压缩前文件校验清单；zip位于本目录之外。

## 联调验收

1. 用示例验证默认模型响应与sample_response.json一致，切换八个ID均可预测。
2. 对相同提交核对后端原始14维值与离线提取值，使用同一模型获得一致结果。
3. 无标签数据可预测；标签作为评估输入独立管理，不传入features。
4. 缺字段、错误版本、非法数值、重复身份明确失败，失败项没有评分。
5. 后端保存版本关联，重启后重新加载能恢复；不把此包能力当成完整工作台验收。

数据限制仍存在：675条小样本；sexp聚合、age单位和SZZ来源及标签时间待核验。
匹配输入契约只表示结构可运行，不能自动消除训练/在线特征差异。
