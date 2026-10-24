import XCTest

@testable import TilavetCore

final class EngineTests: XCTestCase {
    func testGolden() throws {
        let index = try Golden.index()
        let units = mealUnits(try parseTanzil(String(contentsOf: Golden.root.appendingPathComponent(
            "data/raw/tr.diyanet.txt"), encoding: .utf8)))
        let streams = try XCTUnwrap(Golden.json("engine") as? [[String: Any]])
        var differing: [String] = []

        for stream in streams {
            let engine = PositionEngine(index)
            let policy = EmissionPolicy(units, cooldownS: 300)
            var got: [String] = []
            for window in stream["windows"] as! [[Any]] {
                let t = window[0] as! Double
                for event in engine.feed(t, words(normalize(window[1] as! String))) {
                    got.append(describe(event))
                    if let play = policy.on(event) {
                        got.append("Play \(play.t) \(play.unit.sura):\(play.unit.first)-\(play.unit.last)")
                    }
                }
            }

            let expected = (stream["records"] as! [[String: Any]]).map(describe)
            if got != expected {
                differing.append(stream["id"] as! String)
            }
        }

        XCTAssertEqual(differing, [], "\(differing.count) of \(streams.count) streams differ")
    }

    private func describe(_ event: Event) -> String {
        switch event {
        case let .confirmed(t, ref, mode, score):
            return "AyahConfirmed \(t) \(ref.sura):\(ref.aya) \(mode.rawValue) \(score)"
        case let .lost(t):
            return "Lost \(t)"
        }
    }

    private func describe(_ record: [String: Any]) -> String {
        let t = record["t"] as! Double
        switch record["type"] as! String {
        case "AyahConfirmed":
            let ref = record["ref"] as! [Int]
            return "AyahConfirmed \(t) \(ref[0]):\(ref[1]) \(record["mode"] as! String) \(record["score"] as! Int)"
        case "Lost":
            return "Lost \(t)"
        default:
            let unit = record["unit"] as! [Int]
            return "Play \(t) \(unit[0]):\(unit[1])-\(unit[2])"
        }
    }
}
