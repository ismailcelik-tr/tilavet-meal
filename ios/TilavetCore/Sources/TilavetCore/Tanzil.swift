public struct AyahRef: Hashable, Comparable, Codable, Sendable {
    public let sura: Int
    public let aya: Int

    public init(sura: Int, aya: Int) {
        self.sura = sura
        self.aya = aya
    }

    public static func < (lhs: AyahRef, rhs: AyahRef) -> Bool {
        (lhs.sura, lhs.aya) < (rhs.sura, rhs.aya)
    }
}

/// Consecutive ayahs that a translation renders as one sentence.
public struct MealUnit: Hashable, Sendable {
    public let sura: Int
    public let first: Int
    public let last: Int
    public let text: String

    var refs: [AyahRef] {
        (first...last).map { AyahRef(sura: sura, aya: $0) }
    }
}

public enum TanzilError: Error {
    case malformed(String)
    case duplicate(AyahRef)
}

private let comment: Character = "#"
private let separator: Character = "|"
private let basmala = Array("بسم الله الرحمن الرحيم".unicodeScalars)
private let fatiha = 1

/// Tanzil `txt-2` format: `sura|aya|text`.
public func parseTanzil(_ text: String) throws -> [AyahRef: String] {
    var result: [AyahRef: String] = [:]

    for line in text.split(separator: "\n", omittingEmptySubsequences: false) {
        if line.unicodeScalars.allSatisfy(isPythonSpace) || line.first == comment {
            continue
        }

        let parts = line.split(separator: separator, maxSplits: 2, omittingEmptySubsequences: false)
        guard parts.count == 3, let sura = Int(parts[0]), let aya = Int(parts[1]) else {
            throw TanzilError.malformed(String(line))
        }

        let ref = AyahRef(sura: sura, aya: aya)
        if result[ref] != nil {
            throw TanzilError.duplicate(ref)
        }
        result[ref] = String(parts[2])
    }

    return result
}

/// Remove the basmala that Tanzil simple text prefixes to each sura's first ayah; in Al-Fatiha it is an ayah.
func stripBasmala(_ ref: AyahRef, _ text: String) -> String {
    let scalars = Array(text.unicodeScalars)
    if ref.aya != 1 || ref.sura == fatiha || !scalars.starts(with: basmala) {
        return text
    }

    let rest = scalars.dropFirst(basmala.count).drop(while: isPythonSpace)
    let trimmed = rest.reversed().drop(while: isPythonSpace).reversed()
    var view = String.UnicodeScalarView()
    view.append(contentsOf: trimmed)
    return String(view)
}

/// Group consecutive ayahs of a sura that share identical translation text.
public func mealUnits(_ meal: [AyahRef: String]) -> [MealUnit] {
    var units: [MealUnit] = []

    for ref in meal.keys.sorted() {
        let text = meal[ref]!
        if let last = units.last, last.sura == ref.sura, last.last == ref.aya - 1, last.text == text {
            units[units.count - 1] = MealUnit(sura: last.sura, first: last.first, last: ref.aya, text: text)
            continue
        }

        units.append(MealUnit(sura: ref.sura, first: ref.aya, last: ref.aya, text: text))
    }

    return units
}
