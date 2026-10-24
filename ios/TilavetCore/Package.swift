// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "TilavetCore",
    platforms: [.macOS(.v15), .iOS(.v18)],
    products: [.library(name: "TilavetCore", targets: ["TilavetCore"])],
    targets: [
        .target(name: "TilavetCore"),
        .testTarget(name: "TilavetCoreTests", dependencies: ["TilavetCore"]),
    ]
)
