import re


def extract_medical_parameters(text: str) -> dict:
    """
    Extract common laboratory parameters from medical report text.

    This is a basic rule-based extraction layer.
    It is not intended to provide medical diagnosis.
    """

    text = text.lower()

    data = {
        "hemoglobin": None,
        "wbc": None,
        "platelets": None,
        "glucose": None,
        "cholesterol": None,
        "rbc": None,
    }

    # Hemoglobin
    hemoglobin_match = re.search(
        r"hemoglobin\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        text,
    )

    if hemoglobin_match:
        data["hemoglobin"] = float(
            hemoglobin_match.group(1)
        )

    # WBC
    wbc_match = re.search(
        r"(?:wbc|white blood cells?|white blood cell count)"
        r"\s*[:\-]?\s*([\d,]+)",
        text,
    )

    if wbc_match:
        data["wbc"] = int(
            wbc_match.group(1).replace(",", "")
        )

    # Platelets
    platelet_match = re.search(
        r"(?:platelets?|platelet count)"
        r"\s*[:\-]?\s*([\d,]+)",
        text,
    )

    if platelet_match:
        data["platelets"] = int(
            platelet_match.group(1).replace(",", "")
        )

    # Glucose
    glucose_match = re.search(
        r"(?:glucose|blood glucose|fasting glucose)"
        r"\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        text,
    )

    if glucose_match:
        data["glucose"] = float(
            glucose_match.group(1)
        )

    # Cholesterol
    cholesterol_match = re.search(
        r"(?:total cholesterol|cholesterol)"
        r"\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        text,
    )

    if cholesterol_match:
        data["cholesterol"] = float(
            cholesterol_match.group(1)
        )

    # RBC
    rbc_match = re.search(
        r"(?:rbc|red blood cells?|red blood cell count)"
        r"\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        text,
    )

    if rbc_match:
        data["rbc"] = float(
            rbc_match.group(1)
        )

    return data