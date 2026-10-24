/// Track mode within one sura: words needed to rule out nearby ayahs and restarts in the previous one.
/// Mirrors tilavet.feasibility.track_prefix_lengths; nil for the first ayah or if never resolved.
func trackPrefixLengths(_ ayahs: [[String]], window: Int) -> [Int?] {
    let stream = ayahs.flatMap { $0 }
    var starts: [Int] = []
    var cursor = 0
    for ayah in ayahs {
        starts.append(cursor)
        cursor += ayah.count
    }

    var result: [Int?] = [nil]
    for index in 1..<max(1, ayahs.count) {
        let start = starts[index]
        let neighbours = max(0, index - window)..<min(ayahs.count, index + window + 1)
        var rivals = Set(neighbours.map { starts[$0] }).union(starts[index - 1]..<start)
        rivals.remove(start)
        result.append(wordsToResolve(stream, start, rivals))
    }
    return result
}

private func wordsToResolve(_ stream: [String], _ start: Int, _ rivals: Set<Int>) -> Int? {
    var rivals = rivals
    for offset in 0..<(stream.count - start) {
        let word = stream[start + offset]
        rivals = rivals.filter { $0 + offset < stream.count && stream[$0 + offset] == word }
        if rivals.isEmpty {
            return offset + 1
        }
    }
    return nil
}
