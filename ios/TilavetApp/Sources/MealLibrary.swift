import Foundation
import TilavetCore

/// Meal units of the bundled translation, looked up by sura and first ayah.
final class MealLibrary: Sendable {
    static let shared = MealLibrary()

    private let units: [String: MealUnit]

    private init() {
        let text = (try? String(contentsOf: Assets.meal, encoding: .utf8)) ?? ""
        let all = (try? mealUnits(parseTanzil(text))) ?? []
        units = Dictionary(uniqueKeysWithValues: all.map { (Self.key($0.sura, $0.first), $0) })
    }

    func unit(_ entry: FeedEntry) -> MealUnit? {
        units[Self.key(entry.sura, entry.first)]
    }

    private static func key(_ sura: Int, _ first: Int) -> String {
        "\(sura)-\(first)"
    }
}
