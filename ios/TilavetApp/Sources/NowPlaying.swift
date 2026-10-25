import MediaPlayer
import TilavetCore

/// Lock screen and Control Center: the current meal's title; play and pause start and stop listening.
@MainActor
final class NowPlaying {
    private static let artist = "Tilavet Meal"

    init(play: @escaping @MainActor () -> Void, pause: @escaping @MainActor () -> Void,
         toggle: @escaping @MainActor () -> Void) {
        let center = MPRemoteCommandCenter.shared()
        Self.bind(center.playCommand, play)
        Self.bind(center.pauseCommand, pause)
        Self.bind(center.togglePlayPauseCommand, toggle)
    }

    func show(_ unit: MealUnit) {
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [
            MPMediaItemPropertyTitle: mealTitle(sura: unit.sura, first: unit.first, last: unit.last),
            MPMediaItemPropertyArtist: Self.artist,
        ]
    }

    private static func bind(_ command: MPRemoteCommand, _ action: @escaping @MainActor () -> Void) {
        command.addTarget { _ in
            Task { @MainActor in
                action()
            }
            return .success
        }
    }
}
