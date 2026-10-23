# openstack 真实数据清洗与逻辑回归实验

原始 26855 条；保留 12374 条；筛除 14481 条。原文件 SHA256 已检查未变。

| 划分 | 样本 | 正例 | ROC-AUC | AP | F1@0.5 | Recall@20% effort |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 8661 | 957 | 0.7161 | 0.2333 | 0.0336 | 0.0313 |
| validation | 1856 | 373 | 0.7153 | 0.3805 | 0.0412 | 0.0295 |
| test | 1857 | 286 | 0.7160 | 0.3301 | 0.0471 | 0.0559 |

阈值固定 0.5；未调参，未重采样；工作量为 la+ld，按风险降序检查完整提交。
缺失值按训练集的中位数填补并添加训练时发现的缺失标记，标准化也仅拟合训练集。
采用独立11维源数据契约，age保留源尺度，不能宣称与线上14维特征一致。
这是归档数据时间留出评估；缺少标签发现日期，不能证明历史标签在训练时已可获得。

限制：
- Offline archival benchmark only; not a production-ready 14-feature model.
- Blank bugcount becomes negative by source convention, not proof of no defect.
- Fix discovery dates and per-sample label availability are absent; historical label-time leakage cannot be ruled out.
- age retains source numeric units; conversion to seconds/days has not been verified.
- ent retains source bounded scale; no synthetic entropy or age conversion is applied.
- CSV cannot independently establish extraction as-of timing or reproduce SZZ labels.
- Missing history is unknown, not asserted to be zero history; train-only median imputation differs from source zero-fill.

来源：
- https://github.com/software-rebels/JITMovingTarget/blob/master/scripts/load_data.r
- https://github.com/software-rebels/JITMovingTarget/blob/master/scripts/experimental_settings.r
- https://posl.ait.kyushu-u.ac.jp/~kamei/publications/McIntosh_TSE2017.pdf
