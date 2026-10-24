import XCTest

@testable import TilavetCore

final class AlignTests: XCTestCase {
    func testGolden() throws {
        let index = try Golden.index()
        let cases = try XCTUnwrap(Golden.json("align") as? [[String: Any]])
        var mismatches: [Int] = []

        for (n, c) in cases.enumerated() {
            let hyp = try XCTUnwrap(c["hyp"] as? [String])
            let lo = try XCTUnwrap(c["lo"] as? Int), hi = try XCTUnwrap(c["hi"] as? Int)
            let minScore = try XCTUnwrap(c["min_score"] as? Int)
            let expected = try XCTUnwrap(c["expected"] as? [[String: Any]]).map { e in
                Alignment(
                    score: e["score"] as! Int, corpusStart: e["corpus_start"] as! Int, corpusEnd: e["corpus_end"] as! Int,
                    pairs: (e["pairs"] as! [[Int]]).map { Pair(hyp: $0[0], pos: $0[1]) }, hypEnd: e["hyp_end"] as! Int)
            }
            if alignAll(hyp, index.words, lo, hi, minScore) != expected {
                mismatches.append(n)
            }
        }

        XCTAssertEqual(mismatches, [], "cases differ")
    }

    func testSimilarityIsPythonIndel() {
        XCTAssertEqual(indelSimilarity("abc", "abd"), 2.0 / 3.0, accuracy: 1e-12)
        XCTAssertEqual(indelSimilarity("", ""), 1.0)
        XCTAssertEqual(indelSimilarity("وله", "له"), 0.8, accuracy: 1e-12)
    }

    func testIndexLooksUpWordsAndAyahs() {
        let a = AyahRef(sura: 1, aya: 1), b = AyahRef(sura: 1, aya: 2)
        let index = QuranIndex.build([b: ["x", "y"], a: ["y"]])

        XCTAssertEqual(index.words, ["y", "x", "y"])
        XCTAssertEqual(index.positions("y"), [0, 2])
        XCTAssertEqual(index.span(b), 1..<3)
        XCTAssertEqual(index.ordinalAt(2), 1)
        XCTAssertEqual(index.ref(1), b)
    }
}
