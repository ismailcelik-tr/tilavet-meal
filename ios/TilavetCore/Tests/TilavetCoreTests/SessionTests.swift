import XCTest

@testable import TilavetCore

private let text = "قل أعوذ برب الناس"
private let unit = MealUnit(sura: 114, first: 1, last: 1, text: "a")

private final class FakeRecognizer: Recognizer {
    var lengths: [Int] = []

    func transcribe(_ samples: [Float]) -> String {
        lengths.append(samples.count)
        return text
    }
}

private final class FakeEngine: Engine {
    var fed: [(Double, [String])] = []
    let events: [Event]

    init(_ events: [Event] = []) {
        self.events = events
    }

    func feed(_ t: Double, _ words: [String]) -> [Event] {
        fed.append((t, words))
        return events
    }
}

private final class Clock {
    var now = 0.0
}

private func seconds(_ s: Double) -> [Float] {
    [Float](repeating: 0, count: Int((s * Double(sampleRate)).rounded()))
}

final class SessionTests: XCTestCase {
    private func session(_ engine: Engine = FakeEngine(), _ clock: Clock = Clock(),
                         _ recognizer: Recognizer = FakeRecognizer()) -> LiveSession {
        LiveSession(recognizer: recognizer, engine: engine, policy: EmissionPolicy([unit], cooldownS: 300),
                    player: MealPlayer(durationS: { _ in 5.0 }, maxWaitS: 15), clock: { clock.now }, hopS: 1.0,
                    windowS: 12.0)
    }

    func testWindowClosesEveryHopWithComputeInTime() {
        let clock = Clock(), engine = FakeEngine()
        let s = session(engine, clock)

        XCTAssertEqual(s.feed(seconds(0.5), arrivedAt: 10.0), [])
        clock.now = 10.75
        XCTAssertEqual(s.feed(seconds(0.5), arrivedAt: 10.5),
                       [.window(Window(heardS: 1.0, t: 1.25, text: text, skipped: 0))])
        XCTAssertEqual(engine.fed.map(\.0), [1.25])
        XCTAssertEqual(engine.fed.map(\.1), [words(normalize(text))])
    }

    func testBacklogTranscribesLatestWindowOnly() {
        let recognizer = FakeRecognizer()
        let s = session(FakeEngine(), Clock(), recognizer)

        let records = s.feed(seconds(3.0), arrivedAt: 0.0)

        XCTAssertEqual(records, [.window(Window(heardS: 3.0, t: 3.0, text: text, skipped: 2))])
        XCTAssertEqual(recognizer.lengths, [3 * sampleRate])
    }

    func testWindowKeepsLast12Seconds() {
        let recognizer = FakeRecognizer()
        let s = session(FakeEngine(), Clock(), recognizer)

        for _ in 0..<13 {
            _ = s.feed(seconds(1.0), arrivedAt: 0.0)
        }

        XCTAssertEqual(recognizer.lengths.last, 12 * sampleRate)
    }

    func testConfirmedAyahReachesPlayer() {
        let clock = Clock()
        clock.now = 0.25
        let confirmed = Event.confirmed(t: 1.25, ref: AyahRef(sura: 114, aya: 1), mode: .track, score: 6)
        let s = session(FakeEngine([confirmed]), clock)

        let records = s.feed(seconds(1.0), arrivedAt: 0.0)

        let play = Play(t: 1.25, unit: unit, trigger: AyahRef(sura: 114, aya: 1))
        XCTAssertEqual(records, [.window(Window(heardS: 1.0, t: 1.25, text: text, skipped: 0)), .event(confirmed),
                                 .play(play), .player(.started(t: 1.25, play: play))])
    }
}
