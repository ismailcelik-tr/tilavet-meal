/// Live pipeline over microphone chunks: window -> ASR -> engine -> policy -> player. Pure; time is passed in.
public let sampleRate = 16_000

public protocol Recognizer {
    func transcribe(_ samples: [Float]) -> String
}

public protocol Engine {
    func feed(_ t: Double, _ words: [String]) -> [Event]
}

extension PositionEngine: Engine {}

public struct Window: Equatable, Sendable {
    public let heardS: Double  // audio heard when the window closed
    public let t: Double  // decision time: heardS + queueing + compute
    public let text: String
    public let skipped: Int  // hops dropped because ASR fell behind
}

public enum Record: Equatable, Sendable {
    case window(Window)
    case event(Event)
    case play(Play)
    case player(PlayerEvent)
}

public final class LiveSession {
    private let recognizer: Recognizer
    private let engine: Engine
    private let policy: EmissionPolicy
    private let player: MealPlayer
    private let clock: () -> Double
    private let hop: Int
    private let window: Int
    private var buffer: [Float] = []
    private var heard = 0
    private var nextHop: Int

    public init(recognizer: Recognizer, engine: Engine, policy: EmissionPolicy, player: MealPlayer,
                clock: @escaping () -> Double, hopS: Double, windowS: Double) {
        self.recognizer = recognizer
        self.engine = engine
        self.policy = policy
        self.player = player
        self.clock = clock
        hop = Int((hopS * Double(sampleRate)).rounded())
        window = Int((windowS * Double(sampleRate)).rounded())
        nextHop = hop
    }

    /// `arrivedAt`: clock time when the last of `samples` was captured.
    public func feed(_ samples: [Float], arrivedAt: Double) -> [Record] {
        buffer.append(contentsOf: samples)
        if buffer.count > window {
            buffer.removeFirst(buffer.count - window)
        }
        heard += samples.count
        if heard < nextHop {
            return []
        }

        let hops = (heard - nextHop) / hop + 1
        nextHop += hops * hop
        let heardS = Double(heard) / Double(sampleRate)

        let text = recognizer.transcribe(buffer)
        let t = heardS + clock() - arrivedAt
        var records: [Record] = [.window(Window(heardS: heardS, t: t, text: text, skipped: hops - 1))]

        for event in engine.feed(t, words(normalize(text))) {
            records.append(.event(event))
            guard let play = policy.on(event) else {
                continue
            }
            records.append(.play(play))
            records.append(contentsOf: player.submit(play).map(Record.player))
        }

        records.append(contentsOf: player.advance(t).map(Record.player))
        return records
    }
}
