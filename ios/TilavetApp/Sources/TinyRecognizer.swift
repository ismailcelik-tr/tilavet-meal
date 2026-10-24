import Foundation
import TilavetCore

/// quran-asr-tiny through sherpa-onnx; mirrors tilavet.asr.sherpa.QuranAsrTiny.
final class TinyRecognizer: Recognizer {
    private static let wordBoundary = "▁"
    private let recognizer: SherpaOnnxOfflineRecognizer
    private let spelling: [String: String]

    init(threads: Int) throws {
        let model = sherpaOnnxOfflineModelConfig(
            tokens: Assets.tokens.path, numThreads: threads,
            zipformerCtc: sherpaOnnxOfflineZipformerCtcModelConfig(model: Assets.model.path))
        var config = sherpaOnnxOfflineRecognizerConfig(featConfig: sherpaOnnxFeatureConfig(), modelConfig: model)
        recognizer = SherpaOnnxOfflineRecognizer(config: &config)
        spelling = try JSONDecoder().decode([String: String].self, from: Data(contentsOf: Assets.spelling))
    }

    func transcribe(_ samples: [Float]) -> String {
        let text = recognizer.decode(samples: samples, sampleRate: 16_000).text
        let words = text.replacingOccurrences(of: Self.wordBoundary, with: " ").split(separator: " ").map(String.init)
        return words.map { spelling[$0] ?? $0 }.joined(separator: " ")
    }
}
