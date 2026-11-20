# 冻结实验结果 jit14-v5

- validation-comparison.md/json：八类模型的验证集结果。
- *-validation.json：各模型参数、全部试验记录、分类阈值、特征顺序、输入哈希及依赖版本。
- test-report.md、test-comparison.json、test-frozen_protocol.json：冻结方案测试结果及局限。
- mlp-stability.json：固定网络配置在三个种子上的波动；未挑选测试最优种子。

报告中没有完整原始数据集。划分身份和可复现训练见backen/ml/training。
验证与测试数据来自不同时期；正例比例与特征分布变化，不应把验证成绩当作真实部署保证。
部分来源和标签观察证据待核验。此处历史产物保留原样，后续新数据发布应使用新版本目录。
