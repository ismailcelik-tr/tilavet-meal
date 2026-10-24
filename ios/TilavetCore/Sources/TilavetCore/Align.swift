/// Local (Smith-Waterman) alignment of ASR words against a corpus region; mirrors tilavet.engine.align.

let strongSim = 0.9
let weakSim = 0.7
let strongScore = 2
let weakScore = 1
let mismatch = -1
let gap = -1

// Python breaks ties in max((value, direction)) by the larger direction: LEFT, then UP, then DIAG.
private enum Move: Int, Comparable {
    case none = 0, diag, up, left

    static func < (lhs: Move, rhs: Move) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}

struct Pair: Equatable {
    let hyp: Int
    let pos: Int
}

struct Alignment: Equatable {
    let score: Int
    let corpusStart: Int  // [start, end) of the aligned corpus span
    let corpusEnd: Int
    let pairs: [Pair]  // matched words
    let hypEnd: Int  // hypothesis words [.., hypEnd) take part; larger = covers more recent audio

    var positions: [Int] {
        pairs.map(\.pos)
    }

    var matched: Int {
        pairs.count
    }
}

/// rapidfuzz `Indel.normalized_similarity`.
func indelSimilarity(_ a: String, _ b: String) -> Double {
    let x = Array(a.unicodeScalars), y = Array(b.unicodeScalars)
    let total = x.count + y.count
    if total == 0 {
        return 1.0
    }

    var previous = [Int](repeating: 0, count: y.count + 1)
    for i in 0..<x.count {
        var current = [Int](repeating: 0, count: y.count + 1)
        for j in 0..<y.count {
            current[j + 1] = x[i] == y[j] ? previous[j] + 1 : max(previous[j + 1], current[j])
        }
        previous = current
    }

    let distance = total - 2 * previous[y.count]
    return 1.0 - Double(distance) / Double(total)
}

private func substitution(_ a: String, _ b: String) -> Int {
    let similarity = indelSimilarity(a, b)
    if similarity >= strongSim {
        return strongScore
    }
    if similarity >= weakSim {
        return weakScore
    }
    return mismatch
}

/// Best local alignment of `hyp` inside corpus[lo..<hi]; nil if nothing scores above 0.
func localAlign(_ hyp: [String], _ corpus: [String], _ lo: Int, _ hi: Int) -> Alignment? {
    let region = corpus[lo..<hi]
    let rows = hyp.count + 1, cols = region.count + 1
    var score = [[Int]](repeating: [Int](repeating: 0, count: cols), count: rows)
    var move = [[Move]](repeating: [Move](repeating: .none, count: cols), count: rows)
    var sub = [[Int]](repeating: [Int](repeating: 0, count: cols), count: rows)
    var best = 0, bestAt = (0, 0)

    for i in 1..<rows {
        for j in 1..<cols {
            sub[i][j] = substitution(hyp[i - 1], region[lo + j - 1])
            let candidates = [
                (score[i - 1][j - 1] + sub[i][j], Move.diag),
                (score[i - 1][j] + gap, Move.up),
                (score[i][j - 1] + gap, Move.left),
            ]
            let (value, direction) = candidates.max { ($0.0, $0.1) < ($1.0, $1.1) }!
            if value <= 0 {
                continue
            }

            score[i][j] = value
            move[i][j] = direction
            if value > best {
                best = value
                bestAt = (i, j)
            }
        }
    }

    if best <= 0 {
        return nil
    }

    var (i, j) = bestAt
    let hypEnd = i, end = j
    var pairs: [Pair] = []
    while i > 0 && j > 0 && score[i][j] > 0 {
        switch move[i][j] {
        case .diag:
            if sub[i][j] > 0 {
                pairs.append(Pair(hyp: i - 1, pos: lo + j - 1))
            }
            i -= 1
            j -= 1
        case .up:
            i -= 1
        default:
            j -= 1
        }
    }

    return Alignment(score: best, corpusStart: lo + j, corpusEnd: lo + end, pairs: pairs.reversed(), hypEnd: hypEnd)
}

/// Non-overlapping alignments scoring >= minScore: best one, then recurse left and right of it.
func alignAll(_ hyp: [String], _ corpus: [String], _ lo: Int, _ hi: Int, _ minScore: Int) -> [Alignment] {
    guard let best = localAlign(hyp, corpus, lo, hi), best.score >= minScore else {
        return []
    }

    return alignAll(hyp, corpus, lo, best.corpusStart, minScore) + [best]
        + alignAll(hyp, corpus, best.corpusEnd, hi, minScore)
}
