import math
import re


_VALUE_PATTERN = r"(?P<value>\d+(?:[.,]\d+)*)"
_LABEL_SUFFIX = r"\s*(?P<parenthetical>\([^()\r\n]*\)\s*)?[:=\u2013\u2014\u2212-]?\s*"
_UNIT_TOKEN = (
    r"(?:[x\u00d7]\s*)?10\s*(?:\^\s*\d+|[\u00b3\u2079\u00b9\u00b2]+)?"
    r"\s*/\s*[A-Za-z\u00b5\u03bc]+"
    r"|/?[A-Za-z\u00b5\u03bc]+\s*/\s*[A-Za-z\u00b5\u03bc0-9^\u00b3\u2079\u00b9\u00b2]+"
    r"|/[A-Za-z\u00b5\u03bc]+"
)


def _parse_number(value: str):
    if "," in value and "." in value:
        decimal_separator = "." if value.rfind(".") > value.rfind(",") else ","
        grouping_separator = "," if decimal_separator == "." else "."
        normalized = value.replace(grouping_separator, "").replace(decimal_separator, ".")
        return float(normalized)

    if "," in value:
        groups = value.split(",")
        western_grouping = (
            len(groups) > 1
            and len(groups[0]) <= 3
            and all(len(group) == 3 for group in groups[1:])
        )
        indian_grouping = (
            len(groups) > 2
            and len(groups[0]) <= 2
            and all(len(group) == 2 for group in groups[1:-1])
            and len(groups[-1]) == 3
        )
        if western_grouping or indian_grouping:
            return float("".join(groups))
        if len(groups) > 2:
            return None
        return float(value.replace(",", "."))

    return float(value)


def _canonical_unit(parameter: str, unit: str | None) -> tuple[str, float] | None:
    if not unit:
        return None

    normalized = unit.strip().strip("()").lower()
    normalized = normalized.replace("μ", "µ").replace("µ", "u").replace("×", "x")
    normalized = normalized.replace("³", "3").replace("⁹", "9")
    normalized = normalized.replace("¹²", "12").replace("^", "")
    normalized = re.sub(r"\s+", "", normalized)

    if parameter == "hemoglobin":
        return {"g/dl": ("g/dL", 1), "g/l": ("g/L", 0.1)}.get(normalized)
    if parameter in {"wbc", "platelets"}:
        return {
            "/ul": ("/uL", 1),
            "cells/ul": ("cells/uL", 1),
            "cell/ul": ("cells/uL", 1),
            "/mm3": ("/mm3", 1),
            "cells/mm3": ("cells/mm3", 1),
            "cell/mm3": ("cells/mm3", 1),
            "103/ul": ("10^3/uL", 1000),
            "x103/ul": ("10^3/uL", 1000),
            "109/l": ("10^9/L", 1000),
            "x109/l": ("10^9/L", 1000),
        }.get(normalized)
    if parameter == "glucose":
        return {"mg/dl": ("mg/dL", 1), "mmol/l": ("mmol/L", 18.018)}.get(normalized)
    if parameter == "cholesterol":
        return {"mg/dl": ("mg/dL", 1), "mmol/l": ("mmol/L", 38.67)}.get(normalized)
    if parameter == "rbc":
        return {"m/ul": ("M/uL", 1), "1012/l": ("10^12/L", 1)}.get(normalized)
    return None


def _extract_match(match: re.Match, parameter: str):
    parenthetical = match.group("parenthetical")
    suffix = match.group("suffix")
    split_line_unit = match.group("split_line_unit")
    units = []
    if parenthetical:
        units.append(parenthetical.strip())
    if suffix:
        units.append(suffix.strip())
    if split_line_unit:
        units.append(split_line_unit.strip())
    if not units:
        return None

    canonical_units = [_canonical_unit(parameter, unit) for unit in units]
    if any(unit is None for unit in canonical_units):
        return None
    if len({unit[1] for unit in canonical_units}) > 1:
        return None

    value_text = match.group("value")
    if "," in value_text and "." not in value_text:
        groups = value_text.split(",")
        is_ambiguous_single_group = len(groups) == 2 and len(groups[-1]) == 3
        grouping_is_explicit = parameter in {"wbc", "platelets"} and canonical_units[0][1] == 1
        if is_ambiguous_single_group and not grouping_is_explicit:
            return None

    value = _parse_number(value_text)
    if value is None:
        return None
    return value * canonical_units[0][1]


def _is_cholesterol_subtype(text: str, match_start: int) -> bool:
    preceding_text = text[max(0, match_start - 20):match_start]
    return bool(re.search(r"\b(?:HDL|LDL|VLDL|non-HDL)[\s-]+$", preceding_text, re.IGNORECASE))


def _extract_parameter(text: str, labels: str, parameter: str):
    matches = re.finditer(
        rf"\b(?:{labels})\b{_LABEL_SUFFIX}{_VALUE_PATTERN}"
        rf"(?P<suffix>[ \t]+(?:{_UNIT_TOKEN}))?"
        rf"(?:\r?\n[ \t]*(?P<split_line_unit>{_UNIT_TOKEN})[ \t]*(?=\r?$))?",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    values = []
    for match in matches:
        if parameter == "cholesterol" and _is_cholesterol_subtype(text, match.start()):
            continue
        if re.match(r"\s*[-\u2013\u2014]\s*\d", text[match.end():]):
            return None
        value = _extract_match(match, parameter)
        if value is None:
            return None
        values.append(value)

    if not values or any(
        not math.isclose(value, values[0], rel_tol=1e-9, abs_tol=1e-9)
        for value in values[1:]
    ):
        return None
    return values[0]


def extract_medical_parameters(text: str) -> dict:
    """Extract supported laboratory values into the classifier's canonical scales.

    Units may appear in parentheses between a label and value, directly after
    the value, or on the line immediately after a numeric-only table result.
    Supported units: hemoglobin g/dL or g/L; WBC and platelets
    cells/uL, cells/mm3, 10^3/uL, or 10^9/L; glucose mg/dL or mmol/L;
    cholesterol mg/dL or mmol/L; RBC M/uL or 10^12/L. Values without a
    recognized, unambiguous unit remain unavailable. A single comma followed
    by three digits is treated as ambiguous for fractional parameters. This is
    not diagnosis.
    """

    return {
        "hemoglobin": _extract_parameter(
            text, r"hemog[1il]obin|haemoglobin|hgb", "hemoglobin"
        ),
        "wbc": _extract_parameter(
            text, r"wbc|white blood cells?|white blood cell count", "wbc"
        ),
        "platelets": _extract_parameter(text, r"platelets?|platelet count", "platelets"),
        "glucose": _extract_parameter(
            text, r"glucose|blood glucose|fasting glucose", "glucose"
        ),
        "cholesterol": _extract_parameter(
            text, r"total cholesterol|cholesterol", "cholesterol"
        ),
        "rbc": _extract_parameter(text, r"rbc|red blood cells?|red blood cell count", "rbc"),
    }
