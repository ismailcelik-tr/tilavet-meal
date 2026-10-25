import Foundation
import QuartzCore
import TilavetCore
import UIKit

/// Microphone -> LiveSession -> meal audio, everything logged. One serial queue does the work; the UI only reads.
@MainActor
final class Pipeline: ObservableObject {
    @Published private(set) var status = "Hazır"
    /// Shown under the status while the engine searches for a long time.
    @Published private(set) var hint: String?
    @Published private(set) var running = false
    /// Meals play only when on: headphones if connected, else the loudspeaker. Off by default without headphones.
    @Published private(set) var soundOn = AudioRoute.headphonesConnected()
    /// Where meals go when the sound is on: the headphone name, or nil for the loudspeaker.
    @Published private(set) var headphoneName = AudioRoute.headphoneName()

    nonisolated private static let hopS = 1.0
    nonisolated private static let windowS = 12.0
    nonisolated private static let cooldownS = 300.0
    nonisolated private static let maxWaitS = 15.0
    nonisolated private static let metricsS = 5.0
    private static let replayWithinS = 30.0
    private static let hintAfterS = 10.0
    private static let searchHint = "Kısa ve sık geçen ifadelerde âyet hemen bulunamayabilir; okumaya devam edin."

    private var trackedSura: Int?
    private var searchingSince: Date?

    private let worker = Worker()
    private var onMeal: ((MealUnit) -> Void)?
    private var routeObserver: NSObjectProtocol?

    init() {
        worker.setSound(soundOn, replayWithinS: nil)
        routeObserver = AudioRoute.observe { [weak self] change in
            self?.routeChanged(change)
        }
    }

    /// `onMeal` receives every meal that starts, whether or not it is heard.
    func start(threads: Int, durationS: Double?, onMeal: ((MealUnit) -> Void)?) {
        guard !running else {
            return
        }
        running = true
        status = "Yükleniyor"
        trackedSura = nil
        searchingSince = nil
        hint = nil
        UIDevice.current.isBatteryMonitoringEnabled = true
        self.onMeal = onMeal

        worker.start(threads: threads) { [weak self] update in
            Task { @MainActor in
                self?.apply(update)
            }
        }
        if let durationS {
            Task { @MainActor in
                try? await Task.sleep(for: .seconds(durationS))
                self.stop()
            }
        }
    }

    func stop() {
        guard running else {
            return
        }
        running = false
        status = "Durduruldu"
        hint = nil
        worker.stop()
    }

    /// Off stops the playing meal; on restarts the last one if it played within the last 30 s.
    func setSound(_ on: Bool) {
        soundOn = on
        worker.setSound(on, replayWithinS: Pipeline.replayWithinS)
        worker.note("Sound", ["on": on, "outputs": AudioRoute.outputs()])
    }

    /// Plays a meal from the feed; false when the sound is off.
    func replay(_ unit: MealUnit) -> Bool {
        guard soundOn else {
            return false
        }
        worker.replay(unit)
        return true
    }

    /// Headphones arriving turn the sound on; leaving turns it off (no surprise loudspeaker).
    private func routeChanged(_ change: AudioRoute.Change) {
        headphoneName = AudioRoute.headphoneName()
        switch change {
        case .headphonesAdded:
            setSound(true)
        case .headphonesRemoved:
            setSound(false)
        case let .other(reason):
            worker.note("Route", ["reason": reason, "outputs": AudioRoute.outputs()])
        }
    }

    private func apply(_ update: Worker.Update) {
        switch update {
        case .listening:
            status = "Ses bekleniyor"
        case let .heard(speech):
            showSearch(speech: speech)
        case let .confirmed(sura):
            trackedSura = sura
            searchingSince = nil
            hint = nil
            status = "Takip ediliyor · \(suraNames[sura - 1]) Sûresi"
        case .lost:
            trackedSura = nil
            status = "Takip kaybedildi · âyet aranıyor"
        case let .meal(unit):
            onMeal?(unit)
        case let .failed(message):
            status = "Hata: \(message)"
            running = false
        }
    }

    /// Without a tracked position: tell apart silence from speech the engine cannot place yet.
    private func showSearch(speech: Bool) {
        guard trackedSura == nil else {
            return
        }
        guard speech else {
            status = "Ses bekleniyor"
            searchingSince = nil
            hint = nil
            return
        }

        status = "Okuma duyuluyor · âyet aranıyor"
        let since = searchingSince ?? Date()
        searchingSince = since
        hint = Date().timeIntervalSince(since) >= Pipeline.hintAfterS ? Pipeline.searchHint : nil
    }

    /// Off the main actor: audio callbacks, ASR and file writes.
    private final class Worker: @unchecked Sendable {
        enum Update {
            case listening, lost
            /// Per window: did it contain speech (at least `speechWords` words)?
            case heard(Bool)
            case confirmed(Int)
            case meal(MealUnit)
            case failed(String)
        }

        private static let speechWords = 2

        private let queue = DispatchQueue(label: "pipeline", qos: .userInitiated)
        private let lock = NSLock()
        private var pending: [([Float], Double)] = []
        private var input: AudioInput?
        private var session: LiveSession?
        private var recognizer: TimedRecognizer?
        private var log: RunLog?
        private var metrics: DispatchSourceTimer?
        private let output = MealOutput()
        private var soundOn = false
        private var sessionActive = false
        private var notify: (Update) -> Void = { _ in }

        func start(threads: Int, notify: @escaping (Update) -> Void) {
            self.notify = notify
            queue.async { [weak self] in
                guard let self else {
                    return
                }
                do {
                    try self.load(threads: threads)
                    let input = AudioInput()
                    try input.start { [weak self] samples, capturedAt in
                        self?.enqueue(samples, capturedAt)
                    }
                    self.input = input
                    self.sessionActive = true
                    self.startMetrics()
                    self.log?.note("Start", ["sound": self.soundOn, "outputs": AudioRoute.outputs()],
                                   at: CACurrentMediaTime())
                    notify(.listening)
                } catch {
                    notify(.failed("\(error)"))
                }
            }
        }

        /// `replayWithinS` nil: only set the flag (launch).
        func setSound(_ on: Bool, replayWithinS: Double?) {
            queue.async {
                self.soundOn = on
                guard let replayWithinS else {
                    return
                }
                if on {
                    self.output.replayRecent(withinS: replayWithinS)
                } else {
                    self.output.stop()
                }
            }
        }

        func note(_ type: String, _ fields: [String: Any]) {
            let wall = CACurrentMediaTime()
            nonisolated(unsafe) let fields = fields
            queue.async {
                self.log?.note(type, fields, at: wall)
            }
        }

        func replay(_ unit: MealUnit) {
            queue.async {
                if !self.sessionActive {
                    try? AudioRoute.activate()
                    self.sessionActive = true
                }
                self.output.play(unit)
            }
        }

        func stop() {
            input?.stop()
            metrics?.cancel()
            queue.async {
                self.drain()
                self.log?.finish()
                self.log = nil
                self.session = nil
            }
        }

        private func load(threads: Int) throws {
            let quran = try parseTanzil(String(contentsOf: Assets.quran, encoding: .utf8))
            let index = QuranIndex.recited(quran)
            let units = mealUnits(try parseTanzil(String(contentsOf: Assets.meal, encoding: .utf8)))
            let durations = try loadDurations()
            let recognizer = TimedRecognizer(try TinyRecognizer(threads: threads))
            let player = MealPlayer(durationS: { durations["\($0.sura)-\($0.first)"] ?? 0 }, maxWaitS: Pipeline.maxWaitS)

            self.recognizer = recognizer
            session = LiveSession(recognizer: recognizer, engine: PositionEngine(index),
                                  policy: EmissionPolicy(units, cooldownS: Pipeline.cooldownS), player: player,
                                  clock: CACurrentMediaTime, hopS: Pipeline.hopS, windowS: Pipeline.windowS)
            let start = CACurrentMediaTime()
            let name = ISO8601DateFormatter.string(from: Date(), timeZone: .current,
                                                   formatOptions: [.withYear, .withMonth, .withDay, .withTime])
            log = try RunLog(name: name, start: start)
        }

        private func loadDurations() throws -> [String: Double] {
            var result: [String: Double] = [:]
            // The CSV has CRLF endings; Swift reads "\r\n" as one Character, so split on any newline.
            let lines = try String(contentsOf: Assets.durations, encoding: .utf8).split(whereSeparator: \.isNewline)
            let header = lines[0].split(separator: ",").map(String.init)
            let sura = header.firstIndex(of: "sura")!, first = header.firstIndex(of: "first")!
            let seconds = header.firstIndex(of: "seconds")!
            for line in lines.dropFirst() {
                let fields = line.split(separator: ",", omittingEmptySubsequences: false).map(String.init)
                result["\(fields[sura])-\(fields[first])"] = Double(fields[seconds])
            }
            return result
        }

        private func enqueue(_ samples: [Float], _ capturedAt: Double) {
            lock.lock()
            pending.append((samples, capturedAt))
            lock.unlock()
            queue.async { self.drain() }
        }

        /// Feed everything pending at once: a late ASR skips to the newest window (scripts/live.py `_pump`).
        private func drain() {
            lock.lock()
            let batch = pending
            pending.removeAll()
            lock.unlock()
            guard let session, let log, let last = batch.last else {
                return
            }

            let samples = batch.flatMap(\.0)
            log.samples(samples)
            for record in session.feed(samples, arrivedAt: last.1) {
                log.record(record, computeS: recognizer?.lastSeconds)
                switch record {
                case let .window(window):
                    notify(.heard(window.text.split(separator: " ").count >= Worker.speechWords))
                case let .event(.confirmed(_, ref, _, _)):
                    notify(.confirmed(ref.sura))
                case let .player(.started(_, play)):
                    if soundOn {
                        output.play(play.unit)
                        log.playback(play.unit, at: CACurrentMediaTime())
                    }
                    notify(.meal(play.unit))
                case .event(.lost):
                    notify(.lost)
                default:
                    break
                }
            }
        }

        private func startMetrics() {
            let timer = DispatchSource.makeTimerSource(queue: DispatchQueue(label: "metrics"))
            timer.schedule(deadline: .now(), repeating: Pipeline.metricsS)
            timer.setEventHandler { [weak self] in
                var values = Metrics.sample()
                values["t"] = CACurrentMediaTime()
                self?.log?.metric(values)
            }
            timer.resume()
            metrics = timer
        }
    }
}

/// Wall-clock seconds of the last transcription, logged with each window.
final class TimedRecognizer: Recognizer {
    private let inner: Recognizer
    private(set) var lastSeconds = 0.0

    init(_ inner: Recognizer) {
        self.inner = inner
    }

    func transcribe(_ samples: [Float]) -> String {
        let start = CACurrentMediaTime()
        let text = inner.transcribe(samples)
        lastSeconds = CACurrentMediaTime() - start
        return text
    }
}
