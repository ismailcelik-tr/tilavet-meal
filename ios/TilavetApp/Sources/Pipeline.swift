import Foundation
import QuartzCore
import TilavetCore
import UIKit

/// Microphone -> LiveSession -> meal audio, everything logged. One serial queue does the work; the UI only reads.
@MainActor
final class Pipeline: ObservableObject {
    @Published private(set) var status = "Hazır"
    @Published private(set) var meal: MealUnit?
    @Published private(set) var running = false

    private static let hopS = 1.0
    private static let windowS = 12.0
    private static let cooldownS = 300.0
    private static let maxWaitS = 15.0
    private static let metricsS = 5.0

    private let worker = Worker()

    func start(threads: Int, mute: Bool, durationS: Double?) {
        guard !running else {
            return
        }
        running = true
        status = "Yükleniyor"
        UIDevice.current.isBatteryMonitoringEnabled = true

        worker.start(threads: threads, mute: mute) { [weak self] update in
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
        worker.stop()
    }

    private func apply(_ update: Worker.Update) {
        switch update {
        case .listening:
            status = "Dinliyor"
        case .lost:
            status = "Takip kaybedildi"
        case let .meal(unit):
            meal = unit
            status = "Dinliyor"
        case let .failed(message):
            status = "Hata: \(message)"
            running = false
        }
    }

    /// Off the main actor: audio callbacks, ASR and file writes.
    private final class Worker: @unchecked Sendable {
        enum Update {
            case listening, lost
            case meal(MealUnit)
            case failed(String)
        }

        private let queue = DispatchQueue(label: "pipeline", qos: .userInitiated)
        private let lock = NSLock()
        private var pending: [([Float], Double)] = []
        private var input: AudioInput?
        private var session: LiveSession?
        private var recognizer: TimedRecognizer?
        private var log: RunLog?
        private var metrics: DispatchSourceTimer?
        private let output = MealOutput()
        private var mute = false
        private var notify: (Update) -> Void = { _ in }

        func start(threads: Int, mute: Bool, notify: @escaping (Update) -> Void) {
            self.mute = mute
            self.notify = notify
            queue.async {
                do {
                    try self.load(threads: threads)
                    let input = AudioInput()
                    try input.start { [weak self] samples, capturedAt in
                        self?.enqueue(samples, capturedAt)
                    }
                    self.input = input
                    self.startMetrics()
                    notify(.listening)
                } catch {
                    notify(.failed("\(error)"))
                }
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
                case let .player(.started(_, play)):
                    if !mute {
                        output.play(play.unit)
                    }
                    log.playback(play.unit, at: CACurrentMediaTime())
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
