import SwiftUI
import TilavetCore

/// Meal cards in order; every new meal scrolls into view. The highlighted card is the latest meal, or the one
/// the reader tapped to replay until the next meal arrives.
struct FeedView: View {
    let feed: Feed
    let scale: Double
    /// Replays a meal; false when it could not (sound off).
    let onTap: (MealUnit) -> Bool

    @State private var selected: Int?

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(Array(feed.entries.enumerated()), id: \.offset) { index, entry in
                        MealCard(entry: entry, scale: scale,
                                 highlighted: index == (selected ?? feed.entries.count - 1))
                            .id(index)
                            .onTapGesture {
                                if let unit = MealLibrary.shared.unit(entry), onTap(unit) {
                                    selected = index
                                }
                            }
                    }
                }
                .padding(.horizontal)
            }
            .onChange(of: feed.entries.count) {
                selected = nil
                scrollToEnd(proxy, animated: true)
            }
            .onAppear {
                scrollToEnd(proxy, animated: false)
            }
            .overlay {
                if feed.entries.isEmpty {
                    Text("Başlat'a basın; duyulan âyetlerin meali burada listelenir.")
                        .multilineTextAlignment(.center)
                        .foregroundStyle(.secondary)
                        .padding()
                }
            }
        }
    }

    private func scrollToEnd(_ proxy: ScrollViewProxy, animated: Bool) {
        guard !feed.entries.isEmpty else {
            return
        }
        withAnimation(animated ? .default : nil) {
            proxy.scrollTo(feed.entries.count - 1, anchor: .bottom)
        }
    }
}

/// Title, meal text, the joint-translation note and the time.
struct MealCard: View {
    let entry: FeedEntry
    let scale: Double
    let highlighted: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline) {
                Text(mealTitle(sura: entry.sura, first: entry.first, last: entry.last))
                    .font(scaled(.headline, weight: .semibold))
                Spacer()
                Text(entry.startedAt, format: .dateTime.hour().minute())
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Text(MealLibrary.shared.unit(entry)?.text ?? "")
                .font(scaled(.body))
            if entry.first != entry.last {
                Text("(\(entry.first)-\(entry.last). âyetler birbirine bağlı olduğu için birlikte çevrilmiştir.)")
                    .font(scaled(.footnote))
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12)
            .fill(highlighted ? Color.accentColor.opacity(0.12) : Color(.secondarySystemBackground)))
        .contentShape(Rectangle())
    }

    /// Dynamic Type size times the user's text scale.
    private func scaled(_ style: UIFont.TextStyle, weight: Font.Weight = .regular) -> Font {
        .system(size: UIFont.preferredFont(forTextStyle: style).pointSize * scale, weight: weight)
    }
}
