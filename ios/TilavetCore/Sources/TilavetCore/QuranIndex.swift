/// The recited word stream in mushaf order, with word -> ayah lookups.
public final class QuranIndex: Sendable {
    public let words: [String]
    public let refs: [AyahRef]
    private let wordAyah: [Int]  // ordinal of each word's ayah
    private let ordinals: [AyahRef: Int]
    private let starts: [Int]  // ordinal -> first word position
    private let postings: [String: [Int]]

    /// The recited text: Tanzil simple-clean without the basmala prefixes, normalized.
    public static func recited(_ quran: [AyahRef: String]) -> QuranIndex {
        build(Dictionary(uniqueKeysWithValues: quran.map { ($0.key, TilavetCore.words(normalize(stripBasmala($0.key, $0.value)))) }))
    }

    public static func build(_ ayahs: [AyahRef: [String]]) -> QuranIndex {
        let refs = ayahs.keys.sorted()
        var words: [String] = [], wordAyah: [Int] = [], starts: [Int] = []
        var postings: [String: [Int]] = [:]

        for (ordinal, ref) in refs.enumerated() {
            starts.append(words.count)
            for word in ayahs[ref]! {
                postings[word, default: []].append(words.count)
                words.append(word)
                wordAyah.append(ordinal)
            }
        }

        let ordinals = Dictionary(uniqueKeysWithValues: refs.enumerated().map { ($1, $0) })
        return QuranIndex(words: words, refs: refs, wordAyah: wordAyah, ordinals: ordinals, starts: starts,
                          postings: postings)
    }

    private init(words: [String], refs: [AyahRef], wordAyah: [Int], ordinals: [AyahRef: Int], starts: [Int],
                 postings: [String: [Int]]) {
        self.words = words
        self.refs = refs
        self.wordAyah = wordAyah
        self.ordinals = ordinals
        self.starts = starts
        self.postings = postings
    }

    func ordinal(_ ref: AyahRef) -> Int {
        ordinals[ref]!
    }

    func ordinalAt(_ position: Int) -> Int {
        wordAyah[position]
    }

    func ref(_ ordinal: Int) -> AyahRef {
        refs[ordinal]
    }

    /// Word positions of an ayah.
    func span(_ ref: AyahRef) -> Range<Int> {
        let ordinal = ordinals[ref]!
        let end = ordinal + 1 < starts.count ? starts[ordinal + 1] : words.count
        return starts[ordinal]..<end
    }

    func positions(_ word: String) -> [Int] {
        postings[word] ?? []
    }
}
