import asyncio
import subprocess
import unittest
import zlib
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from main import analyze_report
from services.ocr_extractor import (
    InvalidImageError,
    OcrEngineUnavailableError,
    OcrExecutionError,
    OcrResourceLimitError,
    OcrTimeoutError,
    MAX_IMAGE_PIXELS,
    extract_text_from_image,
    extract_text_from_pdf_page,
)
from services.pdf_extractor import extract_text_from_pdf
from test_uploads import make_pdf, make_text_pdf


def make_png() -> bytes:
    image = Image.new("RGB", (600, 100), "white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def make_jpeg() -> bytes:
    image = Image.new("RGB", (600, 100), "white")
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def make_upload(filename: str, content_type: str, contents: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(contents),
        headers=Headers({"content-type": content_type}),
    )


class OcrExtractionTests(unittest.TestCase):
    def test_image_ocr_streams_png_to_tesseract_without_saving_report_files(self):
        with patch("services.ocr_extractor._tesseract_executable", return_value="tesseract"), patch(
            "services.ocr_extractor.subprocess.run"
        ) as run_tesseract:
            run_tesseract.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b"Hemoglobin: 13.2\n", stderr=b""
            )

            text = extract_text_from_image(make_png())

        self.assertEqual(text, "Hemoglobin: 13.2")
        self.assertTrue(run_tesseract.call_args.kwargs["input"].startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(run_tesseract.call_args.args[0][1:3], ["stdin", "stdout"])
        self.assertIn("timeout", run_tesseract.call_args.kwargs)

    def test_jpeg_is_normalized_to_png_before_streaming_to_tesseract(self):
        with patch("services.ocr_extractor._tesseract_executable", return_value="tesseract"), patch(
            "services.ocr_extractor.subprocess.run"
        ) as run_tesseract:
            run_tesseract.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b"synthetic text", stderr=b""
            )

            text = extract_text_from_image(make_jpeg())

        self.assertEqual(text, "synthetic text")
        self.assertTrue(run_tesseract.call_args.kwargs["input"].startswith(b"\x89PNG\r\n\x1a\n"))

    def test_invalid_image_content_is_rejected_before_ocr(self):
        with patch("services.ocr_extractor.subprocess.run") as run_tesseract:
            with self.assertRaises(InvalidImageError):
                extract_text_from_image(b"not an image")

        run_tesseract.assert_not_called()

    def test_oversized_image_dimensions_are_rejected_before_decode_or_ocr(self):
        width = MAX_IMAGE_PIXELS + 1
        height = 1
        png_header = bytearray(make_png())
        png_header[16:20] = width.to_bytes(4, "big")
        png_header[20:24] = height.to_bytes(4, "big")
        png_header[29:33] = zlib.crc32(png_header[12:29]).to_bytes(4, "big")

        with patch("services.ocr_extractor.subprocess.run") as run_tesseract:
            with self.assertRaises(OcrResourceLimitError):
                extract_text_from_image(png_header)

        run_tesseract.assert_not_called()

    def test_missing_tesseract_is_reported_as_configuration_error(self):
        with patch("services.ocr_extractor.shutil.which", return_value=None):
            with self.assertRaises(OcrEngineUnavailableError):
                extract_text_from_image(make_png())

    def test_tesseract_timeout_is_reported_without_exposing_process_output(self):
        with patch("services.ocr_extractor._tesseract_executable", return_value="tesseract"), patch(
            "services.ocr_extractor.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="tesseract", timeout=30),
        ):
            with self.assertRaises(OcrTimeoutError) as raised:
                extract_text_from_image(make_png())

        self.assertTrue(raised.exception.__suppress_context__)
        self.assertIsNone(raised.exception.__cause__)

    def test_tesseract_nonzero_exit_is_reported_without_stderr(self):
        with patch("services.ocr_extractor._tesseract_executable", return_value="tesseract"), patch(
            "services.ocr_extractor.subprocess.run"
        ) as run_tesseract:
            run_tesseract.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout=b"", stderr=b"private engine diagnostic"
            )
            with self.assertRaises(OcrExecutionError) as raised:
                extract_text_from_image(make_png())

        self.assertNotIn("private engine diagnostic", str(raised.exception))

    def test_text_pdf_pages_do_not_invoke_ocr(self):
        with patch("services.pdf_extractor.extract_text_from_pdf_page") as ocr_page:
            text = extract_text_from_pdf(make_text_pdf("Hemoglobin: 13.2"))

        self.assertIn("Hemoglobin: 13.2", text)
        ocr_page.assert_not_called()

    def test_mixed_pdf_ocr_falls_back_only_on_pages_without_text(self):
        from pypdf import PdfReader, PdfWriter

        text_pdf = PdfReader(BytesIO(make_text_pdf("Hemoglobin: 13.2")))
        writer = PdfWriter()
        writer.add_page(text_pdf.pages[0])
        writer.add_blank_page(width=72, height=72)
        output = BytesIO()
        writer.write(output)

        with patch(
            "services.pdf_extractor.extract_text_from_pdf_page",
            return_value="Glucose: 95",
        ) as ocr_page:
            text = extract_text_from_pdf(output.getvalue())

        self.assertLess(text.index("Hemoglobin"), text.index("Glucose"))
        self.assertEqual(ocr_page.call_args.args[1], 1)

    def test_empty_pdf_page_uses_ocr_fallback(self):
        with patch(
            "services.pdf_extractor.extract_text_from_pdf_page",
            return_value="Hemoglobin: 13.2",
        ) as ocr_page:
            text = extract_text_from_pdf(make_pdf())

        self.assertEqual(text, "Hemoglobin: 13.2")
        ocr_page.assert_called_once()

    def test_pdf_page_is_rendered_to_png_bytes_for_ocr(self):
        with patch("services.ocr_extractor._tesseract_executable", return_value="tesseract"), patch(
            "services.ocr_extractor.subprocess.run"
        ) as run_tesseract:
            run_tesseract.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b"synthetic scanned text", stderr=b""
            )

            text = extract_text_from_pdf_page(make_pdf(), 0)

        self.assertEqual(text, "synthetic scanned text")
        self.assertTrue(run_tesseract.call_args.kwargs["input"].startswith(b"\x89PNG\r\n\x1a\n"))

    def test_pdf_with_more_than_ocr_page_limit_is_rejected(self):
        from pypdf import PdfWriter

        writer = PdfWriter()
        for _ in range(26):
            writer.add_blank_page(width=72, height=72)
        output = BytesIO()
        writer.write(output)

        with patch("services.pdf_extractor.extract_text_from_pdf_page", return_value=""):
            with self.assertRaises(OcrResourceLimitError):
                extract_text_from_pdf(output.getvalue())

    def test_pdf_document_ocr_deadline_is_enforced(self):
        with patch("services.pdf_extractor.time.monotonic", side_effect=(0, 121)):
            with patch("services.pdf_extractor.extract_text_from_pdf_page") as ocr_page:
                with self.assertRaises(OcrTimeoutError):
                    extract_text_from_pdf(make_pdf())

        ocr_page.assert_not_called()

    def test_image_analysis_returns_existing_result_fields(self):
        with patch("main.extract_text_from_image", return_value="Hemoglobin: 13.2 g/dL"):
            result = asyncio.run(analyze_report(make_upload("report.png", "image/png", make_png())))

        self.assertEqual(
            set(result),
            {
                "success",
                "filename",
                "message",
                "text",
                "medical_data",
                "classification",
                "document_type",
            },
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["medical_data"]["hemoglobin"], 13.2)

    def test_image_analysis_keeps_unitless_value_unavailable_for_classification(self):
        with patch("main.extract_text_from_image", return_value="Hemoglobin: 13.2"):
            result = asyncio.run(analyze_report(make_upload("report.png", "image/png", make_png())))

        self.assertIsNone(result["medical_data"]["hemoglobin"])
        self.assertEqual(result["classification"]["status"], "REVIEW")
        self.assertIn("unit", result["classification"]["flags"][-1].lower())

    def test_image_analysis_maps_missing_engine_to_service_unavailable(self):
        with patch("main.extract_text_from_image", side_effect=OcrEngineUnavailableError()):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(analyze_report(make_upload("report.png", "image/png", make_png())))

        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
