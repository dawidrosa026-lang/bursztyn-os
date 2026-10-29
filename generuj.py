#!/usr/bin/env python3
"""Bursztyn OS – generator treści strony (bez zależności, tylko Python 3).

Czyta:  manifest.json, data/wydania.json, data/archiwum.json, data/ogloszenia.json, data/strona.json
Pisze:  feed.xml (RSS 2.0) oraz statyczne fragmenty HTML między znacznikami
        <!-- GEN:NAZWA --> ... <!-- /GEN:NAZWA --> w plikach:
          index.html        (GEN:NAJNOWSZE – dwa najnowsze ogłoszenia)
          pobierz.html      (GEN:WYDANIA   – karty wydań)
          pobierz.html      (GEN:ARCHIWUM  – „Archiwum wersji”: starsze wydania + „Pytania i odpowiedzi”)
          aktualnosci.html  (GEN:WPISY     – wszystkie ogłoszenia)
          o-projekcie.html  (GEN:TWORCA    – sekcje „Twórca” i „Współtwórca”)
          wszystkie *.html  (GEN:AUTOR – <meta name="author">,
                             GEN:STOPKA-TWORCA – linia o twórcy w stopce)
Dzięki temu strona działa także bez JavaScriptu.

Użycie:  python3 generuj.py
"""
import email.utils, html, json, pathlib, re, sys
from datetime import datetime, timezone

KAT = pathlib.Path(__file__).resolve().parent
MIESIACE = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca",
            "sierpnia", "września", "października", "listopada", "grudnia"]
e = lambda s: html.escape(str(s or ""), quote=True)


def wczytaj(nazwa):
    with open(KAT / nazwa, encoding="utf-8") as f:
        return json.load(f)


def data_pl(iso):
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{d.day} {MIESIACE[d.month - 1]} {d.year}"
    except (ValueError, TypeError):
        return iso or ""


def slug(t):
    t = t.lower().translate(str.maketrans("ąćęłńóśźż", "acelnoszz"))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


# ---------- ogłoszenia ----------
def wpisy():
    """Ogłoszenia ręczne + wpisy o wydaniach z manifest.json (pole 'historia')."""
    m = wczytaj("manifest.json")
    lista = []
    for w in wczytaj("data/ogloszenia.json").get("wpisy", []):
        lista.append({"id": w.get("id") or slug(w["tytul"]), "tytul": w["tytul"], "data": w.get("data", ""),
                      "rodzaj": "Ogłoszenie", "akapity": w.get("tresc", []), "zmiany": [], "link": w.get("link", "")})
    for h in m.get("historia", []):
        biezaca = h.get("wersja") == m.get("wersja")
        tytul = m.get("nazwa") if biezaca and m.get("nazwa") else f"Bursztyn OS {h.get('wersja')}"
        if biezaca:
            akapity, zmiany = h.get("zmiany", []), m.get("zmiany", [])
        else:
            akapity, zmiany = [], h.get("zmiany", [])
        lista.append({"id": "wydanie-" + slug(str(h.get("wersja"))), "tytul": f"Wydanie: {tytul}",
                      "data": h.get("data", ""), "rodzaj": "Wydanie", "akapity": akapity,
                      "zmiany": zmiany, "link": m.get("pobierz", "") if biezaca else ""})
    # najnowsze na górze; przy tej samej dacie ogłoszenie przed listą zmian
    lista.sort(key=lambda w: (w["data"], w["rodzaj"] == "Ogłoszenie"), reverse=True)
    return lista


def html_wpis(w, skrot=False, poziom="h3"):
    adres = f"aktualnosci.html#{e(w['id'])}"
    s = [f'<article class="karta wpis" id="{e(w["id"])}">',
         f'<time datetime="{e(w["data"])}">{e(data_pl(w["data"]))}</time><span class="rodzaj">{e(w["rodzaj"])}</span>',
         f'<{poziom}><a href="{adres}">{e(w["tytul"])}</a></{poziom}>']
    akapity = w["akapity"][:1] if skrot else w["akapity"]
    s += [f"<p>{e(a)}</p>" for a in akapity]
    if w["zmiany"] and not skrot:
        s.append('<p><strong>Co nowego:</strong></p><ul>' + "".join(f"<li>{e(z)}</li>" for z in w["zmiany"]) + "</ul>")
    elif w["zmiany"] and skrot:
        s.append(f"<p>{len(w['zmiany'])} nowości w tym wydaniu.</p>")
    if w.get("link") and not skrot:
        s.append(f'<p><a class="przycisk maly" href="{e(w["link"])}">Pobierz</a></p>')
    if skrot:
        s.append(f'<p><a href="{adres}">Czytaj dalej →</a></p>')
    s.append("</article>")
    return "\n".join(s)


# ---------- wydania ----------
def html_wydanie(w):
    gotowe = w.get("status") == "gotowe"
    wk = '<span class="wkrotce">wkrótce</span>'
    znaczek = ('<span class="znaczek gotowe">Gotowe</span>' if gotowe
               else '<span class="znaczek w-przygotowaniu">W przygotowaniu</span>')
    sha = (f'<div class="sha"><code>{e(w["sha256"])}</code>'
           f'<button class="przycisk drugi maly kopiuj" type="button" data-kopiuj="{e(w["sha256"])}" hidden>Kopiuj</button></div>'
           if w.get("sha256") else wk)
    url = w.get("url") or "#"
    if url == "#":
        pobierz = '<span class="przycisk wylaczony" aria-disabled="true" title="Plik nie jest jeszcze nigdzie opublikowany">⤓ Link wkrótce</span>'
    else:
        pobierz = f'<a class="przycisk" href="{e(url)}">⤓ Pobierz ISO</a>'
    s = [f'<article class="karta wydanie{" polecane" if gotowe else ""}" id="{e(w["id"])}">',
         '<div class="wydanie-gora"><img src="img/logo.svg" alt="" width="54" height="54">',
         f'<div><h3>{e(w["nazwa"])}</h3>{znaczek}</div></div>',
         f'<p class="opis">{e(w.get("opis"))}</p>',
         '<ul class="lista-tagi" aria-label="Aplikacje">' + "".join(f"<li>{e(a)}</li>" for a in w.get("aplikacje", [])) + "</ul>",
         "<dl>",
         f'<dt>Edycja</dt><dd>{e(w.get("edycja"))}</dd>',
         f'<dt>Data wydania</dt><dd>{e(data_pl(w["data"])) if w.get("data") else wk}</dd>',
         f'<dt>Plik</dt><dd>{"<code>" + e(w["plik"]) + "</code>" if w.get("plik") else wk}</dd>',
         f'<dt>Rozmiar</dt><dd>{e(w["rozmiar"]) if w.get("rozmiar") else wk}</dd>',
         f"<dt>SHA-256</dt><dd>{sha}</dd>",
         '<dt>Wymagania</dt><dd><ul class="wym">' + "".join(f"<li>{e(x)}</li>" for x in w.get("wymagania", [])) + "</ul></dd>",
         "</dl>",
         f'<div class="akcje">{pobierz}</div>',
         "</article>"]
    return "\n".join(s)


# ---------- archiwum wersji ----------
REPO_WYD = "https://github.com/dawidrosa026-lang/bursztyn-os/releases"


def wkl(v):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.\-]", str(v)))


def rozmiar_gb(b):
    return f"{b / 1e9:.2f}".replace(".", ",") + " GB"


def migawka(wydania, manifest):
    """Zapis aktualnego (najnowszego gotowego) wydania na potrzeby archiwum."""
    got = [w for w in wydania if w.get("status") == "gotowe" and w.get("wersja")]
    if not got:
        return None
    wer = max((w["wersja"] for w in got), key=wkl)
    kryptonim = ""
    if manifest.get("wersja") == wer:
        m = re.search(r"„([^”]+)”", manifest.get("nazwa", ""))
        kryptonim = m.group(1) if m else ""
    pliki = []
    for w in got:
        if w["wersja"] != wer:
            continue
        b = re.search(r"\(([\d  ]+)\s*bajt", w.get("rozmiar", ""))
        pliki.append({"edycja": w.get("edycja", ""), "plik": w.get("plik", ""),
                      "rozmiar_bajtow": int(re.sub(r"\D", "", b.group(1))) if b else 0,
                      "url": w.get("url", ""), "url_sha256": w.get("url_sha256", "")})
    dane = [w.get("data") for w in got if w["wersja"] == wer and w.get("data")]
    return {"wersja": wer, "nazwa": f"Bursztyn OS {wer}", "kryptonim": kryptonim,
            "data": dane[0] if dane else "", "url": f"{REPO_WYD}/tag/v{wer}", "pliki": pliki}


def aktualizuj_archiwum(wydania, manifest):
    """Gdy pojawia się nowsze gotowe wydanie, poprzednie „bieżące” trafia do archiwum (automatycznie)."""
    sciezka = KAT / "data/archiwum.json"
    ar = wczytaj("data/archiwum.json")
    nowe = migawka(wydania, manifest)
    if nowe:
        stare = ar.get("biezace")
        if stare and stare.get("wersja") and wkl(nowe["wersja"]) > wkl(stare["wersja"]):
            if all(x.get("wersja") != stare["wersja"] for x in ar["wydania"]):
                ar["wydania"].append(stare)
                print(f"  archiwum: wersja {stare['wersja']} przeniesiona do archiwum")
        if not stare or wkl(nowe["wersja"]) >= wkl(stare.get("wersja", "0")):
            if stare and stare.get("wersja") == nowe["wersja"]:
                for k in ("kryptonim", "w_skrocie"):
                    if not nowe.get(k):
                        nowe[k] = stare.get(k, "")
            ar["biezace"] = nowe
    ar["wydania"].sort(key=lambda x: wkl(x["wersja"]), reverse=True)
    sciezka.write_text(json.dumps(ar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ar["wydania"]


def html_pytania(ar, aktualna):
    """„Pytania i odpowiedzi” pod archiwum – <details> jak FAQ w o-projekcie.html. HTML odpowiedzi pochodzi z data/archiwum.json."""
    zam = lambda t: t.replace("{AKTUALNA}", e(aktualna))
    wszystkie = sorted(ar["wydania"] + ([ar["biezace"]] if ar.get("biezace") else []), key=lambda x: wkl(x["wersja"]), reverse=True)
    s = ['<div class="archiwum-faq">', '<h3>Pytania i odpowiedzi</h3>', '<div class="archiwum-faq-lista">']
    for q in ar.get("pytania", []):
        s.append(f'<details class="karta"><summary>{zam(e(q["pytanie"]))}</summary><div>')
        for a in q.get("odpowiedz", []):  # akapit zwykły → <p>; wpis zaczynający się od „<” (np. <pre>) wstawiany bez zmian
            s.append(zam(a) if a.lstrip().startswith("<") else f"<p>{zam(a)}</p>")
        if q.get("rodzaj") == "wersje":
            s.append('<ul class="archiwum-wersje">')
            for w in wszystkie:
                kr = f' „{e(w["kryptonim"])}”' if w.get("kryptonim") else ""
                opis = f' – {e(w["w_skrocie"])}' if w.get("w_skrocie") else ""
                s.append(f'<li><strong>{e(w["wersja"])}{kr}</strong> ({e(data_pl(w["data"]))}){opis}</li>')
            s.append("</ul>")
        s.append("</div></details>")
    s += ["</div>", "</div>"]
    return "\n".join(s)


def html_archiwum(lista, aktualna):
    s = ['<div class="sekcja-naglowek"><span class="etykieta">Archiwum</span><h2>Archiwum wersji</h2>',
         f'<p>Aktualna wersja to <strong>{e(aktualna)}</strong> – to ją polecamy i to ona dostaje poprawki. '
         'Starsze wydania są tu wyłącznie w celach archiwalnych: nie są już aktualizowane, więc nie instaluj ich na co dzień.</p></div>']
    if not lista:
        return "\n".join(s + ["<p>Archiwum jest na razie puste.</p>"])
    s.append('<div class="siatka dwie archiwum-lista">')
    for r in lista:
        nazwa = r["nazwa"] + (f" „{r['kryptonim']}”" if r.get("kryptonim") else "")
        s += [f'<article class="karta archiwum-wydanie" id="archiwum-{e(slug(r["wersja"]))}">',
              f'<h3>{e(nazwa)}</h3>',
              f'<p class="archiwum-data"><time datetime="{e(r["data"])}">{e(data_pl(r["data"]))}</time></p>',
              '<ul class="archiwum-pliki">']
        for f in r.get("pliki", []):
            sha = f' · <a href="{e(f["url_sha256"])}">suma SHA-256</a>' if f.get("url_sha256") else ""
            rozm = f' <span class="archiwum-rozmiar">({e(rozmiar_gb(f["rozmiar_bajtow"]))})</span>' if f.get("rozmiar_bajtow") else ""
            s.append(f'<li><span class="archiwum-edycja">{e(f["edycja"])}</span> '
                     f'<a href="{e(f["url"])}">⤓ {e(f["plik"])}</a>{rozm}{sha}</li>')
        s += ["</ul>", f'<p class="archiwum-link"><a href="{e(r["url"])}">Strona wydania na GitHubie →</a></p>', "</article>"]
    s.append("</div>")
    return "\n".join(s)


# ---------- twórca ----------
def html_autor(t):
    return f'<meta name="author" content="{e(t["imie"])}">'


def html_stopka_tworca(t, w=None):
    s = (f'<p class="tworca-stopka">Bursztyn OS – twórca: '
         f'<a href="{e(t["url"])}" rel="author">{e(t["imie"])}</a>')
    if w:
        s += f' · współtwórca: {e(w["imie"])}'
    return s + '</p>'


def html_tworca(t, w=None):
    karta_t = [
        '    <div class="karta tworca">']
    if t.get("zdjecie"):
        karta_t.append(f'      <picture><source type="image/webp" srcset="{e(t["zdjecie"])}.webp">'
                       f'<img class="tworca-foto" src="{e(t["zdjecie"])}.jpg" width="600" height="600" loading="lazy" '
                       f'alt="{e(t.get("zdjecie_alt") or t["imie"])}"></picture>')
    karta_t += [
        '      <span class="etykieta">Twórca</span>',
        f'      <h2>{e(t["imie"])}</h2>',
        f'      <p class="rola">{e(t["rola"][:1].upper() + t["rola"][1:])}</p>',
        f'      <p>Bursztyn OS stworzył {e(t["imie"])}. To jego projekt – rozwija go i wydaje kolejne wersje.</p>',
        f'      <p><a class="przycisk drugi maly" href="{e(t["url"])}" rel="author">GitHub: {e(t["github"])}</a></p>',
        '    </div>']
    if not w:
        return "\n".join(['<section class="sekcja" id="tworca" style="padding-top:0">',
                          '  <div class="kontener" style="max-width:860px">'] + karta_t + ['  </div>', '</section>'])
    karta_w = [
        '    <div class="karta tworca wspoltworca">']
    if w.get("zdjecie"):
        karta_w.append(f'      <picture><source type="image/webp" srcset="{e(w["zdjecie"])}.webp">'
                       f'<img class="tworca-foto" src="{e(w["zdjecie"])}.jpg" width="400" height="400" loading="lazy" '
                       f'alt="{e(w.get("zdjecie_alt") or w["imie"])}"></picture>')
    karta_w += [
        '      <span class="etykieta">Współtwórca</span>',
        f'      <h2>{e(w["imie"])}</h2>',
        f'      <p class="rola">{e(w["rola"][:1].upper() + w["rola"][1:])}</p>',
        f'      <p>{e(w["opis"])}</p>',
        '    </div>']
    return "\n".join(['<section class="sekcja" id="tworca" style="padding-top:0">',
                      '  <div class="kontener" style="max-width:860px">',
                      '    <div class="siatka dwie">'] + karta_t + karta_w + ['    </div>', '  </div>', '</section>'])


# ---------- RSS ----------
def rss(lista, strona):
    adres = strona.get("adres", "").rstrip("/")
    tw = strona.get("tworca") or {}
    autor = f"{tw['email']} ({tw['imie']})" if tw.get("email") else ""
    autor_xml = [f"<managingEditor>{e(autor)}</managingEditor>",
                 f"<webMaster>{e(autor)}</webMaster>"] if autor else []
    def rfc(d):
        try:
            return email.utils.format_datetime(datetime.strptime(d, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc))
        except ValueError:
            return ""
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
         f"<title>{e(strona.get('tytul', 'Bursztyn OS'))} – Aktualności</title>",
         f"<link>{e(adres)}/aktualnosci.html</link>",
         f'<atom:link href="{e(adres)}/feed.xml" rel="self" type="application/rss+xml"/>',
         f"<description>{e(strona.get('opis', ''))}</description>", "<language>pl</language>"] + autor_xml
    if tw.get("imie"):
        wsp = strona.get("wspoltworca") or {}
        x.append(f"<copyright>Bursztyn OS – twórca: {e(tw['imie'])}"
                 + (f" · współtwórca: {e(wsp['imie'])}" if wsp.get("imie") else "") + "</copyright>")
    if lista:
        x.append(f"<lastBuildDate>{rfc(lista[0]['data'])}</lastBuildDate>")
    for w in lista:
        tresc = "".join(f"<p>{e(a)}</p>" for a in w["akapity"])
        if w["zmiany"]:
            tresc += "<ul>" + "".join(f"<li>{e(z)}</li>" for z in w["zmiany"]) + "</ul>"
        link = f"{adres}/aktualnosci.html#{w['id']}"
        x += ["<item>", f"<title>{e(w['tytul'])}</title>", f"<link>{e(link)}</link>",
              f'<guid isPermaLink="true">{e(link)}</guid>', f"<pubDate>{rfc(w['data'])}</pubDate>",
              f"<category>{e(w['rodzaj'])}</category>"] + ([f"<author>{e(autor)}</author>"] if autor else []) + [
              f"<description>{e(tresc)}</description>", "</item>"]
    x += ["</channel>", "</rss>", ""]
    return "\n".join(x)


def wstaw(plik, znacznik, tresc):
    p = KAT / plik
    t = p.read_text(encoding="utf-8")
    wz = re.compile(rf"(<!-- GEN:{znacznik} -->)(.*?)(<!-- /GEN:{znacznik} -->)", re.S)
    if not wz.search(t):
        sys.exit(f"Brak znaczników GEN:{znacznik} w {plik}")
    t = wz.sub(lambda mm: f"{mm.group(1)}\n{tresc}\n{mm.group(3)}", t)
    p.write_text(t, encoding="utf-8")
    print(f"  {plik}: GEN:{znacznik} zaktualizowany")


def main():
    lista = wpisy()
    wydania = wczytaj("data/wydania.json")["wydania"]
    strona = wczytaj("data/strona.json")
    wstaw("aktualnosci.html", "WPISY", "\n".join(html_wpis(w, poziom="h2") for w in lista))
    wstaw("index.html", "NAJNOWSZE", "\n".join(html_wpis(w, skrot=True) for w in lista[:2]))
    wstaw("pobierz.html", "WYDANIA", "\n".join(html_wydanie(w) for w in wydania))
    archiwum = aktualizuj_archiwum(wydania, wczytaj("manifest.json"))
    aktualna = (wczytaj("data/archiwum.json").get("biezace") or {}).get("wersja", "")
    wstaw("pobierz.html", "ARCHIWUM", html_archiwum(archiwum, aktualna) + "\n" + html_pytania(wczytaj("data/archiwum.json"), aktualna))
    tw = strona.get("tworca")
    if tw:
        for plik in sorted(KAT.glob("*.html")):
            wstaw(plik.name, "AUTOR", html_autor(tw))
            wstaw(plik.name, "STOPKA-TWORCA", html_stopka_tworca(tw, strona.get("wspoltworca")))
        wstaw("o-projekcie.html", "TWORCA", html_tworca(tw, strona.get("wspoltworca")))
    (KAT / "feed.xml").write_text(rss(lista, strona), encoding="utf-8")
    print(f"  feed.xml: {len(lista)} wpisów")
    if "example" in strona.get("adres", ""):
        print("UWAGA: data/strona.json 'adres' to wciąż adres przykładowy – uzupełnij przed publikacją.")


if __name__ == "__main__":
    main()
