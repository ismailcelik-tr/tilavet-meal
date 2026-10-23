from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

__all__ = ["AyahRef", "MealUnit", "load_tanzil", "meal_units", "parse_tanzil", "strip_basmala"]

_COMMENT = "#"
_SEPARATOR = "|"
_BASMALA = "بسم الله الرحمن الرحيم"
_FATIHA = 1


class AyahRef(NamedTuple):
    sura: int
    aya: int


@dataclass(frozen=True)
class MealUnit:
    """Consecutive ayahs that a translation renders as one sentence."""

    sura: int
    first: int
    last: int
    text: str

    @property
    def refs(self) -> tuple[AyahRef, ...]:
        return tuple(AyahRef(self.sura, aya) for aya in range(self.first, self.last + 1))


def parse_tanzil(lines: Iterable[str]) -> dict[AyahRef, str]:
    """Parse Tanzil `txt-2` format: `sura|aya|text`."""
    result: dict[AyahRef, str] = {}

    for line in lines:
        line = line.rstrip("\n")
        if not line.strip() or line.startswith(_COMMENT):
            continue

        sura, aya, text = line.split(_SEPARATOR, 2)
        ref = AyahRef(int(sura), int(aya))
        if ref in result:
            raise ValueError(f"duplicate ayah {ref}")

        result[ref] = text

    return result


def load_tanzil(path: Path) -> dict[AyahRef, str]:
    with path.open(encoding="utf-8") as f:
        return parse_tanzil(f)


def strip_basmala(ref: AyahRef, text: str) -> str:
    """Remove the basmala that Tanzil simple text prefixes to each sura's first ayah.

    Only in Al-Fatiha is the basmala an ayah of its own.
    """
    if ref.aya != 1 or ref.sura == _FATIHA or not text.startswith(_BASMALA):
        return text

    return text.removeprefix(_BASMALA).strip()


def meal_units(meal: Mapping[AyahRef, str]) -> list[MealUnit]:
    """Group consecutive ayahs of a sura that share identical translation text.

    Some translations (e.g. Tanzil tr.diyanet) render a multi-ayah sentence once
    and repeat it under every ayah it covers.
    """
    units: list[MealUnit] = []

    for ref in sorted(meal):
        text = meal[ref]
        last = units[-1] if units else None
        if last and last.sura == ref.sura and last.last == ref.aya - 1 and last.text == text:
            units[-1] = MealUnit(last.sura, last.first, ref.aya, text)
            continue

        units.append(MealUnit(ref.sura, ref.aya, ref.aya, text))

    return units
