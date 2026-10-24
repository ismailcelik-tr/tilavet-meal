/// Meal playback queue: one meal at a time, never cut mid-sentence. Pure; time is passed in.
public enum PlayerEvent: Equatable, Sendable {
    case started(t: Double, play: Play)
    case skipped(t: Double, play: Play)
}

public final class MealPlayer {
    private let durationS: (MealUnit) -> Double
    private let maxWaitS: Double
    private var queue: [Play] = []
    private var freeAt = -Double.infinity

    public init(durationS: @escaping (MealUnit) -> Double, maxWaitS: Double) {
        self.durationS = durationS
        self.maxWaitS = maxWaitS
    }

    public func submit(_ play: Play) -> [PlayerEvent] {
        // Settle earlier meals first: whether a newer one exists is judged at their start time.
        let events = advance(play.t)
        queue.append(play)
        return events + advance(play.t)
    }

    public func advance(_ now: Double) -> [PlayerEvent] {
        var events: [PlayerEvent] = []
        while let play = queue.first {
            let start = max(freeAt, play.t)
            if start > now {
                break
            }

            queue.removeFirst()
            if !queue.isEmpty && start - play.t > maxWaitS {
                events.append(.skipped(t: start, play: play))
                continue
            }

            events.append(.started(t: start, play: play))
            freeAt = start + durationS(play.unit)
        }
        return events
    }
}
