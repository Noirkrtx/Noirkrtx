"""NOIR profil banner'ının hareketli WebP'si (banner.py ile aynı çizim, kare kare).

Sıra: üst ve alt şerit baştan durur, NOIR soluk bir iz olarak görünür → 3 px mürekkep
çizgi soldan sağa çizilir → NOIR harf harf mürekkep gibi koyulaşır → alt satır soldan
açılır → seri işaretleri sırayla gelir. Son kare statik banner.png ile aynı çizimdir; animasyon bir kez oynar.

Kullanım:  python animasyon.py  [-o banner-hareketli.webp] [--fps 25]
Rastgelelik yok: aynı kod her seferinde aynı kareleri üretir.
"""
import argparse
import os

from PIL import ImageChops

import banner as B

KOK = os.path.dirname(os.path.abspath(__file__))
SURE = 3.4        # hareketli bölüm (sn)
HAYALET = 0.10    # ilk karede başlık soluk iz olarak durur: animasyonu oynatmayan
                  # görüntüleyicide (ilk kareyi gösteren) bile banner boş görünmez
BEKLE = 2.0       # son karede bekleme (sn); sonra durağan kalır


def durum(t):
    k = B.kademe
    return {
        "ust": 1,
        "cizgi": k(t, 0.10, 0.95),
        "baslik": [HAYALET + (1 - HAYALET) * k(t, 0.65 + .2 * i, 1.10 + .2 * i) for i in range(4)],
        "satir": k(t, 1.50, 2.40),
        "isaret": [k(t, 2.25 + .18 * i, 2.65 + .18 * i) for i in range(4)],
        "alt": 1,
    }


def uret(yol, fps):
    zemin = B.zemin()
    kareler, sureler = [], []
    n = int(SURE * fps)
    ms = round(1000 / fps)
    for i in range(n):
        im = B.ciz(durum(i / fps), _zemin=zemin)
        if kareler and not ImageChops.difference(im, kareler[-1]).getbbox():
            sureler[-1] += ms                     # aynı kareyi tekrarlama, süreyi uzat
            continue
        kareler.append(im)
        sureler.append(ms)
    son = B.ciz(_zemin=zemin)                     # statik banner ile birebir aynı
    kareler.append(son)
    sureler.append(int(BEKLE * 1000))
    kareler[0].save(yol, save_all=True, append_images=kareler[1:], duration=sureler,
                    loop=1, lossless=True, quality=100, method=4)
    return len(kareler), sum(sureler)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", default=os.path.join(KOK, "banner-hareketli.webp"))
    ap.add_argument("--fps", type=int, default=25)
    a = ap.parse_args()
    k, ms = uret(a.o, a.fps)
    print(f"yazıldı: {a.o} · {k} kare · {ms / 1000:.1f} sn · {os.path.getsize(a.o) / 1e6:.2f} MB")
