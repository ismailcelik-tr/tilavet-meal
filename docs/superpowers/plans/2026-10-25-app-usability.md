# iOS App Usability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the M6 measurement app into a daily-use app: persistent meal feed with history, Diyanet sura titles, one sound control, keep-awake, text size, lock screen info, app icon.

**Architecture:** Pure, tested pieces (sura names, titles, feed model, feed summary) go into `TilavetCore`. The app layer adds `FeedStore` (JSON files), `AudioRoute` (session + headphone detection), `NowPlaying`, and new SwiftUI views; `Pipeline` publishes started meals instead of one `meal` value and owns the sound state.

**Tech Stack:** Swift 6 package (`TilavetCore`, XCTest), SwiftUI iOS 18, AVFoundation, MediaPlayer, XcodeGen.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-10-25-app-usability-design.md`.
- Sura names verbatim from Diyanet `kuran_meal.pdf` headings, title-cased with Turkish rules; apostrophe `’`.
- Title: `"<Name> Sûresi, <a>. âyet"`; multi-ayah `"<Name> Sûresi, <a>-<b>. âyetler"`.
- Feed stores no meal text; text comes from `tr.diyanet.txt` at display time.
- Only `Started` meals enter the feed; measurement runs (`--autostart`) do not write the feed.
- Sound default: on if headphones connected at launch, else off; headphones removed → off; turning on replays the last meal only if it is playing or ended < 30 s ago.
- Keep-awake only while running; default off; persisted. Text scale 0.8–2.0, step 0.15, persisted.
- Engine, recognizer, meal audio and measurement modes (`--autostart`, `--mute`, `--asr-parity`, `--tts-sample`) keep working.
- Code style: user's CLAUDE.md (early return, `{}` always, constants, minimal `public`).

## File Structure

```
ios/TilavetCore/Sources/TilavetCore/
  SuraNames.swift      suraNames, mealTitle(sura:first:last:)
  Feed.swift           FeedEntry, Feed, feedSummary(_:)
ios/TilavetCore/Tests/TilavetCoreTests/
  SuraNamesTests.swift FeedTests.swift
ios/TilavetApp/Sources/
  AudioRoute.swift     activate(), headphonesConnected(), onHeadphonesRemoved
  MealOutput.swift     play, stop, replayRecent(withinS:)
  FeedStore.swift      active feed, history, append/startNew/delete, JSON files
  MealLibrary.swift    unit lookup by (sura, first)
  NowPlaying.swift     lock screen title + play/pause commands
  Pipeline.swift       sound state, replay, started-meal callback
  ContentView.swift    main screen
  FeedView.swift       scrolling cards, "Yeni meal ↓"
  HistoryView.swift    past feeds sheet
  Assets.xcassets/AppIcon.appiconset
scripts/draw_icon.swift  1024×1024 icon variants
```

---

### Task 1: Sura names and titles (TilavetCore, TDD)

**Files:** Create `SuraNames.swift`, `SuraNamesTests.swift`.

**Produces:** `public let suraNames: [String]` (114, index = sura − 1); `public func mealTitle(sura: Int, first: Int, last: Int) -> String`.

- [x] Write tests:

```swift
final class SuraNamesTests: XCTestCase {
    func testDiyanetSpelling() {
        XCTAssertEqual(suraNames.count, 114)
        XCTAssertEqual(suraNames[0], "Fâtiha")
        XCTAssertEqual(suraNames[2], "Âl-i İmrân")
        XCTAssertEqual(suraNames[22], "Mü’minûn")
        XCTAssertEqual(suraNames[32], "Ahzâb")
        XCTAssertEqual(suraNames[113], "Nâs")
    }

    func testTitle() {
        XCTAssertEqual(mealTitle(sura: 33, first: 40, last: 40), "Ahzâb Sûresi, 40. âyet")
        XCTAssertEqual(mealTitle(sura: 12, first: 11, last: 12), "Yûsuf Sûresi, 11-12. âyetler")
    }
}
```

- [x] `swift test --filter SuraNamesTests` → fails (no symbols). Implement with the 114 names extracted from the PDF. → passes. Commit `Add Diyanet sura names and meal titles`.

### Task 2: Feed model (TilavetCore, TDD)

**Files:** Create `Feed.swift`, `FeedTests.swift`.

**Produces:**
```swift
public struct FeedEntry: Codable, Equatable, Sendable { public let sura: Int; public let first: Int; public let last: Int; public let startedAt: Date }
public struct Feed: Codable, Equatable, Identifiable, Sendable { public let id: Date; public var entries: [FeedEntry] }
public func feedSummary(_ feed: Feed) -> String   // "Yûsuf → Bakara · 23 meal", "Yûsuf · 5 meal", "Boş"
```

- [x] Tests: JSON round trip with default `JSONEncoder`/`JSONDecoder` equals; summary for empty, one sura, two suras.
- [x] Fail → implement → pass. Commit `Add the meal feed model`.

### Task 3: Sound control and replay (app)

**Files:** Create `AudioRoute.swift`; modify `AudioInput.swift`, `MealOutput.swift`, `Pipeline.swift`.

- `AudioRoute.activate()`: `.playAndRecord`, `.measurement`, options `[.allowBluetoothA2DP, .defaultToSpeaker]` (speaker instead of earpiece without headphones), `setActive(true)`, built-in mic preferred. `AudioInput.start` calls it instead of configuring the session itself.
- `AudioRoute.headphonesConnected()`: current route outputs contain `.bluetoothA2DP`, `.bluetoothHFP`, `.bluetoothLE` or `.headphones`.
- `AudioRoute.observeRemoval(_:)`: `routeChangeNotification` with reason `.oldDeviceUnavailable` → callback on main.
- `MealOutput`: `play(unit)`, `stop()`, `replayRecent(withinS:)` (last unit if playing or ended < 30 s ago).
- `Pipeline`: `@Published var soundOn` (init from `headphonesConnected()`); `setSound(_:)` → worker stops or replays recent; `replay(unit)`; `start(threads:durationS:onMeal:)` where `onMeal` receives every started unit on main; `--mute` sets sound off. Worker plays only when sound is on; `Playback` log only for played meals.
- [x] Build (`device.py build`); commit `Add one sound control for headphone and speaker`.

### Task 4: Feed store (app)

**Files:** Create `FeedStore.swift`, `MealLibrary.swift`.

- `FeedStore` (`@MainActor ObservableObject`): `active: Feed`, `history: [Feed]` (newest first, excluding active); `append(unit, at:)`, `startNew()`, `delete(feed)`. Files `Documents/feeds/<epoch>.json` (atomic), pointer `Documents/feeds/active.txt`.
- `MealLibrary.shared.unit(sura:first:)` from `Assets.meal`.
- [x] Build; commit with Task 5.

### Task 5: Screens (app)

**Files:** Rewrite `ContentView.swift`; create `FeedView.swift`, `HistoryView.swift`.

- Top bar: Geçmiş, Yeni akış, Ses, A−, A+. Status line. `FeedView`. "Ekran açık kalsın" toggle (sun icon + text). Full-width 64 pt Başlat (green) / Durdur (red).
- `FeedView(feed:, scale:, onTap:)`: `LazyVStack` cards (title, text, multi-ayah note, HH:mm, last card highlighted); auto-scroll on new entry when at bottom (`onScrollGeometryChange`), else "Yeni meal ↓".
- `HistoryView`: list of `history` (date + `feedSummary`), swipe delete, push read-only `FeedView`.
- Keep-awake `@AppStorage("keepAwake")` → `isIdleTimerDisabled = keepAwake && running`. Text scale `@AppStorage("textScale")`.
- Measurement launch args unchanged; `--autostart` does not pass the feed.
- [x] Build, install; commit `Add the meal feed, history and controls`.

### Task 6: Lock screen

**Files:** Create `NowPlaying.swift`; wire in `ContentView`.

- `MPNowPlayingInfoCenter`: title = `mealTitle`, artist "Tilavet Meal"; `MPRemoteCommandCenter` play → start, pause → stop, toggle.
- [x] Build; commit `Show the current meal on the lock screen`.

### Task 7: App icon

**Files:** Create `scripts/draw_icon.swift`, `ios/TilavetApp/Assets.xcassets/AppIcon.appiconset/{Contents.json, icon.png}`; modify `project.yml`.

- Open book + rising sound waves, dark green background, cream/gold strokes; three variants to `~/Desktop/Tilavet Simge Taslakları/`; the first goes into the app; İsmail can swap.
- [x] Build, install; commit `Add the app icon`.

### Task 8: Device check

- [ ] Install over Wi-Fi; check feed, persistence, history, sound table, keep-awake, text size, lock screen, icon (Claude: logs and files; İsmail: by hand). Report results; İsmail decides final button placement.
