import AVFoundation
import QuartzCore
import TilavetCore

/// Plays pre-rendered meal audio; one player at a time (MealPlayer already prevents overlap).
final class MealOutput {
    private var player: AVAudioPlayer?
    private var unit: MealUnit?
    private var startedAt = 0.0

    func play(_ unit: MealUnit) {
        let url = Assets.meals.appendingPathComponent("\(unit.sura)-\(unit.first).m4a")
        player = try? AVAudioPlayer(contentsOf: url)
        player?.play()
        self.unit = unit
        startedAt = CACurrentMediaTime()
    }

    func stop() {
        player?.stop()
    }

    /// Restarts the last meal if it is still playing or ended less than `withinS` ago.
    func replayRecent(withinS: Double) {
        guard let unit, let player else {
            return
        }

        let endedAgo = CACurrentMediaTime() - startedAt - player.duration
        if player.isPlaying || endedAgo < withinS {
            play(unit)
        }
    }
}
