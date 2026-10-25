import SwiftUI
import TilavetCore

struct ContentView: View {
    @StateObject private var pipeline = Pipeline()
    @State private var parityStatus: String?

    var body: some View {
        VStack(spacing: 24) {
            Text("Tilavet Meal").font(.title)
            Text(parityStatus ?? pipeline.status).foregroundStyle(.secondary)

            if let meal = pipeline.meal {
                VStack(spacing: 8) {
                    Text(span(meal)).font(.headline)
                    Text(meal.text).multilineTextAlignment(.center)
                    if meal.first != meal.last {
                        Text("(\(span(meal)) birbirine bağlı olduğu için birlikte çevrilmiştir.)")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()
            Button(pipeline.running ? "Durdur" : "Başlat") {
                // A tap is a person listening: never reuse measurement arguments such as --mute.
                pipeline.running ? pipeline.stop() : pipeline.start(threads: defaultThreads, mute: false, durationS: nil)
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .task {
            if LaunchArgs.has("--asr-parity") {
                await runParity()
                return
            }
            if LaunchArgs.has("--tts-sample") {
                await runTts()
                return
            }
            if LaunchArgs.has("--autostart") {
                start()
            }
        }
    }

    private let defaultThreads = 2

    private func start() {
        pipeline.start(threads: Int(LaunchArgs.value("--threads") ?? "") ?? defaultThreads,
                       mute: LaunchArgs.has("--mute"), durationS: Double(LaunchArgs.value("--duration") ?? ""))
    }

    private func span(_ unit: MealUnit) -> String {
        unit.first == unit.last ? "\(unit.sura):\(unit.first)" : "\(unit.sura):\(unit.first)-\(unit.last)"
    }

    private func runParity() async {
        parityStatus = "ASR karşılaştırması sürüyor"
        let threads = (LaunchArgs.value("--threads") ?? "1,2,4").split(separator: ",").compactMap { Int($0) }
        do {
            try await Task.detached { try Parity.run(threads: threads) }.value
            parityStatus = "ASR karşılaştırması bitti"
        } catch {
            parityStatus = "Hata: \(error)"
        }
    }

    private func runTts() async {
        parityStatus = "TTS örnekleri yazılıyor"
        do {
            try await TtsSample.run()
            parityStatus = "TTS örnekleri bitti"
        } catch {
            parityStatus = "Hata: \(error)"
        }
    }
}
