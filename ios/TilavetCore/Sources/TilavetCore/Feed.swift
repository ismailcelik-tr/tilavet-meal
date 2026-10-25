import Foundation

/// A meal that started playing. The text is not stored: it is read from the verified translation when shown.
public struct FeedEntry: Codable, Equatable, Sendable {
    public let sura: Int
    public let first: Int
    public let last: Int
    public let startedAt: Date

    public init(sura: Int, first: Int, last: Int, startedAt: Date) {
        self.sura = sura
        self.first = first
        self.last = last
        self.startedAt = startedAt
    }
}

/// Meals heard in order; `id` is the creation time.
public struct Feed: Codable, Equatable, Identifiable, Sendable {
    public let id: Date
    public var entries: [FeedEntry]

    public init(id: Date, entries: [FeedEntry] = []) {
        self.id = id
        self.entries = entries
    }
}

/// "Yûsuf → Bakara · 23 meal": first and last sura, then the count.
public func feedSummary(_ feed: Feed) -> String {
    guard let first = feed.entries.first, let last = feed.entries.last else {
        return "Boş"
    }

    let count = "\(feed.entries.count) meal"
    if first.sura == last.sura {
        return "\(suraNames[first.sura - 1]) · \(count)"
    }
    return "\(suraNames[first.sura - 1]) → \(suraNames[last.sura - 1]) · \(count)"
}
