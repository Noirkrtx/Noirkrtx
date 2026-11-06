"""NOIR GitHub profil banner'ı ve araç kartı (Kâğıt & Mürekkep tasarım dili).

Bütün yazılar kodla dizilir; görsel üretici model kullanılmaz.
Fontlar bu dosyanın yanındaki fonts/ klasöründen okunur (SIL OFL 1.1).

Kullanım:
    python banner.py                 # banner.png + kart-dogallastirici.png

ciz(durum) animasyon.py tarafından kare kare çağrılır; durum verilmezse son hâl çizilir.
"""
import argparse
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

KOK = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(KOK, "fonts")

W, H = 1600, 640          # çıktı boyutu
S = 2                     # iç çizim ölçeği (2x çizilip küçültülür, kenarlar yumuşar)

KAGIT, MUREKKEP, GRI, CIZGI, YUZEY = "#F1EEE7", "#16171B", "#5A5B60", "#D5D0C5", "#E7E2D7"
VURGU = {"kare": "#C8401F", "parantez": "#2445B5", "ceyrek": "#58702F", "cizgi": "#6E1C27", "halka": "#0B7A63"}
MERCEK = ("#C47F2C", "#2F6F8F")   # imzadan önceki iki renkli kapsül

SON = {"cizgi": 1, "ust": 1, "baslik": 4, "satir": 1, "isaret": 4, "alt": 1}


def tr_buyuk(s):
    """Türkçe büyük harf: i→İ, ı→I (str.upper() bunu bilmez)."""
    return str(s).replace("i", "İ").replace("ı", "I").upper()


def s(v):
    return int(round(v * S))


_fc = {}


def font(ad, px, agirlik=None):
    k = (ad, px, agirlik)
    if k not in _fc:
        f = ImageFont.truetype(os.path.join(FONT, ad), s(px))
        if agirlik is not None:                        # Newsreader değişken: [wght, opsz]
            f.set_variation_by_axes([agirlik, min(72, max(6, px))])
        _fc[k] = f
    return _fc[k]


def serif(px, w=600):
    return font("Newsreader-VF.ttf", px, w)


def italik(px, w=420):
    return font("Newsreader-Italic-VF.ttf", px, w)


def mono(px, kalin=True):
    return font("IBMPlexMono-SemiBold.ttf" if kalin else "IBMPlexMono-Medium.ttf", px)


# ── çizim yardımcıları ─────────────────────────────────────────────────────
class Tuval:
    """Renkli zemin + maske üstünden yarı saydam boyama (alfa = 0..1)."""

    def __init__(self, zemin):
        self.im = zemin.copy()

    def boya(self, renk, maske_ciz, alfa=1.0, wipe=None):
        if alfa <= 0:
            return
        m = Image.new("L", self.im.size, 0)
        maske_ciz(ImageDraw.Draw(m))
        if wipe is not None:                       # soldan sağa yumuşak kenarlı açılma
            m = ImageChops.multiply(m, wipe)
        if alfa < 1:
            m = m.point(lambda v: int(v * alfa))
        self.im.paste(renk, (0, 0), m)


def aralikli(d, x, y, metin, f, takip_em, fill=255, anchor="ls"):
    """Harf aralıklı (letter-spacing) mono yazı; genişliği döndürür (2x px)."""
    tk = f.size * takip_em
    for ch in metin:
        d.text((x, y), ch, font=f, fill=fill, anchor=anchor)
        x += f.getlength(ch) + tk
    return x


def aralikli_gen(metin, f, takip_em):
    return sum(f.getlength(c) for c in metin) + f.size * takip_em * (len(metin) - 1)


def isaret(d, tur, x, y, boy, fill=255):
    """Seri işaretleri (logo değil): x,y = sol üst; boy = 1x px."""
    b, k = s(boy), s(3)
    if tur == "kare":
        d.rectangle([x, y, x + int(b * .88), y + int(b * .88)], fill=fill)
    elif tur == "parantez":
        d.rectangle([x, y, x + int(b * .9), y + int(b * .9)], outline=fill, width=s(4))
    elif tur == "ceyrek":
        d.pieslice([x, y, x + 2 * b, y + 2 * b], 180, 270, fill=fill)  # sol üst çeyrek, kutu b×b
    elif tur == "cizgi":
        yy = y + b // 2
        d.rectangle([x, yy - s(2.5), x + b, yy + s(2.5)], fill=fill)
    elif tur == "halka":
        d.ellipse([x, y, x + b, y + b], outline=fill, width=k)
        r = int(b * .22)
        c = (x + b // 2, y + b // 2)
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=fill)


def kapsul(im, kx, ky, kw, kh, alfa=1.0):
    """İmzadan önceki iki renkli kapsül (sol koyu sarı, sağ petrol mavisi); 2x px."""
    for j, renk in enumerate(MERCEK):
        m = Image.new("L", im.size, 0)
        g = ImageDraw.Draw(m)
        g.rounded_rectangle([kx, ky, kx + kw, ky + kh], radius=kh // 2, fill=int(255 * alfa))
        orta = kx + kw // 2
        g.rectangle([orta, ky, kx + kw, ky + kh] if j == 0 else [kx, ky, orta - 1, ky + kh], fill=0)
        im.paste(renk, (0, 0), m)


def wipe_maske(boyut, x0, x1, p, yumusak=60):
    """p∈[0,1]: x0→x1 arası soldan sağa açılan yatay maske."""
    w, h = boyut
    on = x0 + (x1 - x0 + s(yumusak)) * p
    satir = Image.new("L", (w, 1))
    px = satir.load()
    for x in range(w):
        v = (on - x) / s(yumusak)
        px[x, 0] = int(255 * max(0.0, min(1.0, v)))
    return satir.resize((w, h))


def kademe(t, a, b):
    """t'yi [a,b] aralığında 0..1'e eşler; yumuşak (smoothstep)."""
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


# ── banner ─────────────────────────────────────────────────────────────────
SATIR = "Türkçe yapay zekâ araçları ve okuma notları"
SUTUN = [("kare", "ARAÇLAR"), ("parantez", "SKILL'LER"), ("ceyrek", "OKUMA NOTLARI"), ("cizgi", "ARAŞTIRMA NOTLARI")]  # elle büyük harf: "skill" İngilizce, İ almaz
X0, X1 = 80, 1520


def zemin(yon="b"):
    return Image.new("RGB", (s(W), s(H)), KAGIT)


def _alfa(v, i):
    """v sayıysa i. öğe için clamp(v - i); liste ise doğrudan v[i] (örtüşen geçişler için)."""
    if isinstance(v, (list, tuple)):
        return v[i]
    return max(0.0, min(1.0, v - i))


def ciz(durum=None, _zemin=None):
    """durum: SON anahtarlarıyla ilerleme (0..1; baslik/isaret 0..4 ya da 4 öğeli alfa listesi)."""
    d = dict(SON, **(durum or {}))
    t = Tuval(_zemin if _zemin is not None else zemin())
    ink, gri, cizgi, dek = MUREKKEP, GRI, CIZGI, "#4E4F53"

    # üst şerit: işaret + seri adı solda, meta sağda, altında 3 px mürekkep çizgi
    yb = s(70)
    fu, fm_ = mono(24), mono(24, False)
    t.boya(ink, lambda g: isaret(g, "parantez", s(X0), s(49), 22), d["ust"])
    t.boya(ink, lambda g: aralikli(g, s(X0 + 40), yb, "ATÖLYE", fu, .14), d["ust"])
    sag = "TÜRKÇE · AÇIK KAYNAK"
    gw = aralikli_gen(sag, fm_, .14)
    t.boya(gri, lambda g: aralikli(g, s(X1) - gw, yb, sag, fm_, .14), d["ust"])
    if d["cizgi"] > 0:
        xe = s(X0) + (s(X1) - s(X0)) * d["cizgi"]
        t.boya(ink, lambda g: g.rectangle([s(X0), s(94), xe, s(97) - 1], fill=255))

    # başlık: harf harf mürekkep belirmesi (kerning için önek genişliği kullanılır)
    f = serif(232, 600)
    bx, by = s(72), s(352)
    for i, ch in enumerate("NOIR"):
        a = _alfa(d["baslik"], i)
        if a > 0:
            x = bx + f.getlength("NOIR"[:i])
            t.boya(ink, lambda g, x=x, ch=ch: g.text((x, by), ch, font=f, fill=255, anchor="ls"), a)

    # alt satır: soldan sağa açılma
    if d["satir"] > 0:
        fi = italik(48)
        sx = s(X0 + 2)
        sw = fi.getlength(SATIR)
        wm = None if d["satir"] >= 1 else wipe_maske((s(W), s(H)), sx, sx + sw, d["satir"])
        t.boya(dek, lambda g: g.text((sx, s(448)), SATIR, font=fi, fill=255, anchor="ls"), 1, wm)

    # sağ sütun: içerik dizini, her satır bir seri işaretiyle
    n = d["isaret"]
    cx = 1112
    n0 = _alfa(n, 0)
    t.boya(cizgi, lambda g: g.rectangle([s(cx - 52), s(140), s(cx - 52) + s(1.5), s(510)], fill=255), n0)
    t.boya(gri, lambda g: aralikli(g, s(cx), s(172), "BURADA", mono(20, False), .16), n0)
    for i, (tur, ad) in enumerate(SUTUN):
        a = _alfa(n, i)
        if a <= 0:
            continue
        y = 244 + i * 76
        ox = 2 if tur in ("kare", "parantez") else 0      # 28 px yuvada optik ortalama
        t.boya(VURGU[tur], lambda g, tur=tur, y=y, ox=ox: isaret(g, tur, s(cx + ox), s(y - 20), 24), a)
        t.boya(ink, lambda g, ad=ad, y=y: aralikli(g, s(cx + 54), s(y), ad, mono(25), .1), a)

    # alt şerit: 1.5 px açık çizgi, solda kaynak, sağda imza
    al = d["alt"]
    if al > 0:
        ya = 600
        t.boya(cizgi, lambda g: g.rectangle([s(X0), s(558), s(X0) + (s(X1) - s(X0)) * al, s(559.5)], fill=255))
        t.boya(gri, lambda g: aralikli(g, s(X0), s(ya), "GITHUB.COM/NOIRKRTX", mono(21, False), .1), al)
        fm = mono(22)
        iw = aralikli_gen("@noirkrtx", fm, .06)
        ix = s(X1) - iw
        kw, kh = s(40), s(9)
        kx, ky = ix - s(54), s(ya) - s(8) - kh // 2
        kapsul(t.im, kx, ky, kw, kh, al)
        t.boya(ink, lambda g: aralikli(g, ix, s(ya), "@noirkrtx", fm, .06), al)

    return t.im.resize((W, H), Image.LANCZOS)


# ── araç kartı (README'deki kart) ──────────────────────────────────────────
def kart(yol):
    KW, KH = 1600, 520
    im = Image.new("RGB", (s(KW), s(KH)), KAGIT)
    g = ImageDraw.Draw(im)
    x0, x1 = 72, KW - 72
    v = VURGU["parantez"]
    isaret(g, "parantez", s(x0), s(45), 22, fill=v)
    aralikli(g, s(x0 + 40), s(65), "ARAÇ 01 · AGENT SKILL", mono(23), .14, fill=v)
    sag = "AÇIK KAYNAK"
    aralikli(g, s(x1) - aralikli_gen(sag, mono(23, False), .14), s(65), sag, mono(23, False), .14, fill=GRI)
    g.rectangle([s(x0), s(87), s(x1), s(90) - 1], fill=MUREKKEP)
    g.text((s(x0 - 3), s(196)), "turkce-dogallastirici", font=serif(84, 620), fill=MUREKKEP, anchor="ls")
    fd = serif(36, 420)
    for i, satir in enumerate(["Türkçe metindeki yapay zekâ ve çeviri izini seçilen kipe göre temizler;",
                               "sayıları, terimleri, atıfları ve temkinli ifadeleri kodla korur."]):
        g.text((s(x0), s(278 + i * 50)), satir, font=fd, fill="#2A2B30", anchor="ls")
    # kullanılabildiği ortamlar: çerçeveli çipler
    cx = s(x0)
    for ad in ["CLAUDE CODE", "CODEX", "HERMES"]:
        fm = mono(23)
        w = aralikli_gen(ad, fm, .1)
        g.rectangle([cx, s(366), cx + w + s(32), s(414)], outline=MUREKKEP, width=s(2))
        aralikli(g, cx + s(16), s(398), ad, fm, .1, fill=MUREKKEP)
        cx += w + s(32) + s(16)
    g.rectangle([s(x0), s(450), s(x1), s(451.5)], fill=CIZGI)
    aralikli(g, s(x0), s(488), "GITHUB.COM/NOIRKRTX/TURKCE-DOGALLASTIRICI", mono(21, False), .06, fill=GRI)
    fm = mono(22)
    iw = aralikli_gen("@noirkrtx", fm, .06)
    ix = s(x1) - iw
    kapsul(im, ix - s(54), s(488) - s(8) - s(4), s(40), s(9))
    aralikli(g, ix, s(488), "@noirkrtx", fm, .06, fill=MUREKKEP)
    im.resize((KW, KH), Image.LANCZOS).save(yol, optimize=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", default=os.path.join(KOK, "banner.png"))
    ap.add_argument("--kart", default=os.path.join(KOK, "kart-dogallastirici.png"))
    a = ap.parse_args()
    ciz().save(a.o, optimize=True)
    print("yazıldı:", a.o)
    kart(a.kart)
    print("yazıldı:", a.kart)
