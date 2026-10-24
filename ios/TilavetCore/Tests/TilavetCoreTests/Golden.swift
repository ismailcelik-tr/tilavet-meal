import Foundation
import XCTest

@testable import TilavetCore

/// Data the Python side exported (scripts/export_golden.py); tests skip without it.
enum Golden {
    static let root = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent()
    static let goldenDir = root.appendingPathComponent("data/derived/m6/golden")
    static let quranFile = root.appendingPathComponent("data/raw/quran-simple-clean.txt")

    static func json(_ name: String) throws -> Any {
        let url = goldenDir.appendingPathComponent("\(name).json")
        guard FileManager.default.fileExists(atPath: url.path) else {
            throw XCTSkip("run scripts/export_golden.py first")
        }
        return try JSONSerialization.jsonObject(with: Data(contentsOf: url))
    }

    nonisolated(unsafe) private static var cachedIndex: QuranIndex?

    static func index() throws -> QuranIndex {
        if let cachedIndex {
            return cachedIndex
        }
        guard FileManager.default.fileExists(atPath: quranFile.path) else {
            throw XCTSkip("run scripts/fetch_data.py first")
        }
        let quran = try parseTanzil(String(contentsOf: quranFile, encoding: .utf8))
        let index = QuranIndex.build(
            Dictionary(uniqueKeysWithValues: quran.map { ($0.key, words(normalize(stripBasmala($0.key, $0.value)))) }))
        cachedIndex = index
        return index
    }
}
