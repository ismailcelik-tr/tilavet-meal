import SwiftUI

struct ContentView: View {
    @State private var status = "Hazır"

    var body: some View {
        VStack(spacing: 16) {
            Text("Tilavet Meal").font(.title)
            Text(status).foregroundStyle(.secondary)
        }
        .padding()
        .task {
            guard LaunchArgs.has("--asr-parity") else {
                return
            }
            status = "ASR karşılaştırması sürüyor"
            let threads = (LaunchArgs.value("--threads") ?? "1,2,4").split(separator: ",").compactMap { Int($0) }
            do {
                try await Task.detached { try Parity.run(threads: threads) }.value
                status = "ASR karşılaştırması bitti"
            } catch {
                status = "Hata: \(error)"
            }
        }
    }
}
