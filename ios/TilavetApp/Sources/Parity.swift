import AVFoundation
import Foundation
import QuartzCore

/// `--asr-parity`: transcribe the bundled clips per thread count; scripts/asr_parity.py compares with Python.
enum Parity {
    static let resultName = "parity.json"

    static func run(threads: [Int]) throws {
        try? FileManager.default.removeItem(at: Assets.documents.appendingPathComponent(resultName))
        let clips = try FileManager.default.contentsOfDirectory(at: Assets.parity, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "wav" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        var results: [[String: Any]] = []

        for count in threads {
            print("parity: loading recognizer, threads \(count)")
            let recognizer = try TinyRecognizer(threads: count)
            print("parity: loaded")
            for clip in clips {
                let samples = try readFloat32(clip)
                let start = CACurrentMediaTime()
                let text = recognizer.transcribe(samples)
                print("parity: \(clip.lastPathComponent) \(CACurrentMediaTime() - start) s")
                results.append(["threads": count, "clip": clip.lastPathComponent, "text": text,
                                "seconds": CACurrentMediaTime() - start, "audio_s": Double(samples.count) / 16_000])
            }
        }

        try Assets.publish(JSONSerialization.data(withJSONObject: results), as: resultName)
    }

    static func readFloat32(_ url: URL) throws -> [Float] {
        let file = try AVAudioFile(forReading: url, commonFormat: .pcmFormatFloat32, interleaved: false)
        let buffer = AVAudioPCMBuffer(pcmFormat: file.processingFormat, frameCapacity: AVAudioFrameCount(file.length))!
        try file.read(into: buffer)
        return Array(UnsafeBufferPointer(start: buffer.floatChannelData![0], count: Int(buffer.frameLength)))
    }
}
