import unittest

from services.classifier import classify_medical_report
from services.medical_extractor import extract_medical_parameters


class MedicalParameterExtractionTests(unittest.TestCase):
    def test_extracts_decimal_comma_with_parenthetical_unit_and_reference_range(self):
        data = extract_medical_parameters(
            "Hemoglobin (g/dL)\n: 13,2 (reference range: 12,0 - 16,0)"
        )

        self.assertEqual(data["hemoglobin"], 13.2)

    def test_extracts_comma_grouped_wbc_after_parenthetical_unit(self):
        data = extract_medical_parameters("White blood cell count (10^3/uL): 7.25")

        self.assertEqual(data["wbc"], 7250)

    def test_extracts_platelets_with_equals_separator_and_unit(self):
        data = extract_medical_parameters("Platelets = 250,000 /uL")

        self.assertEqual(data["platelets"], 250000)

    def test_extracts_indian_grouped_platelet_count(self):
        data = extract_medical_parameters("Platelet count: 2,50,000 /uL")

        self.assertEqual(data["platelets"], 250000)

    def test_extracts_table_results_with_label_value_and_unit_on_adjacent_lines(self):
        data = extract_medical_parameters(
            "Hemoglobin\n13.4\ng/dL\n"
            "WBC\n7,200\ncells/µL\n"
            "Platelets\n250,000\ncells/µL\n"
            "Glucose\n90\nmg/dL\n"
            "Total cholesterol\n180\nmg/dL\n"
            "RBC\n5.0\nM/µL"
        )

        self.assertEqual(
            data,
            {
                "hemoglobin": 13.4,
                "wbc": 7200,
                "platelets": 250000,
                "glucose": 90,
                "cholesterol": 180,
                "rbc": 5.0,
            },
        )

    def test_table_reference_range_without_a_patient_result_stays_unavailable(self):
        data = extract_medical_parameters("Hemoglobin\n12.0 - 16.0\ng/dL")

        self.assertIsNone(data["hemoglobin"])

    def test_extracts_glucose_after_em_dash_with_decimal_unit_and_range(self):
        data = extract_medical_parameters(
            "Blood glucose — 98.6 mg/dL (reference: 70-100)"
        )

        self.assertEqual(data["glucose"], 98.6)

    def test_extracts_cholesterol_with_parenthetical_unit(self):
        data = extract_medical_parameters("Total cholesterol (mg/dL): 198.5")

        self.assertEqual(data["cholesterol"], 198.5)

    def test_reference_range_without_a_result_does_not_become_a_value(self):
        data = extract_medical_parameters(
            "Hemoglobin (g/dL)\nReference range: 12.0 - 16.0"
        )

        self.assertIsNone(data["hemoglobin"])

    def test_label_adjacent_hemoglobin_reference_range_is_not_a_result(self):
        data = extract_medical_parameters("Hemoglobin (g/dL): 12.0-16.0")

        self.assertIsNone(data["hemoglobin"])

    def test_label_adjacent_wbc_reference_range_is_not_a_result(self):
        data = extract_medical_parameters("WBC: 4,000-11,000 cells/uL")

        self.assertIsNone(data["wbc"])

    def test_separate_line_reference_range_is_not_a_result(self):
        data = extract_medical_parameters(
            "Hemoglobin (g/dL):\n12.0 - 16.0 (reference range)"
        )

        self.assertIsNone(data["hemoglobin"])

    def test_genuine_result_followed_by_separate_line_reference_range_is_preserved(self):
        data = extract_medical_parameters(
            "Hemoglobin (g/dL): 13.4\nReference range: 12.0 - 16.0"
        )

        self.assertEqual(data["hemoglobin"], 13.4)

    def test_reference_range_with_label_unit_does_not_become_a_result(self):
        data = extract_medical_parameters("WBC (cells/uL): 4,000-11,000")

        self.assertIsNone(data["wbc"])

    def test_recovers_common_ocr_digit_for_letter_confusion_in_label(self):
        data = extract_medical_parameters("Hemog1obin: 14.1 g/dL")

        self.assertEqual(data["hemoglobin"], 14.1)

    def test_unreadable_or_absent_values_remain_missing_and_are_not_normal(self):
        data = extract_medical_parameters("Report text with no supported lab values")

        self.assertTrue(all(value is None for value in data.values()))
        classification = classify_medical_report(data)
        self.assertEqual(classification["status"], "REVIEW")
        self.assertIn("interpretation is incomplete", classification["flags"][0])

    def test_partial_values_are_not_presented_as_a_complete_normal_result(self):
        data = extract_medical_parameters("Glucose: 90 mg/dL")

        self.assertEqual(data["glucose"], 90.0)
        self.assertIsNone(data["hemoglobin"])
        classification = classify_medical_report(data)
        self.assertEqual(classification["status"], "REVIEW")
        self.assertTrue(
            any("interpretation is incomplete" in flag for flag in classification["flags"])
        )

    def test_complete_values_with_no_triggered_rule_keep_normal_status(self):
        data = {
            "hemoglobin": 14.0,
            "wbc": 7000,
            "platelets": 250000,
            "glucose": 90.0,
            "cholesterol": 180.0,
            "rbc": 5.0,
        }

        classification = classify_medical_report(data)

        self.assertEqual(classification["status"], "NORMAL")

    def test_wbc_scaled_and_base_units_normalize_to_classifier_scale(self):
        scaled = extract_medical_parameters("WBC (10^3/uL): 7.2")
        base = extract_medical_parameters("WBC: 7,200 cells/uL")

        self.assertEqual(scaled["wbc"], 7200)
        self.assertEqual(base["wbc"], 7200)

    def test_platelet_scaled_and_base_units_normalize_to_classifier_scale(self):
        scaled = extract_medical_parameters("Platelets (10^3/uL): 250")
        base = extract_medical_parameters("Platelets: 250,000 cells/uL")

        self.assertEqual(scaled["platelets"], 250000)
        self.assertEqual(base["platelets"], 250000)

    def test_supported_unit_conversions_preserve_equivalent_values(self):
        data = extract_medical_parameters(
            "Hemoglobin (g/L): 140\n"
            "Glucose (mmol/L): 5.0\n"
            "Total cholesterol (mmol/L): 4.65\n"
            "RBC (10^12/L): 5.0"
        )

        self.assertEqual(data["hemoglobin"], 14.0)
        self.assertAlmostEqual(data["glucose"], 90.09, places=2)
        self.assertAlmostEqual(data["cholesterol"], 179.82, places=2)
        self.assertEqual(data["rbc"], 5.0)

    def test_recognizes_unicode_scaled_count_and_rbc_unit_forms(self):
        data = extract_medical_parameters(
            "WBC (×10³/µL): 7.2\n"
            "Platelets: 250 x10^9/L\n"
            "RBC (10¹²/L): 5.0"
        )

        self.assertEqual(data["wbc"], 7200)
        self.assertEqual(data["platelets"], 250000)
        self.assertEqual(data["rbc"], 5.0)

    def test_total_cholesterol_is_not_taken_from_hdl_or_ldl_rows(self):
        data = extract_medical_parameters(
            "HDL cholesterol: 50 mg/dL\n"
            "LDL cholesterol: 120 mg/dL\n"
            "Total cholesterol: 210 mg/dL"
        )

        self.assertEqual(data["cholesterol"], 210)

    def test_conflicting_duplicate_parameter_results_are_unavailable(self):
        data = extract_medical_parameters(
            "Hemoglobin (g/dL): 14.0\n"
            "WBC (10^3/uL): 7.2\nWBC: 12,000 cells/uL\n"
            "Platelets (10^3/uL): 250\n"
            "Glucose (mg/dL): 90\n"
            "Total cholesterol (mg/dL): 180\n"
            "RBC (M/uL): 5.0"
        )

        self.assertIsNone(data["wbc"])
        self.assertEqual(classify_medical_report(data)["status"], "REVIEW")

    def test_equivalent_duplicate_results_remain_available(self):
        data = extract_medical_parameters(
            "WBC (10^3/uL): 7.2\nWBC: 7,200 cells/uL"
        )

        self.assertEqual(data["wbc"], 7200)

    def test_single_comma_with_three_trailing_digits_is_ambiguous_for_fractional_values(self):
        data = extract_medical_parameters(
            "RBC (M/uL): 5,234\nGlucose (mg/dL): 1,234"
        )

        self.assertIsNone(data["rbc"])
        self.assertIsNone(data["glucose"])

    def test_missing_unsupported_or_conflicting_units_are_unavailable(self):
        data = extract_medical_parameters(
            "Hemoglobin: 14.0\n"
            "WBC (10^6/uL): 7.2\n"
            "Glucose: 90 mg/L\n"
            "Total cholesterol (mmol/L): 4.65 mg/dL"
        )

        self.assertIsNone(data["hemoglobin"])
        self.assertIsNone(data["wbc"])
        self.assertIsNone(data["glucose"])
        self.assertIsNone(data["cholesterol"])

    def test_unavailable_unit_values_force_review_instead_of_normal(self):
        data = extract_medical_parameters(
            "Hemoglobin (g/dL): 14.0\n"
            "WBC (10^3/uL): 7.2\n"
            "Platelets (10^3/uL): 250\n"
            "Glucose: 90 mg/L\n"
            "Total cholesterol (mg/dL): 180\n"
            "RBC (M/uL): 5.0"
        )

        classification = classify_medical_report(data)

        self.assertIsNone(data["glucose"])
        self.assertEqual(classification["status"], "REVIEW")
        self.assertTrue(any("unit" in flag.lower() for flag in classification["flags"]))

    def test_missing_required_unit_keeps_multiple_rule_flags_at_review(self):
        classification = classify_medical_report(
            {
                "hemoglobin": 10.0,
                "wbc": 12000,
                "platelets": 500000,
                "glucose": None,
                "cholesterol": 180.0,
                "rbc": 5.0,
            }
        )

        self.assertEqual(classification["status"], "REVIEW")
        self.assertTrue(any("review is needed" in flag.lower() for flag in classification["flags"]))


if __name__ == "__main__":
    unittest.main()
