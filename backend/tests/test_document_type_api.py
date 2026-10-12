import asyncio
import unittest
from unittest.mock import patch

import main
from ml_experiments.indicphi_document_type import DOCUMENT_TYPES
from test_uploads import make_text_pdf, make_upload


class PredictingModel:
    classes_ = DOCUMENT_TYPES

    def __init__(self, category="lab_report", error=None):
        self.category = category
        self.error = error
        self.calls = []

    def predict(self, texts):
        self.calls.append(texts)
        if self.error:
            raise self.error
        return [self.category]


class DocumentTypeApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.previous_model = main.document_type_pipeline
        self.previous_load_error = main.document_type_model_load_error
        main.document_type_pipeline = None
        main.document_type_model_load_error = False

    def tearDown(self):
        main.document_type_pipeline = self.previous_model
        main.document_type_model_load_error = self.previous_load_error

    async def test_startup_loads_the_pipeline_once_and_checks_expected_classes(self):
        model = PredictingModel()
        with patch("main.joblib.load", return_value=model) as load:
            async with main.lifespan(main.app):
                self.assertIs(main.document_type_pipeline, model)
                load.assert_called_once_with(main.DOCUMENT_TYPE_MODEL_PATH)

    async def test_startup_rejects_a_pipeline_with_unexpected_classes(self):
        model = PredictingModel()
        model.classes_ = ("invented_category",)
        with patch("main.joblib.load", return_value=model):
            async with main.lifespan(main.app):
                self.assertIsNone(main.document_type_pipeline)
                self.assertTrue(main.document_type_model_load_error)

    async def test_model_load_failure_is_controlled_and_does_not_block_app_lifespan(self):
        with patch("main.joblib.load", side_effect=OSError("private model path detail")):
            async with main.lifespan(main.app):
                result = main.classify_document_type("Synthetic English text. " * 10)

        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["category"])
        self.assertNotIn("private model path detail", result["uncertainty"])

    async def test_successful_analysis_adds_category_and_preserves_existing_response(self):
        model = PredictingModel("lab_report")
        main.document_type_pipeline = model
        extracted_text = "Hemoglobin: 13.2 g/dL\n" + (
            "The report is for review, and this synthetic example contains values. " * 3
        )
        with patch("main.extract_text_from_pdf", return_value=extracted_text):
            result = await main.analyze_report(
                make_upload("synthetic.pdf", "application/pdf", make_text_pdf(extracted_text))
            )

        self.assertEqual(
            set(result),
            {"success", "filename", "message", "text", "medical_data", "classification", "document_type"},
        )
        self.assertEqual(result["document_type"]["status"], "predicted")
        self.assertEqual(result["document_type"]["category"], "lab_report")
        self.assertIsNone(result["document_type"]["confidence"])
        self.assertIn("no calibrated confidence", result["document_type"]["uncertainty"].lower())
        self.assertEqual(result["classification"]["status"], "REVIEW")
        self.assertEqual(model.calls, [[extracted_text]])

    async def test_empty_extraction_returns_no_document_type_prediction(self):
        model = PredictingModel()
        main.document_type_pipeline = model
        with patch("main.extract_text_from_pdf", return_value=""):
            result = await main.analyze_report(
                make_upload("empty.pdf", "application/pdf", make_text_pdf(""))
            )

        self.assertFalse(result["success"])
        self.assertNotIn("document_type", result)
        self.assertEqual(model.calls, [])

    async def test_insufficient_or_unsupported_language_text_is_unavailable(self):
        model = PredictingModel()
        main.document_type_pipeline = model

        short = main.classify_document_type("English words " * 5)
        other_script = main.classify_document_type(
            "\u0939\u093f\u0928\u094d\u0926\u0940 "
            "\u091a\u093f\u0915\u093f\u0924\u094d\u0938\u093e "
            "\u0930\u093f\u092a\u094b\u0930\u094d\u091f " * 10
        )
        other_latin_language = main.classify_document_type(
            "Bonjour, ce document m\u00e9dical contient des informations cliniques. " * 6
        )

        self.assertEqual(short["status"], "unavailable")
        self.assertIsNone(short["category"])
        self.assertEqual(other_script["status"], "unavailable")
        self.assertIsNone(other_script["category"])
        self.assertIn("this script", other_script["uncertainty"])
        self.assertEqual(other_latin_language["status"], "unavailable")
        self.assertIsNone(other_latin_language["category"])
        self.assertIn("English-language signal", other_latin_language["uncertainty"])
        self.assertEqual(model.calls, [])

    async def test_inference_failure_keeps_analysis_and_returns_no_category(self):
        model = PredictingModel(error=RuntimeError("private inference detail"))
        main.document_type_pipeline = model
        extracted_text = "The report is for review, and this synthetic example contains values. " * 3
        with patch("main.extract_text_from_pdf", return_value=extracted_text):
            result = await main.analyze_report(
                make_upload("synthetic.pdf", "application/pdf", make_text_pdf(extracted_text))
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["document_type"]["status"], "unavailable")
        self.assertIsNone(result["document_type"]["category"])
        self.assertNotIn("private inference detail", result["document_type"]["uncertainty"])
        self.assertEqual(result["classification"]["status"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
