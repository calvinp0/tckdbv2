def normalize_optional_text(value: str | None) -> str | None:
    """Trim optional text inputs and collapse blank strings to None."""

    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def normalize_required_text(value: str) -> str:
    """Trim required text inputs and reject blank values."""

    normalized = value.strip()
    if not normalized:
        raise ValueError("Value must not be blank")
    return normalized
