import Foundation
import TilavetCore

/// The active feed and past feeds, one JSON file each in Documents/feeds; active.txt names the active one.
@MainActor
final class FeedStore: ObservableObject {
    @Published private(set) var active: Feed
    /// Newest first, without the active feed.
    @Published private(set) var history: [Feed]

    private static let folder = Assets.documents.appendingPathComponent("feeds")
    private static let pointer = folder.appendingPathComponent("active.txt")

    init() {
        try? FileManager.default.createDirectory(at: Self.folder, withIntermediateDirectories: true)
        let feeds = Self.loadAll()
        let activeName = try? String(contentsOf: Self.pointer, encoding: .utf8)
        let current = feeds.first { Self.fileName($0) == activeName } ?? Feed(id: Date())

        active = current
        history = feeds.filter { $0.id != current.id }
        Self.save(current)
    }

    func append(_ unit: MealUnit, at date: Date = Date()) {
        active.entries.append(FeedEntry(sura: unit.sura, first: unit.first, last: unit.last, startedAt: date))
        Self.save(active)
    }

    /// Keeps the active feed in history and opens an empty one; nothing happens if the active feed is empty.
    func startNew() {
        guard !active.entries.isEmpty else {
            return
        }
        history.insert(active, at: 0)
        active = Feed(id: Date())
        Self.save(active)
    }

    /// Deleting the active feed opens an empty one.
    func delete(_ feed: Feed) {
        try? FileManager.default.removeItem(at: Self.url(feed))
        if feed.id == active.id {
            active = Feed(id: Date())
            Self.save(active)
            return
        }
        history.removeAll { $0.id == feed.id }
    }

    private static func fileName(_ feed: Feed) -> String {
        "\(Int(feed.id.timeIntervalSince1970)).json"
    }

    private static func url(_ feed: Feed) -> URL {
        folder.appendingPathComponent(fileName(feed))
    }

    private static func save(_ feed: Feed) {
        guard let data = try? JSONEncoder().encode(feed) else {
            return
        }
        try? data.write(to: url(feed), options: .atomic)
        try? Data(fileName(feed).utf8).write(to: pointer, options: .atomic)
    }

    private static func loadAll() -> [Feed] {
        let files = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
        return files.filter { $0.pathExtension == "json" }
            .compactMap { try? JSONDecoder().decode(Feed.self, from: Data(contentsOf: $0)) }
            .sorted { $0.id > $1.id }
    }
}
