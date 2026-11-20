# 八类模型固定方案测试报告

预选候选：随机森林（仅由验证集选出，不按本表重新选模）。
测试集 102 条，正例 27 条；无重训练、无调阈值。

| 模型 | AP | ROC-AUC | Precision | Recall | F1 | 预算停止 | 预算跳过 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic_regression | 0.4507 | 0.7674 | 0.4750 | 0.7037 | 0.5672 | 0.0000 | 0.0741 |
| decision_tree | 0.4675 | 0.7820 | 0.5405 | 0.7407 | 0.6250 | 0.2963 | 0.2963 |
| gaussian_nb | 0.4474 | 0.7669 | 0.4565 | 0.7778 | 0.5753 | 0.2593 | 0.3333 |
| knn | 0.4346 | 0.7096 | 0.4250 | 0.6296 | 0.5075 | 0.2593 | 0.2593 |
| rbf_svm | 0.5108 | 0.7778 | 0.5000 | 0.5185 | 0.5091 | 0.0000 | 0.1852 |
| random_forest | 0.4056 | 0.7427 | 0.5278 | 0.7037 | 0.6032 | 0.1111 | 0.1111 |
| gradient_boosting | 0.4450 | 0.7751 | 0.5143 | 0.6667 | 0.5806 | 0.1481 | 0.1481 |
| deep_mlp | 0.4673 | 0.6768 | 0.4545 | 0.5556 | 0.5000 | 0.0000 | 0.2222 |

简单策略对照（相同预算和测试样本）：
- smallest_first：审查 81 条、找到 13 个正例，召回率 0.4815。
- chronological：审查 33 条、找到 13 个正例，召回率 0.4815。

限制：
- The test set has already been inspected for the early LR baseline; this is not a pristine blind confirmation set.
- 675 samples, 27 test positives; small-sample uncertainty.
- Feature extraction/SZZ provenance and label-time availability remain unverified.
- Search budgets differ by model; extensive repeated validation selection.
- MLP seed 42 configuration was selected on validation; other seeds were sensitivity checks.

## 本轮结论

八类模型的首轮训练、验证选择、固定方案测试已完成。验证预选的随机森林未在测试审查预算指标上超过小提交优先基线，不建议直接作为真实审查的默认排序。不得据本表重选模型后将同一测试成绩称为独立验证。

后续优先核验标签证据、特征提取及时间分布，并在独立新数据或预先约定的时间回放实验中确认排序策略；可继续以实验模型做系统联调。
