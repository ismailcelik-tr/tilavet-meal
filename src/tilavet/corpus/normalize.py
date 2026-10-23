import re

__all__ = ["normalize"]

# Harakat, Quranic annotation marks (waqf, small letters), superscript alef, tatweel.
_MARKS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_NON_LETTER = re.compile(r"[^ء-ي\s]")
_WHITESPACE = re.compile(r"\s+")

# ASR output spells hamza seats and alef forms inconsistently; fold them to one letter.
_LETTER_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ي",
        "ی": "ي",
        "ک": "ك",
    }
)


def normalize(text: str) -> str:
    text = _MARKS.sub("", text)
    text = text.translate(_LETTER_MAP)
    text = _NON_LETTER.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()
