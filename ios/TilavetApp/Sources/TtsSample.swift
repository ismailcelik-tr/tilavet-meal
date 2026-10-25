import AVFoundation
import Foundation
import QuartzCore
import TilavetCore

/// `--tts-sample`: on-device Turkish TTS of the scripts/package_options.py samples, with time to first audio.
enum TtsSample {
    static let resultName = "tts.json"
    private static let language = "tr-TR"
    // Same units as SAMPLES in scripts/package_options.py.
    private static let samples = [(1, 2), (112, 1), (12, 11), (2, 255), (2, 282)]

    enum Failure: Error {
        case noVoice
    }

    /// `voiceName` picks the best installed quality of that voice (e.g. "Cem"); nil is the language default.
    static func run(voiceName: String?) async throws {
        try? FileManager.default.removeItem(at: Assets.documents.appendingPathComponent(resultName))
        let units = mealUnits(try parseTanzil(String(contentsOf: Assets.meal, encoding: .utf8)))
        guard let voice = pick(voiceName) else {
            throw Failure.noVoice
        }
        let prefix = voiceName.map { "tts-\($0.lowercased())" } ?? "tts"

        let synthesizer = AVSpeechSynthesizer()
        var results: [[String: Any]] = []
        for (sura, first) in samples {
            guard let unit = units.first(where: { $0.sura == sura && $0.first == first }) else {
                continue
            }

            let name = "\(prefix)-\(sura)-\(first).caf"
            let utterance = AVSpeechUtterance(string: unit.text)
            utterance.voice = voice
            let writer = Writer(Assets.documents.appendingPathComponent(name))
            try await writer.run(synthesizer, utterance)
            results.append(["file": name, "first_audio_s": writer.firstAudioS ?? -1, "synthesis_s": writer.totalS,
                            "audio_s": writer.audioS, "empty_buffers": writer.emptyBuffers])
        }

        let voices = AVSpeechSynthesisVoice.speechVoices().filter { $0.language == language }
            .map { ["name": $0.name, "identifier": $0.identifier, "quality": $0.quality.rawValue] }
        let result: [String: Any] = ["voice": voice.identifier, "voices": voices, "units": results]
        try Assets.publish(JSONSerialization.data(withJSONObject: result), as: resultName)
    }

    private static func pick(_ name: String?) -> AVSpeechSynthesisVoice? {
        guard let name else {
            return AVSpeechSynthesisVoice(language: language)
        }
        return AVSpeechSynthesisVoice.speechVoices()
            .filter { $0.language == language && $0.name.hasPrefix(name) }
            .max { $0.quality.rawValue < $1.quality.rawValue }
    }

    /// Writes one utterance to a file. The synthesizer also sends empty buffers mid-utterance, so the end is
    /// the delegate's didFinish.
    private final class Writer: NSObject, AVSpeechSynthesizerDelegate {
        private let url: URL
        private var file: AVAudioFile?
        private var frames: AVAudioFramePosition = 0
        private var sampleRate = 0.0
        private var start = 0.0
        private var error: Error?
        private var continuation: CheckedContinuation<Void, Error>?
        private(set) var firstAudioS: Double?
        private(set) var totalS = 0.0
        private(set) var emptyBuffers = 0

        var audioS: Double {
            sampleRate > 0 ? Double(frames) / sampleRate : 0
        }

        init(_ url: URL) {
            self.url = url
        }

        func run(_ synthesizer: AVSpeechSynthesizer, _ utterance: AVSpeechUtterance) async throws {
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                self.continuation = continuation
                synthesizer.delegate = self
                start = CACurrentMediaTime()
                synthesizer.write(utterance) { [self] buffer in
                    guard error == nil, let pcm = buffer as? AVAudioPCMBuffer else {
                        return
                    }

                    if pcm.frameLength == 0 {
                        emptyBuffers += 1
                        return
                    }

                    do {
                        try append(pcm)
                    } catch {
                        self.error = error
                    }
                }
            }
        }

        func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
            totalS = CACurrentMediaTime() - start
            file = nil
            if let error {
                continuation?.resume(throwing: error)
            } else {
                continuation?.resume()
            }
            continuation = nil
        }

        private func append(_ pcm: AVAudioPCMBuffer) throws {
            firstAudioS = firstAudioS ?? CACurrentMediaTime() - start
            if file == nil {
                file = try AVAudioFile(forWriting: url, settings: pcm.format.settings,
                                       commonFormat: pcm.format.commonFormat, interleaved: pcm.format.isInterleaved)
                sampleRate = pcm.format.sampleRate
            }
            try file?.write(from: pcm)
            frames += AVAudioFramePosition(pcm.frameLength)
        }
    }
}
