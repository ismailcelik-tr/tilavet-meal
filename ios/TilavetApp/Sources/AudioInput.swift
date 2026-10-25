import AVFoundation
import QuartzCore

/// iPhone microphone -> 16 kHz mono Float32 chunks stamped with capture time; headphones stay on A2DP.
final class AudioInput {
    private let engine = AVAudioEngine()
    private let target = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: 16_000, channels: 1,
                                       interleaved: false)!
    private static let tapFrames: AVAudioFrameCount = 4_800

    func start(onChunk: @escaping ([Float], Double) -> Void) throws {
        try AudioRoute.activate()

        let input = engine.inputNode
        let source = input.outputFormat(forBus: 0)
        guard let converter = AVAudioConverter(from: source, to: target) else {
            throw NSError(domain: "AudioInput", code: 1, userInfo: [NSLocalizedDescriptionKey: "no converter"])
        }

        let ratio = target.sampleRate / source.sampleRate
        input.installTap(onBus: 0, bufferSize: Self.tapFrames, format: source) { [target] buffer, _ in
            let capturedAt = CACurrentMediaTime()
            let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio) + 32
            guard let out = AVAudioPCMBuffer(pcmFormat: target, frameCapacity: capacity) else {
                return
            }

            var consumed = false
            var error: NSError?
            converter.convert(to: out, error: &error) { _, status in
                if consumed {
                    status.pointee = .noDataNow
                    return nil
                }
                consumed = true
                status.pointee = .haveData
                return buffer
            }
            onChunk(Array(UnsafeBufferPointer(start: out.floatChannelData![0], count: Int(out.frameLength))),
                    capturedAt)
        }

        engine.prepare()
        try engine.start()
    }

    func stop() {
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
    }
}
