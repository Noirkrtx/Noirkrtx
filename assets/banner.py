"""NOIR GitHub profil banner'ı ve araç kartı (koyu, sıcak; NOIR karakterinin paleti).

Sahne (sahne.png, 1600x640) yazısız bir görseldir: onaylı NOIR portresi görsel referans
verilerek üretildi, yalnız göz içi ikinci bir yerel düzenlemeyle portreye eşlendi, sonra
2,5:1 kırpılıp ölçeklendi (esnetme yok). Bütün yazılar bu dosyada kodla dizilir; görsel
üretici modele yazı yazdırılmaz. Fontlar fonts/ klasöründen okunur (SIL OFL 1.1).

Kullanım:
    python banner.py                 # banner.png + kart-dogallastirici.png

ciz(durum, zoom, parla) animasyon.py tarafından kare kare çağrılır; argümansız çağrı
statik banner'ın son halidir.
"""
import argparse
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

KOK = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(KOK, "fonts")
SAHNE = os.path.join(KOK, "sahne.png")

W, H = 1600, 640          # çıktı boyutu
S = 2                     # yazı maskesi ölçeği (2x çizilip küçültülür, kenarlar yumuşar)

# Palet: portreden ölçülen renkler (zemin umber/kömür, gömlek fildişi, iris altını,
# iris çevresindeki kızıl halka ve saçtaki bordo tutam).
ZEMIN = "#14100C"
KREM = "#EFE4D2"
SOLUK = "#BBA88E"
SATIR_RENK = "#D2C2A8"
AMBER = "#E0A43C"
KIZIL = "#A8321E"
CIZGI = "#4A3A2B"

ODAK = (1145, 271)        # iki gözün ortası (sahne.png px); yakınlaşma bu noktaya doğru
GOZLER = ((1098, 281), (1192, 261))

SON = {"etiket": 1, "baslik": 1, "satir": 1, "alt": 1}


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


def serif(px, w=560):
    return font("Newsreader-VF.ttf", px, w)


def italik(px, w=400):
    return font("Newsreader-Italic-VF.ttf", px, w)


def mono(px, kalin=True):
    return font("IBMPlexMono-SemiBold.ttf" if kalin else "IBMPlexMono-Medium.ttf", px)


def kademe(t, a, b):
    """t'yi [a,b] aralığında 0..1'e eşler; yumuşak (smoothstep)."""
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


# ── çizim yardımcıları ─────────────────────────────────────────────────────
class Tuval:
    """1x görüntü üstüne 2x çizilmiş maskeyle yarı saydam boyama."""

    def __init__(self, im):
        self.im = im.copy()

    def boya(self, renk, maske_ciz, alfa=1.0, wipe=None):
        if alfa <= 0:
            return
        m = Image.new("L", (s(W), s(H)), 0)
        maske_ciz(ImageDraw.Draw(m))
        if wipe is not None:
            m = ImageChops.multiply(m, wipe)
        m = m.resize(self.im.size, Image.LANCZOS)
        if alfa < 1:
            m = m.point(lambda v: int(v * alfa))
        self.im.paste(renk, (0, 0), m)


def aralikli(d, x, y, metin, f, takip_em, fill=255, anchor="ls"):
    """Harf aralıklı (letter-spacing) yazı; bitiş x'ini döndürür (2x px)."""
    tk = f.size * takip_em
    for ch in metin:
        d.text((x, y), ch, font=f, fill=fill, anchor=anchor)
        x += f.getlength(ch) + tk
    return x


def aralikli_gen(metin, f, takip_em):
    return sum(f.getlength(c) for c in metin) + f.size * takip_em * (len(metin) - 1)


def wipe_maske(x0, x1, p, yumusak=70):
    """p∈[0,1]: x0→x1 (2x px) arası soldan sağa açılan yatay maske."""
    w, h = s(W), s(H)
    on = x0 + (x1 - x0 + s(yumusak)) * p
    satir = Image.new("L", (w, 1))
    px = satir.load()
    for x in range(w):
        v = (on - x) / s(yumusak)
        px[x, 0] = int(255 * max(0.0, min(1.0, v)))
    return satir.resize((w, h))


def kapsul(t, kx, ky, kw, kh, alfa=1.0):
    """İmzadan önceki iki renkli kapsül: sol amber (iris), sağ kızıl (halka/saç tutamı); 2x px."""
    orta = kx + kw // 2
    for j, renk in enumerate((AMBER, KIZIL)):
        def m(g, j=j):
            g.rounded_rectangle([kx, ky, kx + kw, ky + kh], radius=kh // 2, fill=255)
            g.rectangle([orta, ky, kx + kw, ky + kh] if j == 0 else [kx, ky, orta - 1, ky + kh], fill=0)
        t.boya(renk, m, alfa)


# ── sahne katmanları ───────────────────────────────────────────────────────
_sahne = None


def sahne():
    global _sahne
    if _sahne is None:
        im = Image.open(SAHNE).convert("RGB")
        if im.size != (W, H):
            raise SystemExit(f"sahne.png {im.size}; beklenen {(W, H)}")
        _sahne = im
    return _sahne


def _pencere(z):
    fx, fy = ODAK
    w, h = W / z, H / z
    x0 = min(max(fx - fx / z, 0), W - w)
    y0 = min(max(fy - fy / z, 0), H - h)
    return x0, y0, w, h


def yakinlas(im, z):
    """ODAK noktasına doğru z kat yakınlaşma (z ≥ 1); en-boy oranı korunur."""
    if z <= 1.0001:
        return im
    x0, y0, w, h = _pencere(z)
    return im.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BICUBIC)


def nokta(p, z):
    """Sahne noktasının z yakınlaşmasındaki yeri."""
    if z <= 1.0001:
        return p
    x0, y0, _, _ = _pencere(z)
    return ((p[0] - x0) * z, (p[1] - y0) * z)


_kar = None


def karartma_maskesi():
    """Yazı alanının arkası: soldan sağa azalan yumuşak karartma + hafif alt kenar."""
    global _kar
    if _kar is None:
        sutun = [1 - kademe(x, 0, 0.60 * W) for x in range(W)]
        satir = [kademe(y, 0.70 * H, H) * 0.35 for y in range(H)]
        m = Image.new("L", (W, H), 0)
        m.putdata([int(255 * min(1.0, 0.52 * u + v * (1 - 0.5 * u)))
                   for v in satir for u in sutun])
        _kar = m
    return _kar


def parilti(im, g, z=1.0):
    """Gözlerde ince sıcak parlama (yüz geometrisine dokunmaz); g=0 iken görüntü değişmez."""
    if g <= 0:
        return im
    k = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(k)
    for p in GOZLER:
        x, y = nokta(p, z)
        r = 9 * z
        d.ellipse([x - r, y - r * .62, x + r, y + r * .62], fill=int(115 * g))
    k = k.filter(ImageFilter.GaussianBlur(5 * z))
    renk = Image.new("RGB", (W, H), AMBER)
    return ImageChops.add(im, ImageChops.multiply(renk, Image.merge("RGB", (k, k, k))))


# ── banner ─────────────────────────────────────────────────────────────────
SATIR = "Türkçe yapay zeka araçları ve okuma notları"
ETIKET = "ARAÇLAR · SKILL'LER · OKUMA NOTLARI"   # elle büyük harf: "skill" İngilizce, İ almaz
X0 = 92


def ciz(durum=None, zoom=1.0, parla=0.0):
    """durum: SON anahtarlarıyla ilerleme (0..1). zoom ≥ 1, parla 0..1. Argümansız = statik son hal."""
    d = dict(SON, **(durum or {}))
    im = yakinlas(sahne(), zoom)
    im = parilti(im, parla, zoom)
    im = Image.composite(Image.new("RGB", (W, H), ZEMIN), im, karartma_maskesi())
    t = Tuval(im)

    # etiket satırı: kızıl kısa çizgi + amber mono
    e = d["etiket"]
    if e > 0:
        y = 188
        t.boya(KIZIL, lambda g: g.rectangle([s(X0), s(y - 9), s(X0 + 26), s(y - 5)], fill=255), e)
        fm = mono(20)
        bx = s(X0 + 42)
        wm = None if e >= 1 else wipe_maske(bx, bx + aralikli_gen(ETIKET, fm, .16), e)
        t.boya(AMBER, lambda g: aralikli(g, bx, s(y), ETIKET, fm, .16), 1, wm)

    # başlık
    b = d["baslik"]
    if b > 0:
        f = serif(204, 540)
        bx, by = s(X0 - 8), s(388)
        wm = None if b >= 1 else wipe_maske(bx, bx + aralikli_gen("NOIR", f, .02), b, yumusak=120)
        t.boya(KREM, lambda g: aralikli(g, bx, by, "NOIR", f, .02), 1, wm)

    # alt satır
    st = d["satir"]
    if st > 0:
        fi = italik(38, 430)
        sx = s(X0)
        wm = None if st >= 1 else wipe_maske(sx, sx + fi.getlength(SATIR), st)
        t.boya(SATIR_RENK, lambda g: g.text((sx, s(452)), SATIR, font=fi, fill=255, anchor="ls"), 1, wm)

    # alt imza: kısa çizgi, iki renkli kapsül, @noirkrtx
    al = d["alt"]
    if al > 0:
        ya = 562
        t.boya(CIZGI, lambda g: g.rectangle([s(X0), s(514), s(X0) + s(300) * al, s(515.5)], fill=255))
        kw, kh = s(36), s(8)
        kapsul(t, s(X0), s(ya) - s(7) - kh // 2, kw, kh, al)
        t.boya(KREM, lambda g: aralikli(g, s(X0 + 52), s(ya), "@noirkrtx", mono(22), .06), al)

    return t.im


# ── araç kartı (README'deki kart; karakter yok) ────────────────────────────
def kart(yol, no="01", tur="AGENT SKILL", ad="turkce-dogallastirici",
         aciklama=("Türkçe metindeki yapay zeka ve çeviri izini seçilen kipe göre temizler;",
                   "sayıları, terimleri, atıfları ve temkinli ifadeleri kodla korur."),
         etiketler=("CLAUDE CODE", "CODEX", "HERMES")):
    KW, KH = 1600, 520
    zem = Image.new("RGB", (KW, KH), ZEMIN)
    # sağ üstten gelen çok hafif amber ışık (portredeki ışık yönü)
    isik = Image.new("L", (KW, KH), 0)
    ImageDraw.Draw(isik).ellipse([KW - 700, -520, KW + 500, 420], fill=60)
    isik = isik.filter(ImageFilter.GaussianBlur(160))
    zem = Image.composite(Image.new("RGB", (KW, KH), "#5A3A1E"), zem, isik)

    big = zem.resize((s(KW), s(KH)), Image.BICUBIC)
    g = ImageDraw.Draw(big)
    x0, x1 = 72, KW - 72
    g.rectangle([s(x0), s(56), s(x0 + 26), s(60)], fill=KIZIL)
    aralikli(g, s(x0 + 42), s(65), f"ARAÇ {no} · {tur}", mono(23), .14, fill=AMBER)
    sag = "AÇIK KAYNAK"
    aralikli(g, s(x1) - aralikli_gen(sag, mono(23, False), .14), s(65), sag, mono(23, False), .14, fill=SOLUK)
    g.rectangle([s(x0), s(88), s(x1), s(89.5)], fill=CIZGI)
    g.text((s(x0 - 3), s(196)), ad, font=serif(84, 560), fill=KREM, anchor="ls")
    fd = serif(36, 400)
    for i, satir in enumerate(aciklama):
        g.text((s(x0), s(278 + i * 50)), satir, font=fd, fill="#D3C5AF", anchor="ls")
    cx = s(x0)
    for et in etiketler:
        fm = mono(23)
        w = aralikli_gen(et, fm, .1)
        g.rectangle([cx, s(366), cx + w + s(32), s(414)], outline="#8A6A3E", width=s(2))
        aralikli(g, cx + s(16), s(398), et, fm, .1, fill=AMBER)
        cx += w + s(32) + s(16)
    g.rectangle([s(x0), s(450), s(x1), s(451.5)], fill=CIZGI)
    aralikli(g, s(x0), s(488), "GITHUB.COM/NOIRKRTX/" + ad.upper(), mono(21, False), .06, fill=SOLUK)
    fm = mono(22)
    iw = aralikli_gen("@noirkrtx", fm, .06)
    ix = s(x1) - iw
    kx, ky, kw, kh = ix - s(52), s(488) - s(7) - s(4), s(36), s(8)
    orta = kx + kw // 2
    g.rounded_rectangle([kx, ky, kx + kw, ky + kh], radius=kh // 2, fill=AMBER)
    m = Image.new("L", big.size, 0)
    gm = ImageDraw.Draw(m)
    gm.rounded_rectangle([kx, ky, kx + kw, ky + kh], radius=kh // 2, fill=255)
    gm.rectangle([kx, ky, orta - 1, ky + kh], fill=0)
    big.paste(KIZIL, (0, 0), m)
    aralikli(g, ix, s(488), "@noirkrtx", fm, .06, fill=KREM)
    big.resize((KW, KH), Image.LANCZOS).save(yol, optimize=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", default=os.path.join(KOK, "banner.png"))
    ap.add_argument("--kart", default=os.path.join(KOK, "kart-dogallastirici.png"))
    a = ap.parse_args()
    ciz().save(a.o, optimize=True)
    print("yazıldı:", a.o)
    kart(a.kart)
    print("yazıldı:", a.kart)
    kart(os.path.join(KOK, "kart-harf-bekcisi.png"), no="02", tur="HOOK · SKILL", ad="tr-harf-bekcisi",
         aciklama=("Ajanların dosyaya yazarken bozduğu Türkçe harfleri bulur: düşen harfler",
                   "(cok, icin) ve bozuk kodlama (TÃ¼rkÃ§e). Güvenli olanları onarır."),
         etiketler=("CLAUDE CODE", "CODEX", "HERMES", "PRE-COMMIT"))
    print("yazıldı: kart-harf-bekcisi.png")
