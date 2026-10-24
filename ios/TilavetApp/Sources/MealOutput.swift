import AVFoundation
import TilavetCore

/// Plays pre-rendered meal audio; one player at a time (MealPlayer already prevents overlap).
final class MealOutput {
    private var player: AVAudioPlayer?

    func play(_ unit: MealUnit) {
        let url = Assets.meals.appendingPathComponent("\(unit.sura)-\(unit.first).m4a")
        player = try? AVAudioPlayer(contentsOf: url)
        player?.play()
    }
}
