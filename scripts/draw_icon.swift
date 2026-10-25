// App icon: an open book with sound waves rising from it.
//
//     swift scripts/draw_icon.swift <a|b|c> <out.png>
//
// a: filled pages, gold arcs; b: gold line book, cream arcs; c: filled pages, waveform bars.
import AppKit

let size = 1024.0
let green = (top: CGColor(red: 0.08, green: 0.36, blue: 0.26, alpha: 1),
             bottom: CGColor(red: 0.04, green: 0.20, blue: 0.15, alpha: 1))
let cream = CGColor(red: 0.96, green: 0.92, blue: 0.82, alpha: 1)
let gold = CGColor(red: 0.85, green: 0.69, blue: 0.30, alpha: 1)

let args = CommandLine.arguments
guard args.count == 3, ["a", "b", "c"].contains(args[1]) else {
    print("usage: draw_icon.swift <a|b|c> <out.png>")
    exit(1)
}
let variant = args[1]

// No alpha channel: iOS app icons must be opaque.
let ctx = CGContext(data: nil, width: Int(size), height: Int(size), bitsPerComponent: 8, bytesPerRow: 0,
                    space: CGColorSpace(name: CGColorSpace.sRGB)!,
                    bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!

// Background (iOS rounds the corners itself; the icon must be opaque and square).
let gradient = CGGradient(colorsSpace: nil, colors: [green.top, green.bottom] as CFArray, locations: [0, 1])!
ctx.drawLinearGradient(gradient, start: CGPoint(x: 0, y: size), end: CGPoint(x: 0, y: 0), options: [])

// Open book: two pages meeting at the spine, lower third of the icon (origin bottom-left).
let spine = CGPoint(x: size / 2, y: 300)
let pageWidth = 300.0
let pageRise = 70.0
let pageHeight = 190.0

func page(_ side: Double) -> CGPath {
    let path = CGMutablePath()
    let outer = spine.x + side * pageWidth
    path.move(to: spine)
    path.addQuadCurve(to: CGPoint(x: outer, y: spine.y + pageRise),
                      control: CGPoint(x: spine.x + side * pageWidth * 0.5, y: spine.y - 25))
    path.addLine(to: CGPoint(x: outer, y: spine.y + pageRise + pageHeight))
    path.addQuadCurve(to: CGPoint(x: spine.x, y: spine.y + pageHeight),
                      control: CGPoint(x: spine.x + side * pageWidth * 0.5, y: spine.y + pageHeight - 25 + pageRise))
    path.closeSubpath()
    return path
}

ctx.setLineJoin(.round)
ctx.setLineCap(.round)
for side in [-1.0, 1.0] {
    ctx.addPath(page(side))
    if variant == "b" {
        ctx.setStrokeColor(gold)
        ctx.setLineWidth(22)
        ctx.strokePath()
    } else {
        ctx.setFillColor(cream)
        ctx.fillPath()
    }
}
if variant != "b" {
    ctx.setStrokeColor(green.bottom)
    ctx.setLineWidth(12)
    ctx.move(to: spine)
    ctx.addLine(to: CGPoint(x: spine.x, y: spine.y + pageHeight))
    ctx.strokePath()
}

// Sound rising from the open book; bars sit higher so they clear the page edges.
let center = CGPoint(x: size / 2, y: spine.y + pageHeight + (variant == "c" ? 75 : 40))
if variant == "c" {
    let heights = [70.0, 130.0, 210.0, 130.0, 70.0]
    let barWidth = 44.0
    let gap = 30.0
    let total = Double(heights.count) * barWidth + Double(heights.count - 1) * gap
    ctx.setFillColor(gold)
    for (i, height) in heights.enumerated() {
        let x = center.x - total / 2 + Double(i) * (barWidth + gap)
        ctx.addPath(CGPath(roundedRect: CGRect(x: x, y: center.y, width: barWidth, height: height),
                           cornerWidth: barWidth / 2, cornerHeight: barWidth / 2, transform: nil))
        ctx.fillPath()
    }
} else {
    ctx.setStrokeColor(variant == "a" ? gold : cream)
    ctx.setLineWidth(30)
    for radius in [90.0, 170.0, 250.0] {
        ctx.addArc(center: center, radius: radius, startAngle: .pi * 0.25, endAngle: .pi * 0.75, clockwise: false)
        ctx.strokePath()
    }
}

let data = NSBitmapImageRep(cgImage: ctx.makeImage()!).representation(using: .png, properties: [:])!
try! data.write(to: URL(fileURLWithPath: args[2]))
