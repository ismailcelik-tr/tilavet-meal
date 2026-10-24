/// Two-mode position tracker over ASR window hypotheses; mirrors tilavet.engine.tracker (rules frozen at 398b251).
public struct EngineConfig: Sendable {
    var acquireMinMatched = 4
    var acquireMinScore = 6
    var acquireMargin = 3
    var acquireMinVotes = 3
    var acquireMaxCandidates = 8
    var acquireRivalVotes = 2  // the winner's corpus words lining up elsewhere: a look-alike passage
    var diagonalTolerance = 8  // words; ASR insertions/deletions shift the diagonal
    var commonWordLimit = 500  // words with more occurrences don't vote
    var trackBack = 30
    var trackAhead = 50
    var trackMinScore = 3
    var trackTieSlack = 0
    var trackMargin = 2  // words a rival this close elsewhere also explains are contested (near-duplicates)
    var pastMargin = 3  // rivals over ayahs already recited: likely a repetition, contest more readily
    var confirmWords = 2  // minimum; raised per ayah to what sets it apart from its neighbours
    var distinctWindow = 3
    var prefixSlack = 1  // ASR may drop one of the opening words
    var maxSkip = 2  // ayahs a reciter may skip and still count as sequential
    var jumpExtra = 1
    var lostAfter = 4  // consecutive non-matching hops
    var minWordsForMiss = 3

    public init() {}
}

public enum Mode: String, Sendable {
    case acquire, track
}

public enum Event: Equatable, Sendable {
    case confirmed(t: Double, ref: AyahRef, mode: Mode, score: Int)
    case lost(t: Double)
}

public final class PositionEngine {
    private let index: QuranIndex
    private let config: EngineConfig
    private(set) var mode = Mode.acquire
    private var pointer = 0
    private var lastConfirmed = -1
    private var confirmed: Set<Int> = []
    private var misses = 0
    private let distinct: [Int?]

    public init(_ index: QuranIndex, _ config: EngineConfig = EngineConfig()) {
        self.index = index
        self.config = config
        distinct = distinctPrefixes(index, config.distinctWindow)
    }

    public func feed(_ t: Double, _ words: [String]) -> [Event] {
        if words.isEmpty {
            return []
        }

        return mode == .acquire ? acquire(t, words) : track(t, words)
    }

    private func acquire(_ t: Double, _ words: [String]) -> [Event] {
        let voters = words.enumerated().map { ($0.offset, $0.element) }
        let alignments = candidateAlignments(words, voters, config.acquireMinVotes, config.acquireMaxCandidates)
        guard let best = firstMax(alignments) else {
            return []
        }

        // Look-alikes share the winner's corpus words, not the (maybe misheard) hypothesis words.
        let lookalikes = candidateAlignments(words, best.pairs.map { ($0.hyp, index.words[$0.pos]) },
                                             config.acquireRivalVotes, nil)
        let rivals = (alignments + lookalikes).filter { !overlaps($0, best) }
        let runnerUp = rivals.map(\.score).max() ?? 0

        if best.score < config.acquireMinScore || best.matched < config.acquireMinMatched
            || best.score - runnerUp < config.acquireMargin {
            return []
        }

        mode = .track
        pointer = best.corpusEnd
        misses = 0
        let current = index.ordinalAt(best.positions.last!)
        lastConfirmed = current
        confirmed = [current]
        return [.confirmed(t: t, ref: index.ref(current), mode: .acquire, score: best.score)]
    }

    /// Align regions where at least `minVotes` (hypothesis index, word) voters line up; at most `limit`.
    private func candidateAlignments(_ words: [String], _ voters: [(Int, String)], _ minVotes: Int,
                                     _ limit: Int?) -> [Alignment] {
        var diagonals: [Int: Int] = [:]
        for (i, word) in voters {
            let positions = index.positions(word)
            if positions.count > config.commonWordLimit {
                continue
            }
            for position in positions {
                diagonals[position - i, default: 0] += 1
            }
        }

        let tolerance = config.diagonalTolerance
        let support = diagonals.keys.map { d in
            (d, (-tolerance...tolerance).reduce(0) { $0 + (diagonals[d + $1] ?? 0) })
        }

        var chosen: [Int] = []
        for (diagonal, votes) in support.sorted(by: { ($1.1, $0.0) < ($0.1, $1.0) }) {
            if votes < minVotes {
                break
            }
            if let limit, chosen.count >= limit {
                break
            }
            if chosen.allSatisfy({ abs(diagonal - $0) > tolerance }) {
                chosen.append(diagonal)
            }
        }

        // Rivals below this cannot block a commit, so they need not be found.
        let minScore = max(1, config.acquireMinScore - config.acquireMargin)
        var alignments: [Alignment] = []
        let corpus = index.words
        for diagonal in chosen {
            let lo = max(0, diagonal - tolerance)
            let hi = min(corpus.count, diagonal + words.count + tolerance)
            for alignment in alignAll(words, corpus, lo, hi, minScore)
            where !alignments.contains(where: { overlaps(alignment, $0) }) {
                alignments.append(alignment)
            }
        }
        return alignments
    }

    private func track(_ t: Double, _ words: [String]) -> [Event] {
        let corpus = index.words
        let lo = max(0, pointer - config.trackBack)
        let hi = min(corpus.count, pointer + config.trackAhead)
        let alignments = alignAll(words, corpus, lo, hi, config.trackMinScore)

        if alignments.isEmpty {
            if words.count < config.minWordsForMiss {
                return []
            }

            misses += 1
            if misses < config.lostAfter {
                return []
            }

            mode = .acquire
            return [.lost(t: t)]
        }

        // Ties (refrains, back-jumps): the most recent words decide, then closeness to the pointer.
        let bestScore = alignments.map(\.score).max()!
        var alignment: Alignment?
        for a in alignments where a.score >= bestScore - config.trackTieSlack {
            guard let current = alignment else {
                alignment = a
                continue
            }
            if (-a.hypEnd, abs(a.corpusEnd - pointer)) < (-current.hypEnd, abs(current.corpusEnd - pointer)) {
                alignment = a
            }
        }
        let chosen = alignment!
        misses = 0
        pointer = chosen.corpusEnd

        let rivals = alignments.filter { !overlaps($0, chosen) && $0.score > chosen.score - margin($0) }
        let contested = Set(rivals.flatMap { $0.pairs.map(\.hyp) })
        let evidence = Set(chosen.pairs.filter { !contested.contains($0.hyp) }.map(\.pos))

        let current = index.ordinalAt(chosen.positions.last!)
        var events: [Event] = []
        for ordinal in Set(chosen.positions.map(index.ordinalAt)).sorted() {
            let sequential = lastConfirmed < ordinal && ordinal <= lastConfirmed + 1 + config.maxSkip
            if confirmed.contains(ordinal) || (!sequential && ordinal != current) {
                continue
            }

            let span = index.span(index.ref(ordinal))
            let extra = sequential ? 0 : config.jumpExtra
            let needed = min(max(config.confirmWords, distinct[ordinal] ?? 0) + extra, span.count)
            let prefix = span.lowerBound..<min(span.upperBound, span.lowerBound + needed + config.prefixSlack)
            if prefix.filter(evidence.contains).count < needed {
                continue
            }

            events.append(.confirmed(t: t, ref: index.ref(ordinal), mode: .track, score: chosen.score))
            confirmed.insert(ordinal)
            lastConfirmed = max(lastConfirmed, ordinal)
        }
        return events
    }

    private func margin(_ rival: Alignment) -> Int {
        let recited = rival.positions.allSatisfy { confirmed.contains(index.ordinalAt($0)) }
        return recited ? config.pastMargin : config.trackMargin
    }
}

/// Python `max(alignments, key=score)`: the first maximum.
private func firstMax(_ alignments: [Alignment]) -> Alignment? {
    var best: Alignment?
    for a in alignments where best == nil || a.score > best!.score {
        best = a
    }
    return best
}

/// Per ayah ordinal: opening words needed to tell it from nearby ayahs (nil: never resolved / first).
private func distinctPrefixes(_ index: QuranIndex, _ window: Int) -> [Int?] {
    var bySura: [Int: [Int]] = [:]
    for (ordinal, ref) in index.refs.enumerated() {
        bySura[ref.sura, default: []].append(ordinal)
    }

    var result = [Int?](repeating: nil, count: index.refs.count)
    for ordinals in bySura.values {
        let ayahs = ordinals.map { Array(index.words[index.span(index.ref($0))]) }
        for (o, k) in zip(ordinals, trackPrefixLengths(ayahs, window: window)) {
            result[o] = k
        }
    }
    return result
}

private func overlaps(_ a: Alignment, _ b: Alignment) -> Bool {
    a.corpusStart < b.corpusEnd && b.corpusStart < a.corpusEnd
}
