/// Which meal unit to play, and when. Early policy: on first confirmed ayah of a unit.
public struct Play: Equatable, Sendable {
    public let t: Double
    public let unit: MealUnit
    public let trigger: AyahRef
}

public final class EmissionPolicy {
    private let unitOf: [AyahRef: MealUnit]
    private let cooldownS: Double
    private var playedAt: [MealUnit: Double] = [:]

    public init(_ units: [MealUnit], cooldownS: Double) {
        unitOf = Dictionary(uniqueKeysWithValues: units.flatMap { unit in unit.refs.map { ($0, unit) } })
        self.cooldownS = cooldownS
    }

    public func on(_ event: Event) -> Play? {
        guard case let .confirmed(t, ref, _, _) = event, let unit = unitOf[ref] else {
            return nil
        }

        // Reciters repeat passages; replaying the same meal right away only adds backlog.
        if let played = playedAt[unit], t - played < cooldownS {
            return nil
        }

        playedAt[unit] = t
        return Play(t: t, unit: unit, trigger: ref)
    }
}
