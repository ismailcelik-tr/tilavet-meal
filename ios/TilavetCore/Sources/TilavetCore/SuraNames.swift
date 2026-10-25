/// Sura headings of Diyanet's Kur'an-ı Kerim Meali (kuran_meal.pdf), title-cased; index = sura - 1.
public let suraNames = [
    "Fâtiha", "Bakara", "Âl-i İmrân", "Nisâ", "Mâide", "En’âm", "A’râf", "Enfâl", "Tevbe", "Yûnus",
    "Hûd", "Yûsuf", "Ra’d", "İbrâhim", "Hicr", "Nahl", "İsrâ", "Kehf", "Meryem", "Tâ Hâ",
    "Enbiyâ", "Hac", "Mü’minûn", "Nûr", "Furkân", "Şu’arâ", "Neml", "Kasas", "Ankebût", "Rûm",
    "Lokmân", "Secde", "Ahzâb", "Sebe’", "Fâtır", "Yâsin", "Sâffât", "Sâd", "Zümer", "Mü’min",
    "Fussilet", "Şûrâ", "Zuhruf", "Duhân", "Câsiye", "Ahkâf", "Muhammed", "Fetih", "Hucurât", "Kâf",
    "Zâriyât", "Tûr", "Necm", "Kamer", "Rahmân", "Vâkı’a", "Hadîd", "Mücâdele", "Haşr", "Mümtehine",
    "Saff", "Cum’a", "Münâfikûn", "Teğabun", "Talâk", "Tahrîm", "Mülk", "Kalem", "Hâkka", "Me’âric",
    "Nûh", "Cin", "Müzzemmil", "Müddessir", "Kıyâme", "İnsân", "Mürselât", "Nebe’", "Nâzi’ât", "Abese",
    "Tekvîr", "İnfitâr", "Mutaffifîn", "İnşikâk", "Bürûc", "Târık", "A’lâ", "Ğaşiye", "Fecr", "Beled",
    "Şems", "Leyl", "Duhâ", "İnşirâh", "Tîn", "Alâk", "Kadr", "Beyyine", "Zilzâl", "Âdiyât",
    "Kâri’a", "Tekâsür", "Asr", "Hümeze", "Fil", "Kureyş", "Mâ’ûn", "Kevser", "Kâfirûn", "Nasr",
    "Tebbet", "İhlâs", "Felâk", "Nâs",
]

/// "Ahzâb Sûresi, 40. âyet"; a multi-ayah unit reads "Yûsuf Sûresi, 11-12. âyetler".
public func mealTitle(sura: Int, first: Int, last: Int) -> String {
    let name = suraNames[sura - 1]
    if first == last {
        return "\(name) Sûresi, \(first). âyet"
    }
    return "\(name) Sûresi, \(first)-\(last). âyetler"
}
