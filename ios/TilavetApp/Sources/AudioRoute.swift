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

    /// Name of the connected headphones, nil when meals would go to the loudspeaker.
    static func headphoneName() -> String? {
        AVAudioSession.sharedInstance().currentRoute.outputs.first { headphonePorts.contains($0.portType) }?.portName
    }

    /// Outputs of the current route, for the run log.
    static func outputs() -> [String] {
        AVAudioSession.sharedInstance().currentRoute.outputs.map { "\($0.portType.rawValue):\($0.portName)" }
    }

    /// Calls `action` with the change reason on every route change; `headphonesAdded` / `headphonesRemoved` mark
    /// a headphone arriving or leaving.
    static func observe(_ action: @escaping @MainActor (Change) -> Void) -> NSObjectProtocol {
        NotificationCenter.default.addObserver(forName: AVAudioSession.routeChangeNotification, object: nil,
                                               queue: .main) { note in
            let raw = note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt ?? 0
            let reason = AVAudioSession.RouteChangeReason(rawValue: raw) ?? .unknown
            let change: Change
            switch reason {
            case .newDeviceAvailable where headphonesConnected():
                change = .headphonesAdded
            case .oldDeviceUnavailable:
                change = .headphonesRemoved
            default:
                change = .other(raw)
            }
            MainActor.assumeIsolated {
                action(change)
            }
        }
    }

    enum Change {
        case headphonesAdded, headphonesRemoved
        case other(UInt)
    }
}
