def classify_medical_report(data: dict) -> dict:
    """
    Basic rule-based screening classifier.

    This is a prototype baseline for MEDAI.
    It does NOT provide a medical diagnosis.
    """

    flags = []

    hemoglobin = data.get("hemoglobin")
    wbc = data.get("wbc")
    platelets = data.get("platelets")
    glucose = data.get("glucose")
    cholesterol = data.get("cholesterol")
    rbc = data.get("rbc")

    # --------------------------------
    # Basic screening rules
    # --------------------------------

    if glucose is not None:
        if glucose >= 126:
            flags.append("Glucose value requires review.")
        elif glucose >= 100:
            flags.append("Glucose value is above the preferred range.")

    if cholesterol is not None:
        if cholesterol >= 240:
            flags.append("Total cholesterol value requires review.")
        elif cholesterol >= 200:
            flags.append("Total cholesterol is elevated.")

    if hemoglobin is not None:
        if hemoglobin < 12:
            flags.append("Hemoglobin value is below the reference range.")
        elif hemoglobin > 17.5:
            flags.append("Hemoglobin value is above the reference range.")

    if wbc is not None:
        if wbc < 4000:
            flags.append("WBC count is below the reference range.")
        elif wbc > 11000:
            flags.append("WBC count is above the reference range.")

    if platelets is not None:
        if platelets < 150000:
            flags.append("Platelet count is below the reference range.")
        elif platelets > 450000:
            flags.append("Platelet count is above the reference range.")

    if rbc is not None:
        if rbc < 4.0:
            flags.append("RBC value is below the reference range.")
        elif rbc > 6.0:
            flags.append("RBC value is above the reference range.")

    # --------------------------------
    # Overall classification
    # --------------------------------

    rule_flag_count = len(flags)
    required_parameters = (
        "hemoglobin",
        "wbc",
        "platelets",
        "glucose",
        "cholesterol",
        "rbc",
    )
    incomplete = any(data.get(parameter) is None for parameter in required_parameters)

    if incomplete:
        flags.append(
            "One or more values are missing or use an unsupported or ambiguous unit; "
            "review is needed and interpretation is incomplete."
        )
        status = "REVIEW"
        confidence = 0.82

    elif rule_flag_count == 0:
        status = "NORMAL"
        confidence = 0.92

    elif rule_flag_count <= 2:
        status = "REVIEW"
        confidence = 0.82

    else:
        status = "ATTENTION"
        confidence = 0.75

    return {
        "status": status,
        "confidence": confidence,
        "flags": flags,
    }
