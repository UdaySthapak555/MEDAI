import json
import tempfile
import unittest
from pathlib import Path

from ml_experiments.indicphi_document_type import (
    DOCUMENT_TYPES,
    build_pipeline,
    evaluate_predictions,
    load_english_split,
    normalized_text_hash,
)


class IndicPhiExperimentTests(unittest.TestCase):
    def write_jsonl(self, rows):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "split.jsonl"
        with path.open("w", encoding="utf-8") as output:
            for row in rows:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path

    def row(self, text, label, language="en", errors=None):
        return {
            "document_id": "synthetic-document-id",
            "text": text,
            "tokenized_text": [],
            "ner": [],
            "spans": [],
            "domain_id": "synthetic-domain",
            "doc_type_id": label,
            "document_language_code": language,
            "token_align_errors": errors or [],
            "uuid": "synthetic-metadata-must-not-become-a-feature",
            "split": "train",
            "stage": "s10_split",
        }

    def test_loader_filters_language_and_returns_only_text_and_labels(self):
        path = self.write_jsonl(
            [
                self.row("English synthetic report", DOCUMENT_TYPES[0], errors=["offset-only"]),
                self.row("Assamese synthetic report", DOCUMENT_TYPES[1], "as"),
                self.row("Second English report", DOCUMENT_TYPES[1]),
            ]
        )

        split = load_english_split(path)

        self.assertEqual(split.texts, ["English synthetic report", "Second English report"])
        self.assertEqual(split.labels, [DOCUMENT_TYPES[0], DOCUMENT_TYPES[1]])
        self.assertEqual(split.language_counts, {"en": 2, "as": 1})
        self.assertEqual(split.english_token_alignment_error_records, 1)
        self.assertFalse(hasattr(split, "rows"))

    def test_loader_rejects_labels_outside_source_document_types(self):
        path = self.write_jsonl([self.row("Synthetic report", "invented_category")])

        with self.assertRaisesRegex(ValueError, "Unsupported doc_type_id"):
            load_english_split(path)

    def test_loader_rejects_unexpected_dataset_schema(self):
        row = self.row("Synthetic report", DOCUMENT_TYPES[0])
        row.pop("uuid")
        path = self.write_jsonl([row])

        with self.assertRaisesRegex(ValueError, "Unexpected dataset schema at line 1"):
            load_english_split(path)

    def test_loader_rejects_records_from_the_wrong_provided_split(self):
        path = self.write_jsonl([self.row("Synthetic report", DOCUMENT_TYPES[0], language="en")])

        with self.assertRaisesRegex(ValueError, "Record does not belong to the expected split"):
            load_english_split(path, expected_split="eval")

    def test_loader_rejects_malformed_jsonl_without_exposing_record_contents(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "split.jsonl"
        path.write_text('{"text":"synthetic marker"\n', encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Invalid JSONL at line 1") as caught:
            load_english_split(path)

        self.assertNotIn("synthetic marker", str(caught.exception))

    def test_normalized_text_hash_is_stable_for_case_and_whitespace(self):
        self.assertEqual(
            normalized_text_hash("  Synthetic   NOTE\n"),
            normalized_text_hash("synthetic note"),
        )

    def test_pipeline_preprocessing_and_predictions_are_deterministic(self):
        texts = [
            "synthetic discharge summary follow up",
            "synthetic discharge summary patient review",
            "synthetic radiology report chest imaging",
            "synthetic radiology report image review",
        ]
        labels = [DOCUMENT_TYPES[0], DOCUMENT_TYPES[0], DOCUMENT_TYPES[1], DOCUMENT_TYPES[1]]
        first = build_pipeline("logistic_regression").fit(texts, labels)
        second = build_pipeline("logistic_regression").fit(texts, labels)

        self.assertEqual(
            first.named_steps["features"].get_feature_names_out().tolist(),
            second.named_steps["features"].get_feature_names_out().tolist(),
        )
        self.assertEqual(first.predict(texts).tolist(), second.predict(texts).tolist())

    def test_evaluation_contains_all_class_metrics_and_full_confusion_matrix(self):
        labels = list(DOCUMENT_TYPES)
        true = [labels[0], labels[0], labels[1], labels[2]]
        predicted = [labels[0], labels[1], labels[1], labels[3]]

        result = evaluate_predictions(true, predicted, labels)

        self.assertEqual(set(result), {"accuracy", "macro_f1", "weighted_f1", "per_class", "confusion_matrix"})
        self.assertEqual(len(result["per_class"]), 14)
        self.assertEqual(result["per_class"][labels[0]]["support"], 2)
        self.assertEqual(len(result["confusion_matrix"]), 14)
        self.assertTrue(all(len(row) == 14 for row in result["confusion_matrix"]))


if __name__ == "__main__":
    unittest.main()
