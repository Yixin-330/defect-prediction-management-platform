# Model comparison (validation only)

472 training samples; 101 validation samples; 44 validation positives. Test not evaluated.

| Model | AP | ROC-AUC | Precision | Recall | F1 | Budget stop | Budget skip |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic_regression | 0.7963 | 0.8744 | 0.8333 | 0.7955 | 0.8140 | 0.0000 | 0.2955 |
| decision_tree | 0.8574 | 0.8929 | 0.7755 | 0.8636 | 0.8172 | 0.3409 | 0.5000 |
| gaussian_nb | 0.7022 | 0.8170 | 0.7143 | 0.9091 | 0.8000 | 0.0000 | 0.4091 |
| knn | 0.8704 | 0.9013 | 0.8222 | 0.8409 | 0.8315 | 0.0227 | 0.3182 |
| rbf_svm | 0.8806 | 0.8943 | 0.8684 | 0.7500 | 0.8049 | 0.4545 | 0.4545 |
| random_forest | 0.8836 | 0.8987 | 0.8571 | 0.8182 | 0.8372 | 0.5000 | 0.5455 |
| gradient_boosting | 0.8536 | 0.8772 | 0.8000 | 0.8182 | 0.8090 | 0.3864 | 0.4773 |
| deep_mlp | 0.8638 | 0.8907 | 0.8780 | 0.8182 | 0.8471 | 0.1136 | 0.4318 |

Selection: validation AP; threshold: validation F1. Search budgets differ.
Validation was used for selection, so these are not independent estimates of generalization.
RF and GBDT use raw features, no scaling or resampling. Scores are unverified risk scores.
SVM internal probability estimation uses training folds; this is not strict chronological calibration.
Runtime versions and dataset/split hashes are recorded in each report.
