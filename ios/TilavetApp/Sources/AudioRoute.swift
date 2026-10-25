import AVFoundation

/// The shared audio session: iPhone microphone in, meals out to headphones or, without them, the loudspeaker.
enum AudioRoute {
    private static let headphonePorts: Set<AVAudioSession.Port> = [.bluetoothA2DP, .bluetoothHFP, .bluetoothLE,
                                                                     .headphones]

    static func activate() throws {
        let session = AVAudioSession.sharedInstance()
        // .allowBluetoothA2DP, never .allowBluetooth: HFP would pull the headphone to the low-quality call profile.
        // .defaultToSpeaker: without headphones play on the loudspeaker, not the earpiece.
        try session.setCategory(.playAndRecord, mode: .measurement, options: [.allowBluetoothA2DP, .defaultToSpeaker])
        try session.setActive(true)
        if let builtIn = session.availableInputs?.first(where: { $0.portType == .builtInMic }) {
            try session.setPreferredInput(builtIn)
        }
    }

    static func headphonesConnected() -> Bool {
        AVAudioSession.sharedInstance().currentRoute.outputs.contains { headphonePorts.contains($0.portType) }
    }

    /// Calls `action` when headphones go away (unplugged, Bluetooth lost).
    static func observeRemoval(_ action: @escaping @MainActor () -> Void) -> NSObjectProtocol {
        NotificationCenter.default.addObserver(forName: AVAudioSession.routeChangeNotification, object: nil,
                                               queue: .main) { note in
            guard let raw = note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
                  AVAudioSession.RouteChangeReason(rawValue: raw) == .oldDeviceUnavailable else {
                return
            }
            MainActor.assumeIsolated {
                action()
            }
        }
    }
}
