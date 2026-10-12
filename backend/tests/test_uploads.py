import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from pypdf import PdfWriter
from starlette.datastructures import Headers, UploadFile

from main import analyze_report, upload_report


def make_pdf() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(output)
    return output.getvalue()


def make_text_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(body + b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def make_upload(filename: str, content_type: str, contents: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(contents),
        headers=Headers({"content-type": content_type}),
    )


class UploadHandlingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_cwd = Path.cwd()
        os.chdir(self.temp_dir.name)
        Path("uploads").mkdir()

    def tearDown(self):
        os.chdir(self.previous_cwd)
        self.temp_dir.cleanup()

    async def test_valid_pdf_upload_returns_existing_metadata_without_saving_copy(self):
        contents = make_pdf()

        result = await upload_report(make_upload("report.pdf", "application/pdf", contents))

        self.assertEqual(result["success"], True)
        self.assertEqual(result["filename"], "report.pdf")
        self.assertEqual(result["content_type"], "application/pdf")
        self.assertEqual(result["size"], len(contents))
        self.assertFalse(Path("uploads/report.pdf").exists())

    async def test_unsupported_format_returns_415(self):
        with self.assertRaises(HTTPException) as raised:
            await upload_report(make_upload("notes.txt", "text/plain", b"text"))

        self.assertEqual(raised.exception.status_code, 415)

    async def test_upload_larger_than_limit_returns_413(self):
        contents = b"%PDF-1.4\n" + b"x" * (10 * 1024 * 1024)
        uploaded_file = make_upload("large.pdf", "application/pdf", contents)

        with self.assertRaises(HTTPException) as raised:
            await upload_report(uploaded_file)

        self.assertEqual(raised.exception.status_code, 413)
        self.assertEqual(uploaded_file.file.tell(), 10 * 1024 * 1024 + 1)

    async def test_unsafe_filename_returns_400_without_writing_outside_upload_directory(self):
        for filename in ("../outside.pdf", r"..\outside.pdf", "/outside.pdf"):
            with self.subTest(filename=filename):
                with self.assertRaises(HTTPException) as raised:
                    await upload_report(make_upload(filename, "application/pdf", make_pdf()))

                self.assertEqual(raised.exception.status_code, 400)
        self.assertFalse(Path("outside.pdf").exists())

    async def test_content_mismatch_returns_415(self):
        with self.assertRaises(HTTPException) as raised:
            await upload_report(make_upload("report.pdf", "application/pdf", b"not a PDF"))

        self.assertEqual(raised.exception.status_code, 415)

    async def test_malformed_pdf_analysis_returns_400(self):
        with self.assertRaises(HTTPException) as raised:
            await analyze_report(make_upload("broken.pdf", "application/pdf", b"%PDF-not-valid"))

        self.assertEqual(raised.exception.status_code, 400)

    async def test_malformed_pdf_upload_returns_400(self):
        with self.assertRaises(HTTPException) as raised:
            await upload_report(make_upload("broken.pdf", "application/pdf", b"%PDF-not-valid"))

        self.assertEqual(raised.exception.status_code, 400)

    async def test_analysis_extracts_text_from_pdf_bytes_without_saving_a_copy(self):
        result = await analyze_report(
            make_upload("report.pdf", "application/pdf", make_text_pdf("Hemoglobin: 13.2 g/dL"))
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["medical_data"]["hemoglobin"], 13.2)
        self.assertFalse(Path("uploads/report.pdf").exists())


if __name__ == "__main__":
    unittest.main()
