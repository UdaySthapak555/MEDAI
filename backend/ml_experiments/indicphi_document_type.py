"""Train and evaluate a text-only IndicPHI document-type prototype.

Run from ``backend`` with ``venv/Scripts/python.exe -m
ml_experiments.indicphi_document_type``.

The experiment intentionally does not integrate with the FastAPI application.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression


RANDOM_SEED = 42
ENGLISH_LANGUAGE_CODE = "en"
DOCUMENT_TYPES = (
    "asha_worker_note",
    "automated_sms",
    "discharge_summary",
    "er_triage_notes",
    "hospital_billing",
    "insurance_claim",
    "lab_report",
    "opd_slip",
    "phc_register",
    "prescription",
    "radiology_report",
    "referral_letter",
    "surgical_note",
    "telemedicine_transcript",
)
DOCUMENT_TYPE_SET = frozenset(DOCUMENT_TYPES)
EXPECTED_SCHEMA_KEYS = frozenset(
    {
        "document_id",
        "doc_type_id",
        "document_language_code",
        "domain_id",
        "ner",
        "spans",
        "split",
        "stage",
        "text",
        "token_align_errors",
        "tokenized_text",
        "uuid",
    }
)
DATASET_URL = "https://huggingface.co/datasets/Sidharth1743/indicphi"
LICENSE_NOTE = (
    "The published dataset card states MIT, and separately notes that persona seed data "
    "comes from NVIDIA Nemotron-Personas-India and its license must also be respected. "
    "Verify applicable terms before redistribution."
)


@dataclass
class SplitData:
    """A split's selected text and labels plus non-sensitive aggregate diagnostics."""

    texts: list[str]
    labels: list[str]
    total_records: int
    language_counts: dict[str, int]
    class_counts: dict[str, int]
    token_alignment_error_records: int
    english_token_alignment_error_records: int
    normalized_duplicate_text_count: int


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield JSON objects one line at a time without including row content in errors."""

    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}.") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Expected a JSON object at line {line_number}.")
            yield record


def normalized_text_hash(text: str) -> str:
    """Hash normalized text for duplicate checks without retaining or displaying it."""

    normalized = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_english_split(path: Path, expected_split: str | None = None) -> SplitData:
    """Read a dataset split incrementally and select only English text and doc_type_id."""

    texts: list[str] = []
    labels: list[str] = []
    language_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    seen_hashes: set[str] = set()
    duplicate_count = 0
    total_records = 0
    alignment_error_records = 0
    english_alignment_error_records = 0

    for line_number, record in enumerate(iter_jsonl(path), start=1):
        total_records += 1
        if frozenset(record) != EXPECTED_SCHEMA_KEYS:
            raise ValueError(f"Unexpected dataset schema at line {line_number}.")
        if record.get("split") not in {"train", "eval"}:
            raise ValueError(f"Invalid split value at line {line_number}.")
        if expected_split is not None and record["split"] != expected_split:
            raise ValueError(f"Record does not belong to the expected split at line {line_number}.")
        text = record.get("text")
        label = record.get("doc_type_id")
        language = record.get("document_language_code")
        alignment_errors = record.get("token_align_errors")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Missing or invalid text at line {line_number}.")
        if not isinstance(label, str) or label not in DOCUMENT_TYPE_SET:
            raise ValueError(f"Unsupported doc_type_id at line {line_number}.")
        if not isinstance(language, str) or not language:
            raise ValueError(f"Missing or invalid document_language_code at line {line_number}.")
        if not isinstance(alignment_errors, list):
            raise ValueError(f"Invalid token_align_errors field at line {line_number}.")

        language_counts[language] += 1
        if alignment_errors:
            alignment_error_records += 1
        if language != ENGLISH_LANGUAGE_CODE:
            continue

        if alignment_errors:
            english_alignment_error_records += 1
        digest = normalized_text_hash(text)
        if digest in seen_hashes:
            duplicate_count += 1
        seen_hashes.add(digest)
        texts.append(text)
        labels.append(label)
        class_counts[label] += 1

    if not texts:
        raise ValueError(f"No {ENGLISH_LANGUAGE_CODE!r} records found in the dataset split.")

    return SplitData(
        texts=texts,
        labels=labels,
        total_records=total_records,
        language_counts=dict(sorted(language_counts.items())),
        class_counts={label: class_counts[label] for label in DOCUMENT_TYPES if class_counts[label]},
        token_alignment_error_records=alignment_error_records,
        english_token_alignment_error_records=english_alignment_error_records,
        normalized_duplicate_text_count=duplicate_count,
    )


def _feature_union() -> FeatureUnion:
    """Create deterministic word and character n-gram TF-IDF features."""

    return FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                    lowercase=True,
                    strip_accents="unicode",
                    sublinear_tf=True,
                    min_df=1,
                    max_features=50_000,
                ),
            ),
            (
                "character",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    lowercase=True,
                    strip_accents="unicode",
                    sublinear_tf=True,
                    min_df=2,
                    max_features=50_000,
                ),
            ),
        ],
        n_jobs=1,
    )


def build_pipeline(model_name: str) -> Pipeline:
    """Return a text-vectorization and classifier pipeline for a named model."""

    if model_name == "logistic_regression":
        classifier = LogisticRegression(
            C=1.0,
            max_iter=2_000,
            random_state=RANDOM_SEED,
            solver="lbfgs",
        )
    elif model_name == "linear_svc":
        classifier = LinearSVC(C=1.0, max_iter=10_000, random_state=RANDOM_SEED)
    else:
        raise ValueError(f"Unknown model name: {model_name}")

    return Pipeline([("features", _feature_union()), ("classifier", classifier)])


def evaluate_predictions(
    true_labels: list[str], predicted_labels: list[str], labels: list[str] | tuple[str, ...]
) -> dict[str, Any]:
    """Calculate aggregate, per-class and confusion-matrix evaluation metrics."""

    if len(true_labels) != len(predicted_labels):
        raise ValueError("True and predicted label counts must match.")
    if not true_labels:
        raise ValueError("Evaluation requires at least one labeled example.")

    precision, recall, f1, support = precision_recall_fscore_support(
        true_labels,
        predicted_labels,
        labels=list(labels),
        zero_division=0,
    )
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }
    _, _, macro_f1, _ = precision_recall_fscore_support(
        true_labels,
        predicted_labels,
        labels=list(labels),
        average="macro",
        zero_division=0,
    )
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        true_labels,
        predicted_labels,
        labels=list(labels),
        average="weighted",
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(true_labels, predicted_labels)),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(
            true_labels, predicted_labels, labels=list(labels)
        ).tolist(),
    }


def _summary(split: SplitData) -> dict[str, Any]:
    """Produce a report-safe aggregate summary, excluding all report text."""

    return {
        "total_records": split.total_records,
        "language_counts": split.language_counts,
        "english_records": len(split.texts),
        "english_class_counts": split.class_counts,
        "english_normalized_duplicate_text_count": split.normalized_duplicate_text_count,
        "token_alignment_error_records_all_languages": split.token_alignment_error_records,
        "token_alignment_error_records_english": split.english_token_alignment_error_records,
    }


def _validate_complete_label_support(train: SplitData, evaluation: SplitData) -> None:
    missing_train = [label for label in DOCUMENT_TYPES if train.class_counts.get(label, 0) == 0]
    missing_eval = [label for label in DOCUMENT_TYPES if evaluation.class_counts.get(label, 0) == 0]
    if missing_train or missing_eval:
        raise ValueError(
            "The English split does not support all source labels; "
            f"missing from train={missing_train}, missing from eval={missing_eval}. "
            "No labels were dropped or merged."
        )


def run_experiment(
    train_path: Path,
    evaluation_path: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    """Fit on the supplied English train split and evaluate on the supplied eval split."""

    train = load_english_split(train_path, expected_split="train")
    evaluation = load_english_split(evaluation_path, expected_split="eval")
    _validate_complete_label_support(train, evaluation)

    train_hashes = {normalized_text_hash(text) for text in train.texts}
    evaluation_hashes = {normalized_text_hash(text) for text in evaluation.texts}
    cross_split_duplicates = len(train_hashes & evaluation_hashes)
    summary = {
        "train": _summary(train),
        "evaluation": _summary(evaluation),
        "cross_split_normalized_duplicate_text_count": cross_split_duplicates,
    }
    # Print counts before any model is fitted. This intentionally contains no row text.
    print(json.dumps({"pretraining_data_summary": summary}, indent=2, sort_keys=True))
    if cross_split_duplicates:
        raise ValueError(
            "Normalized English text overlaps across supplied train/eval splits; "
            "training stopped to avoid leakage."
        )

    majority_label = min(
        DOCUMENT_TYPES,
        key=lambda label: (-train.class_counts.get(label, 0), DOCUMENT_TYPES.index(label)),
    )
    results: dict[str, Any] = {
        "majority_class_baseline": {
            "predicted_class": majority_label,
            "metrics": evaluate_predictions(
                evaluation.labels,
                [majority_label] * len(evaluation.labels),
                DOCUMENT_TYPES,
            ),
        }
    }

    artifact_dir.mkdir(parents=True, exist_ok=True)
    for model_name in ("logistic_regression", "linear_svc"):
        pipeline = build_pipeline(model_name)
        pipeline.fit(train.texts, train.labels)
        predictions = pipeline.predict(evaluation.texts).tolist()
        results[model_name] = {
            "metrics": evaluate_predictions(evaluation.labels, predictions, DOCUMENT_TYPES),
            "model_file": f"{model_name}.joblib",
        }
        joblib.dump(pipeline, artifact_dir / f"{model_name}.joblib")

    report = {
        "experiment": "IndicPHI English synthetic document-type classification",
        "dataset_source": DATASET_URL,
        "license_note": LICENSE_NOTE,
        "target": "doc_type_id",
        "feature_source": "text only",
        "excluded_metadata": [
            "document_id",
            "uuid",
            "doc_type_id (target only)",
            "domain_id",
            "document_language_code",
            "split",
            "stage",
            "ner",
            "spans",
            "token_align_errors",
            "all other metadata",
        ],
        "provided_split_preserved": True,
        "preprocessing_fit_only_on_train": True,
        "random_seed": RANDOM_SEED,
        "labels": list(DOCUMENT_TYPES),
        "data_summary": summary,
        "results": results,
        "vectorization": {
            "word": {
                "analyzer": "word",
                "ngram_range": [1, 2],
                "min_df": 1,
                "max_features": 50_000,
                "sublinear_tf": True,
                "lowercase": True,
                "strip_accents": "unicode",
            },
            "character": {
                "analyzer": "char_wb",
                "ngram_range": [3, 5],
                "min_df": 2,
                "max_features": 50_000,
                "sublinear_tf": True,
                "lowercase": True,
                "strip_accents": "unicode",
            },
        },
        "model_parameters": {
            "logistic_regression": {
                "C": 1.0,
                "solver": "lbfgs",
                "max_iter": 2_000,
                "random_state": RANDOM_SEED,
            },
            "linear_svc": {"C": 1.0, "max_iter": 10_000, "random_state": RANDOM_SEED},
        },
        "scikit_learn_version": sklearn.__version__,
        "python_version": sys.version.split()[0],
        "limitations": [
            "Synthetic text only; results do not establish performance on real reports or OCR output.",
            "English evaluation support is small for some labels; per-class metrics are exploratory.",
            "The text is synthetic and may encode source-template or identifier patterns useful to the target.",
            "The model is not clinically validated and must not be used for diagnosis or treatment.",
            "The dataset card notes an upstream persona-data license condition in addition to its MIT label.",
        ],
    }
    report_path = artifact_dir / "evaluation.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Aggregate evaluation written to {report_path}")
    return report


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=project_root / "datasets/raw/train.jsonl")
    parser.add_argument("--evaluation", type=Path, default=project_root / "datasets/raw/eval.jsonl")
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=project_root / "backend/artifacts/indicphi_document_type",
    )
    args = parser.parse_args()
    run_experiment(args.train, args.evaluation, args.artifacts)


if __name__ == "__main__":
    main()
