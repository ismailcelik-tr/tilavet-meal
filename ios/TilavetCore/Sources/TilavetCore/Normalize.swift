/// Mirrors tilavet.corpus.normalize: code point rules, so Swift and Python agree byte for byte.
public func normalize(_ text: String) -> String {
    var out = String.UnicodeScalarView()
    var pendingSpace = false

    for scalar in text.unicodeScalars {
        if isMark(scalar) {
            continue
        }

        let letter = letterMap[scalar] ?? scalar
        if isArabicLetter(letter) {
            if pendingSpace && !out.isEmpty {
                out.append(" ")
            }
            pendingSpace = false
            out.append(letter)
            continue
        }

        // Python: non-letters become spaces, whitespace runs collapse, ends are stripped.
        pendingSpace = true
    }

    return String(out)
}

/// Words of normalized text (Python `str.split()`).
public func words(_ normalized: String) -> [String] {
    normalized.split(separator: " ").map(String.init)
}

/// Python `str.isspace()`: Unicode White_Space plus the information separators U+001C–U+001F.
func isPythonSpace(_ scalar: Unicode.Scalar) -> Bool {
    scalar.properties.isWhitespace || (0x1C...0x1F).contains(scalar.value)
}

private let letterMap: [Unicode.Scalar: Unicode.Scalar] = [
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ی": "ي", "ک": "ك",
]

// Harakat, Quranic annotation marks (waqf, small letters), superscript alef, tatweel.
private func isMark(_ scalar: Unicode.Scalar) -> Bool {
    switch scalar.value {
    case 0x0610...0x061A, 0x064B...0x065F, 0x0670, 0x06D6...0x06ED, 0x0640:
        return true
    default:
        return false
    }
}

private func isArabicLetter(_ scalar: Unicode.Scalar) -> Bool {
    (0x0621...0x064A).contains(scalar.value)
}
