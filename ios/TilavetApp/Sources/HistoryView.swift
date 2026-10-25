import SwiftUI
import TilavetCore

/// The active feed and past feeds; open one to read it, swipe to delete.
struct HistoryView: View {
    @ObservedObject var store: FeedStore
    let scale: Double
    let onTap: (MealUnit) -> Bool

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section("Şu anki akış") {
                    row(store.active)
                        .swipeActions {
                            Button("Sil", role: .destructive) {
                                store.delete(store.active)
                            }
                        }
                }
                Section("Geçmiş") {
                    if store.history.isEmpty {
                        Text("Henüz geçmiş akış yok.")
                            .foregroundStyle(.secondary)
                    }
                    ForEach(store.history) { feed in
                        NavigationLink {
                            FeedView(feed: feed, scale: scale, onTap: onTap)
                                .navigationTitle(Text(feed.id, format: .dateTime.day().month().hour().minute()))
                                .navigationBarTitleDisplayMode(.inline)
                        } label: {
                            row(feed)
                        }
                    }
                    .onDelete { offsets in
                        offsets.map { store.history[$0] }.forEach(store.delete)
                    }
                }
            }
            .navigationTitle("Geçmiş")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Kapat") {
                        dismiss()
                    }
                }
            }
        }
    }

    private func row(_ feed: Feed) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(feed.id, format: .dateTime.day().month().hour().minute())
            Text(feedSummary(feed))
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }
}
