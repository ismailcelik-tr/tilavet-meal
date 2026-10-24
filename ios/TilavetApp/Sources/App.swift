import SwiftUI

@main
struct TilavetApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

/// Launch arguments, so the Mac can drive measurement runs (`devicectl device process launch ... -- ARGS`).
enum LaunchArgs {
    static let all = ProcessInfo.processInfo.arguments

    static func has(_ flag: String) -> Bool {
        all.contains(flag)
    }

    static func value(_ flag: String) -> String? {
        guard let i = all.firstIndex(of: flag), i + 1 < all.count else {
            return nil
        }
        return all[i + 1]
    }
}
