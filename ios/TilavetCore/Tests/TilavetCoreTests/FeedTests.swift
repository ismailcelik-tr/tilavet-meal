import XCTest

@testable import TilavetCore

final class FeedTests: XCTestCase {
    private let start = Date(timeIntervalSinceReferenceDate: 783_000_000.25)

    private func entry(_ sura: Int, _ first: Int, _ last: Int) -> FeedEntry {
        FeedEntry(sura: sura, first: first, last: last, startedAt: start.addingTimeInterval(Double(first)))
    }

    func testJSONRoundTrip() throws {
        let feed = Feed(id: start, entries: [entry(12, 11, 12), entry(12, 13, 13)])

        let decoded = try JSONDecoder().decode(Feed.self, from: JSONEncoder().encode(feed))

        XCTAssertEqual(decoded, feed)
    }

    func testSummary() {
        XCTAssertEqual(feedSummary(Feed(id: start, entries: [])), "Boş")
        XCTAssertEqual(feedSummary(Feed(id: start, entries: [entry(12, 3, 3), entry(12, 4, 4)])), "Yûsuf · 2 meal")
        XCTAssertEqual(feedSummary(Feed(id: start, entries: [entry(12, 3, 3), entry(2, 25, 25), entry(2, 26, 27)])),
                       "Yûsuf → Bakara · 3 meal")
    }
}
