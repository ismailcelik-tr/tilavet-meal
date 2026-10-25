import XCTest

@testable import TilavetCore

final class SuraNamesTests: XCTestCase {
    func testDiyanetSpelling() {
        XCTAssertEqual(suraNames.count, 114)
        XCTAssertEqual(suraNames[0], "Fâtiha")
        XCTAssertEqual(suraNames[2], "Âl-i İmrân")
        XCTAssertEqual(suraNames[22], "Mü’minûn")
        XCTAssertEqual(suraNames[32], "Ahzâb")
        XCTAssertEqual(suraNames[113], "Nâs")
    }

    func testTitle() {
        XCTAssertEqual(mealTitle(sura: 33, first: 40, last: 40), "Ahzâb Sûresi, 40. âyet")
        XCTAssertEqual(mealTitle(sura: 12, first: 11, last: 12), "Yûsuf Sûresi, 11-12. âyetler")
    }
}
