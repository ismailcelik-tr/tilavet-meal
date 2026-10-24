import XCTest

@testable import TilavetCore

final class NormalizeTests: XCTestCase {
    func testGolden() throws {
        let pairs = try XCTUnwrap(Golden.json("normalize") as? [[String]])
        let mismatches = pairs.filter { Array(normalize($0[0]).unicodeScalars) != Array($0[1].unicodeScalars) }

        XCTAssertEqual(mismatches.count, 0, "first: \(mismatches.prefix(5).map { [$0[0], normalize($0[0]), $0[1]] })")
    }

    func testBasmalaIsStrippedExceptInFatiha() {
        let basmala = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        let plain = "بسم الله الرحمن الرحيم"

        XCTAssertEqual(stripBasmala(AyahRef(sura: 2, aya: 1), "\(plain) الم"), "الم")
        XCTAssertEqual(stripBasmala(AyahRef(sura: 1, aya: 1), plain), plain)
        XCTAssertEqual(stripBasmala(AyahRef(sura: 2, aya: 1), basmala), basmala)
    }

    func testIdenticalConsecutiveMealsMergeIntoOneUnit() throws {
        let meal = try parseTanzil("2|8|a\n2|9|a\n2|10|b\n3|1|b\n")

        XCTAssertEqual(mealUnits(meal), [
            MealUnit(sura: 2, first: 8, last: 9, text: "a"),
            MealUnit(sura: 2, first: 10, last: 10, text: "b"),
            MealUnit(sura: 3, first: 1, last: 1, text: "b"),
        ])
    }
}
