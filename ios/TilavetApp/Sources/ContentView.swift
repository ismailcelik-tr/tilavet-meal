import SwiftUI
import TilavetCore

struct ContentView: View {
    @StateObject private var pipeline = Pipeline()
    @StateObject private var store = FeedStore()
    @State private var nowPlaying: NowPlaying?
    @State private var modeStatus: String?
    @State private var showHistory = false
    @State private var soundHint = false
    @AppStorage("keepAwake") private var keepAwake = false
    @AppStorage("textScale") private var textScale = 1.0

    private let defaultThreads = 2
    private static let scaleRange = 0.8...2.0
    private static let scaleStep = 0.15
    private static let hintS = 0.8

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                VStack(spacing: 4) {
                    Text(modeStatus ?? pipeline.status)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    if let hint = pipeline.hint {
                        Text(hint)
                            .font(.footnote)
                            .foregroundStyle(.orange)
                            .multilineTextAlignment(.center)
                    }
                    Label(outputText, systemImage: pipeline.soundOn ? "speaker.wave.2" : "speaker.slash")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal)

                FeedView(feed: store.active, scale: textScale, onTap: play)

                Toggle(isOn: $keepAwake) {
                    Label("Ekran açık kalsın", systemImage: "sun.max")
                }
                .toggleStyle(.button)

                Button(action: toggleRunning) {
                    Text(pipeline.running ? "Durdur" : "Başlat")
                        .font(.title2.bold())
                        .frame(maxWidth: .infinity, minHeight: 64)
                }
                .buttonStyle(.borderedProminent)
                .tint(pipeline.running ? .red : .green)
                .padding(.horizontal)
            }
            .padding(.bottom)
            .navigationTitle("Tilavet Meal")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItemGroup(placement: .topBarTrailing) {
                    toolbarButtons
                }
            }
            .sheet(isPresented: $showHistory) {
                HistoryView(store: store, scale: textScale, onTap: play)
            }
        }
        .onChange(of: keepAwake) {
            applyIdleTimer()
        }
        .onChange(of: pipeline.running) {
            applyIdleTimer()
        }
        .task {
            nowPlaying = NowPlaying(play: start, pause: pipeline.stop, toggle: toggleRunning)
            if LaunchArgs.has("--asr-parity") {
                await runParity()
                return
            }
            if LaunchArgs.has("--tts-sample") {
                await runTts()
                return
            }
            if LaunchArgs.has("--autostart") {
                startMeasurement()
            }
        }
    }

    @ViewBuilder
    private var toolbarButtons: some View {
        Button {
            showHistory = true
        } label: {
            Image(systemName: "clock.arrow.circlepath")
        }
        .accessibilityLabel("Geçmiş")

        Button {
            store.startNew()
        } label: {
            Image(systemName: "plus")
        }
        .accessibilityLabel("Yeni akış")

        Button {
            pipeline.setSound(!pipeline.soundOn)
        } label: {
            Image(systemName: pipeline.soundOn ? "speaker.wave.2.fill" : "speaker.slash")
                .foregroundStyle(soundHint ? Color.red : Color.accentColor)
        }
        .accessibilityLabel(pipeline.soundOn ? "Sesi kapat" : "Sesi aç")

        Button {
            textScale = max(Self.scaleRange.lowerBound, textScale - Self.scaleStep)
        } label: {
            Image(systemName: "textformat.size.smaller")
        }
        .disabled(textScale <= Self.scaleRange.lowerBound)
        .accessibilityLabel("Yazıyı küçült")

        Button {
            textScale = min(Self.scaleRange.upperBound, textScale + Self.scaleStep)
        } label: {
            Image(systemName: "textformat.size.larger")
        }
        .disabled(textScale >= Self.scaleRange.upperBound)
        .accessibilityLabel("Yazıyı büyüt")
    }

    /// Where meals go right now.
    private var outputText: String {
        guard pipeline.soundOn else {
            return "Ses kapalı"
        }
        return pipeline.headphoneName.map { "Kulaklık: \($0)" } ?? "Telefon hoparlörü"
    }

    private func toggleRunning() {
        if pipeline.running {
            pipeline.stop()
            return
        }
        start()
    }

    private func start() {
        pipeline.start(threads: defaultThreads, durationS: nil) { unit in
            store.append(unit)
            nowPlaying?.show(unit)
        }
    }

    /// Mac-driven runs: logged under Documents/<run>, never added to the feed.
    private func startMeasurement() {
        if LaunchArgs.has("--mute") {
            pipeline.setSound(false)
        }
        pipeline.start(threads: Int(LaunchArgs.value("--threads") ?? "") ?? defaultThreads,
                       durationS: Double(LaunchArgs.value("--duration") ?? ""), onMeal: nil)
    }

    private func play(_ unit: MealUnit) -> Bool {
        if pipeline.replay(unit) {
            return true
        }
        soundHint = true
        Task {
            try? await Task.sleep(for: .seconds(Self.hintS))
            soundHint = false
        }
        return false
    }

    private func applyIdleTimer() {
        UIApplication.shared.isIdleTimerDisabled = keepAwake && pipeline.running
    }

    private func runParity() async {
        modeStatus = "ASR karşılaştırması sürüyor"
        let threads = (LaunchArgs.value("--threads") ?? "1,2,4").split(separator: ",").compactMap { Int($0) }
        do {
            try await Task.detached { try Parity.run(threads: threads) }.value
            modeStatus = "ASR karşılaştırması bitti"
        } catch {
            modeStatus = "Hata: \(error)"
        }
    }

    private func runTts() async {
        modeStatus = "TTS örnekleri yazılıyor"
        do {
            try await TtsSample.run(voiceName: LaunchArgs.value("--voice"))
            modeStatus = "TTS örnekleri bitti"
        } catch {
            modeStatus = "Hata: \(error)"
        }
    }
}
