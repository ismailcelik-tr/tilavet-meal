import Foundation

/// Bundled files (scripts/ios_resources.sh) and the run output folder.
enum Assets {
    static let root = Bundle.main.resourceURL!.appendingPathComponent("Data")
    static let model = root.appendingPathComponent("model.int8.onnx")
    static let tokens = root.appendingPathComponent("tokens.txt")
    static let spelling = root.appendingPathComponent("spelling.json")
    static let quran = root.appendingPathComponent("quran-simple-clean.txt")
    static let meal = root.appendingPathComponent("tr.diyanet.txt")
    static let durations = root.appendingPathComponent("meal-durations-tr.diyanet-eren.csv")
    static let meals = root.appendingPathComponent("meals")
    static let parity = root.appendingPathComponent("parity")
    static let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]

    /// Write atomically, so a reader polling from the Mac never sees half a file.
    static func publish(_ data: Data, as name: String) throws {
        try data.write(to: documents.appendingPathComponent(name), options: .atomic)
    }
}
