import XCTest

@testable import TilavetCore

final class PlayerTests: XCTestCase {
    private let units = (1...6).map { MealUnit(sura: 114, first: $0, last: $0, text: String($0)) }

    private func play(_ t: Double, _ i: Int) -> Play {
        Play(t: t, unit: units[i], trigger: AyahRef(sura: 114, aya: i + 1))
    }

    private func player(_ durationS: Double) -> MealPlayer {
        MealPlayer(durationS: { _ in durationS }, maxWaitS: 15)
    }

    func testIdlePlayerStartsAtOnce() {
        XCTAssertEqual(player(5).submit(play(1.0, 0)), [.started(t: 1.0, play: play(1.0, 0))])
    }

    func testMealsNeverOverlap() {
        let p = player(5)
        _ = p.submit(play(1.0, 0))

        XCTAssertEqual(p.submit(play(2.0, 1)), [])
        XCTAssertEqual(p.advance(5.9), [])
        XCTAssertEqual(p.advance(6.0), [.started(t: 6.0, play: play(2.0, 1))])
    }

    func testStaleMealGivesWayToNewer() {
        let p = player(20)
        _ = p.submit(play(0.0, 0))
        _ = p.submit(play(1.0, 1))
        _ = p.submit(play(2.0, 2))

        XCTAssertEqual(p.advance(20.0), [.skipped(t: 20.0, play: play(1.0, 1)), .started(t: 20.0, play: play(2.0, 2))])
    }

    func testLastMealAlwaysPlays() {
        let p = player(20)
        _ = p.submit(play(0.0, 0))
        _ = p.submit(play(1.0, 1))

        XCTAssertEqual(p.advance(20.0), [.started(t: 20.0, play: play(1.0, 1))])
    }
}
