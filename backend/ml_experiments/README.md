# IndicPHI document-type experiment

This module is a local synthetic-data research experiment. Training remains separate from the FastAPI request flow. The API loads the saved LogisticRegression pipeline from the local artifact directory; its existing rule-based lab screening classifier remains unchanged.

Run it from `backend/` with:

```powershell
.\venv\Scripts\python.exe -m ml_experiments.indicphi_document_type
```

The script streams the supplied JSONL files, selects records whose `document_language_code` is `en`, uses only `text` as the feature source, and predicts the original 14-category `doc_type_id`. It preserves the supplied train/eval files, fits both TF-IDF vectorizers only through pipelines trained on train text, and reports a majority-class baseline, LogisticRegression, and LinearSVC. It prints class and language counts before fitting. Reports contain aggregate metrics only; raw text is not written to logs or artifacts.

The default outputs are written to `backend/artifacts/indicphi_document_type/`: two fitted pipelines and `evaluation.json`. The API uses only `logistic_regression.joblib`; this repository intentionally includes that inference artifact. The raw JSONL files, `evaluation.json`, and the alternative `linear_svc.joblib` remain local and excluded. The model artifact is approximately 15 MB and can retain synthetic phrase or identifier-like vocabulary; it is not trained on real patient data and must not be used as a clinical system.

The [published IndicPHI dataset card](https://huggingface.co/datasets/Sidharth1743/indicphi) lists MIT and says its personas come from [NVIDIA Nemotron-Personas-India](https://huggingface.co/datasets/nvidia/Nemotron-Personas-India), which is listed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This repository provides source attribution in `THIRD_PARTY_NOTICES.md`; it does not redistribute the raw dataset.

This experiment uses synthetic data only. Its metrics do not establish performance on real medical reports, OCR text, or clinical decisions. It is not clinically validated and must not diagnose disease or recommend treatment.
