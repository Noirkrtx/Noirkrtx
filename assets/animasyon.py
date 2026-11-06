"""NOIR profil banner'ının hareketli WebP'si (banner.py ile aynı çizim, kare kare).

Sıra: sahne 1,035 yakınlıktan gözlerin ortasına doğru yavaşça 1,00'a oturur (kamera
geri çekilir; yüz geometrisine dokunan bir efekt yok) → gözlerde ince, sıcak bir parlama
yükselip söner → etiket, NOIR, alt satır ve imza soldan açılır. Son kare statik
banner.png ile aynı çizimdir (zoom 1, parlama 0); animasyon bir kez oynar.

Kullanım:  python animasyon.py  [-o banner-hareketli.webp] [--fps 20] [--kalite 82]
Rastgelelik yok: aynı kod her seferinde aynı kareleri üretir.
"""
import argparse
import os

import banner as B

KOK = os.path.dirname(os.path.abspath(__file__))
SURE = 4.2        # hareketli bölüm (sn)
BEKLE = 1.5       # son karede bekleme (sn); sonra durağan kalır


def kare(t):
    k = B.kademe
    zoom = 1.0 + 0.035 * (1 - k(t, 0.0, SURE))
    parla = k(t, 0.6, 1.5) * (1 - k(t, 1.9, 3.0))
    durum = {
        "etiket": k(t, 1.0, 1.8),
        "baslik": k(t, 1.3, 2.4),
        "satir": k(t, 2.0, 3.0),
        "alt": k(t, 2.7, 3.5),
    }
    return B.ciz(durum, zoom=zoom, parla=parla)


def uret(yol, fps, kalite):
    n = int(SURE * fps)
    ms = round(1000 / fps)
    kareler = [kare(i / fps) for i in range(n)]
    kareler.append(B.ciz())                       # statik banner ile aynı çizim
    sureler = [ms] * n + [int(BEKLE * 1000)]
    kareler[0].save(yol, save_all=True, append_images=kareler[1:], duration=sureler,
                    loop=1, lossless=False, quality=kalite, method=6)
    return len(kareler), sum(sureler)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", default=os.path.join(KOK, "banner-hareketli.webp"))
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--kalite", type=int, default=82)
    a = ap.parse_args()
    k, ms = uret(a.o, a.fps, a.kalite)
    print(f"yazıldı: {a.o} · {k} kare · {ms / 1000:.1f} sn · {os.path.getsize(a.o) / 1e6:.2f} MB")
