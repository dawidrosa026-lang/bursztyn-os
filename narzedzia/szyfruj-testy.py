#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Szyfruje treść strony dla testerów (AES-256-GCM, PBKDF2-SHA256).

Hasło wyłącznie ze zmiennej środowiskowej BURSZTYN_TESTER_PASSWORD.
Nigdy nie wypisuje hasła. Użycie:

  BURSZTYN_TESTER_PASSWORD=… python3 narzedzia/szyfruj-testy.py \\
      /sciezka/do/tresc.html testy.html
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITERACJE = 600000
SOL_BAJTY = 16
IV_BAJTY = 12
KLUCZ_BAJTY = 32


def _haslo() -> bytes:
    wartosc = os.environ.get("BURSZTYN_TESTER_PASSWORD")
    if wartosc is None or wartosc == "":
        sys.exit("Brak zmiennej środowiskowej BURSZTYN_TESTER_PASSWORD.")
    return wartosc.encode("utf-8")


def szyfruj(tresc: bytes, haslo: bytes) -> dict:
    sol = secrets.token_bytes(SOL_BAJTY)
    iv = secrets.token_bytes(IV_BAJTY)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=KLUCZ_BAJTY, salt=sol, iterations=ITERACJE)
    klucz = kdf.derive(haslo)
    dane = AESGCM(klucz).encrypt(iv, tresc, None)
    return {
        "kdf": "PBKDF2-SHA256",
        "iter": ITERACJE,
        "sol": base64.b64encode(sol).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "dane": base64.b64encode(dane).decode("ascii"),
    }


def deszyfruj(pakiet: dict, haslo: bytes) -> bytes:
    if pakiet.get("kdf") != "PBKDF2-SHA256":
        raise ValueError("nieznany kdf")
    iteracje = int(pakiet["iter"])
    if iteracje < 600000:
        raise ValueError("za mało iteracji")
    sol = base64.b64decode(pakiet["sol"])
    iv = base64.b64decode(pakiet["iv"])
    dane = base64.b64decode(pakiet["dane"])
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=KLUCZ_BAJTY, salt=sol, iterations=iteracje)
    klucz = kdf.derive(haslo)
    return AESGCM(klucz).decrypt(iv, dane, None)


SZABLON = """<!doctype html>
<html lang="pl" class="bez-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dla testerów – Bursztyn OS</title>
<meta name="description" content="Strefa dla testerów Bursztyn OS. Wejście wymaga hasła.">
<meta name="robots" content="noindex,nofollow">
<!-- GEN:AUTOR -->
<meta name="author" content="Dawid Rosa">
<!-- /GEN:AUTOR -->
<meta name="theme-color" content="#140d07">
<meta property="og:title" content="Dla testerów – Bursztyn OS">
<meta property="og:description" content="Strefa dla testerów Bursztyn OS. Wejście wymaga hasła.">
<meta property="og:image" content="https://dawidrosa026-lang.github.io/bursztyn-os/img/zrzuty/ekran-powitalny.jpg">
<link rel="canonical" href="https://dawidrosa026-lang.github.io/bursztyn-os/testy.html">
<meta property="og:url" content="https://dawidrosa026-lang.github.io/bursztyn-os/testy.html">
<meta property="og:type" content="website">
<meta property="og:locale" content="pl_PL">
<link rel="icon" href="img/logo.svg" type="image/svg+xml">
<link rel="icon" href="img/favicon.png" type="image/png" sizes="64x64">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="Bursztyn OS – Aktualności" href="feed.xml">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<a class="pomin" href="#tresc">Przejdź do treści</a>
<header class="naglowek">
  <div class="kontener">
    <a class="marka" href="index.html"><img src="img/logo.svg" alt="" width="34" height="34">Bursztyn <span>OS</span></a>
    <button class="menu-przelacznik" type="button" aria-expanded="false" aria-controls="nawigacja">☰ Menu</button>
    <nav class="nawigacja" id="nawigacja" aria-label="Główna nawigacja"><a href="index.html">Start</a><a href="pobierz.html">Pobierz</a><a href="aktualnosci.html">Aktualności</a><a href="o-projekcie.html">O projekcie</a><a href="testy.html" aria-current="page">Dla testerów</a></nav>
  </div>
</header>
<main id="tresc">
<section class="strona-tytul"><div class="kontener">
  <span class="etykieta">Dla testerów</span><h1>Dla testerów</h1>
  <p>Ta część strony jest przeznaczona tylko dla osób, które dostały hasło od twórcy projektu.</p>
</div></section>
<section class="sekcja" style="padding-top:8px">
  <div class="kontener">
    <form class="formularz-testerow karta" id="formularz-testerow" autocomplete="on">
      <label for="haslo-testerow">Hasło dla testerów</label>
      <input id="haslo-testerow" name="haslo" type="password" autocomplete="current-password" required>
      <label class="zapamietaj"><input id="zapamietaj-testerow" type="checkbox"> Zapamiętaj na tym urządzeniu</label>
      <p class="blad" id="blad-testerow" role="alert" hidden>Nieprawidłowe hasło</p>
      <button class="przycisk" type="submit">Otwórz</button>
    </form>
    <div id="tresc-testerow" hidden></div>
  </div>
</section>
</main>
<footer class="stopka">
  <div class="kontener">
    <div>
      <a class="marka" href="index.html"><img src="img/logo.svg" alt="" width="34" height="34">Bursztyn <span>OS</span></a>
      <p>Ciepły i lekki system na bazie Debiana 13, po polsku od pierwszego uruchomienia.</p>
    </div>
    <div>
      <h4>Strona</h4>
      <ul><li><a href="index.html">Start</a></li><li><a href="pobierz.html">Pobierz</a></li><li><a href="aktualnosci.html">Aktualności</a></li><li><a href="o-projekcie.html">O projekcie i FAQ</a></li></ul>
    </div>
    <div>
      <h4>Dla zaawansowanych</h4>
      <ul><li><a href="feed.xml">Kanał RSS</a></li><li><a href="manifest.json">manifest.json</a></li><li><a href="data/wydania.json">wydania.json</a></li><li><a href="https://www.debian.org/">Debian</a></li></ul>
    </div>
    <!-- GEN:STOPKA-TWORCA -->
<p class="tworca-stopka">Bursztyn OS – twórca: <a href="https://github.com/dawidrosa026-lang" rel="author">Dawid Rosa</a> · współtwórca: slavko vinčić</p>
<!-- /GEN:STOPKA-TWORCA -->
    <p class="prawne">Bursztyn OS nie jest oficjalnym projektem Debiana. Debian jest znakiem towarowym Software in the Public Interest, Inc.</p>
  </div>
</footer>
<script type="application/json" id="bursztyn-szyfr">{PAKIET}</script>
<script src="js/main.js" defer></script>
<script src="js/testerzy.js" defer></script>
</body>
</html>
"""


def main() -> int:
    p = argparse.ArgumentParser(description="Szyfruje treść strony dla testerów. Hasło tylko z ENV.")
    p.add_argument("tresc", type=Path, help="plik HTML z treścią do zaszyfrowania")
    p.add_argument("wyjscie", type=Path, help="docelowy testy.html")
    args = p.parse_args()
    tresc = args.tresc.read_bytes()
    if not tresc.strip():
        sys.exit("pusta treść")
    pakiet = szyfruj(tresc, _haslo())
    # szybka weryfikacja, bez wypisywania treści ani hasła
    if deszyfruj(pakiet, _haslo()) != tresc:
        sys.exit("wewnętrzna weryfikacja deszyfrowania nie powiodła się")
    html = SZABLON.replace("{PAKIET}", json.dumps(pakiet, ensure_ascii=True, separators=(",", ":")))
    args.wyjscie.write_text(html, encoding="utf-8")
    print(f"zapisano {args.wyjscie} ({len(html)} znaków, iter={ITERACJE})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
