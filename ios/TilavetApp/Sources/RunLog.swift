import Foundation
import TilavetCore

/// Documents/<run>/{mic.f32, live.jsonl, metrics.jsonl}; written as it happens, never only in memory (M5 lesson).
final class RunLog {
    let folder: URL
    private let mic: FileHandle
    private let live: FileHandle
    private let metrics: FileHandle
    private let start: Double

    init(name: String, start: Double) throws {
        folder = Assets.documents.appendingPathComponent(name)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        for file in ["mic.f32", "live.jsonl", "metrics.jsonl"] {
            FileManager.default.createFile(atPath: folder.appendingPathComponent(file).path, contents: nil)
        }
        mic = try FileHandle(forWritingTo: folder.appendingPathComponent("mic.f32"))
        live = try FileHandle(forWritingTo: folder.appendingPathComponent("live.jsonl"))
        metrics = try FileHandle(forWritingTo: folder.appendingPathComponent("metrics.jsonl"))
        self.start = start
        try Assets.publish(Data(name.utf8), as: "latest.txt")
    }

    func samples(_ chunk: [Float]) {
        chunk.withUnsafeBytes { mic.write(Data($0)) }
    }

    func record(_ record: Record, computeS: Double?) {
        switch record {
        case let .window(w):
            write(live, ["type": "Window", "heard_s": w.heardS, "t": w.t, "text": w.text, "skipped": w.skipped,
                         "compute_s": computeS ?? 0])
        case let .event(.confirmed(t, ref, mode, score)):
            write(live, ["type": "AyahConfirmed", "t": t, "ref": [ref.sura, ref.aya], "mode": mode.rawValue,
                         "score": score])
        case let .event(.lost(t)):
            write(live, ["type": "Lost", "t": t])
        case let .play(p):
            write(live, ["type": "Play", "t": p.t, "unit": unit(p.unit), "trigger": [p.trigger.sura, p.trigger.aya]])
        case let .player(.started(t, p)):
            write(live, ["type": "Started", "t": t, "unit": unit(p.unit)])
        case let .player(.skipped(t, p)):
            write(live, ["type": "Skipped", "t": t, "unit": unit(p.unit)])
        }
    }

    func playback(_ unit: MealUnit, at wall: Double) {
        write(live, ["type": "Playback", "unit": [unit.sura, unit.first], "wall_s": wall - start])
    }

    func metric(_ values: [String: Any]) {
        write(metrics, values)
    }

    func finish() {
        try? mic.close()
        try? live.close()
        try? metrics.close()
        FileManager.default.createFile(atPath: folder.appendingPathComponent("done").path, contents: nil)
    }

    private func unit(_ u: MealUnit) -> [Int] {
        [u.sura, u.first, u.last]
    }

    private func write(_ handle: FileHandle, _ object: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: object) else {
            return
        }
        handle.write(data + Data("\n".utf8))
    }
}
