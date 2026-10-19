# Strona internetowa Bursztyn OS

Statyczna strona (HTML + CSS + odrobina JavaScriptu) dla Bursztyn OS, polskiego remiksu Debiana 13.
Nie wymaga żadnego kroku budowania: wystarczy wrzucić zawartość tego folderu na dowolny hosting plików statycznych.

## Struktura

```
bursztyn-www/
├── index.html          Strona główna: hero, funkcje, zrzuty ekranu, tapety, najnowsze ogłoszenia
├── pobierz.html        Pobieranie: karty wydań, weryfikacja SHA-256, nagrywanie pendrive'a
├── aktualnosci.html    Ogłoszenia i wydania (z manifest.json + data/ogloszenia.json)
├── o-projekcie.html    O projekcie i FAQ
├── 404.html            Strona „nie znaleziono” (GitHub Pages / Netlify / Cloudflare używają jej automatycznie)
├── manifest.json       Manifest wersji – TEN SAM format, który czyta system (nowa-wersja.sh / co-nowego.py)
├── feed.xml            Kanał RSS (generowany przez generuj.py)
├── generuj.py          Generator: RSS + statyczne fragmenty HTML (dla użytkowników bez JS)
├── data/
│   ├── wydania.json    Dane wydań (rozmiar, sha256, linki) – strona Pobierz
│   ├── ogloszenia.json Ręcznie pisane ogłoszenia
│   └── strona.json     Docelowy adres strony (używany w feed.xml)
├── css/style.css       Wygląd (ciemny bursztyn, responsywny)
├── js/main.js          Menu mobilne, podgląd zrzutów, kopiowanie sum, odświeżanie danych z JSON
└── img/                Logo, favicony, zrzuty ekranu i tapety (JPG + WebP)
```

### Jak działają dane

- Treść wydań i ogłoszeń jest **wpisana na stałe w HTML** przez `generuj.py` (między znacznikami
  `<!-- GEN:… -->` i `<!-- /GEN:… -->`), więc strona działa bez JavaScriptu.
- `js/main.js` po załadowaniu strony dodatkowo czyta `data/wydania.json`, `manifest.json`
  i `data/ogloszenia.json` i odświeża te same sekcje. Dzięki temu poprawka w JSON jest widoczna
  od razu, nawet jeśli zapomnisz uruchomić `generuj.py` (ale RSS i wersja bez JS wymagają generatora).
- Ogłoszenia = wpisy z `data/ogloszenia.json` + po jednym wpisie „Wydanie: …” dla każdej pozycji
  `historia` w `manifest.json`. Dla bieżącej wersji lista zmian pochodzi z pola `zmiany`.
- Nie edytuj ręcznie treści między znacznikami `GEN` – generator ją nadpisze.

## Wydanie nowej wersji (np. 1.1)

1. Opublikuj plik ISO (i plik `.sha256`) – np. GitHub Releases, SourceForge, własny serwer.
2. W `data/wydania.json` zaktualizuj kartę wydania: `nazwa`, `wersja`, `data`, `plik`, `rozmiar`,
   `sha256`, `url` (prawdziwy link zamiast `#`), `url_sha256`, `status: "gotowe"`.
3. W `manifest.json` ustaw nowe `wersja`, `data`, `nazwa`, `zmiany`, `pobierz`
   i dopisz wpis **na górze** listy `historia`. (Format opisany w `~/bursztyn/wersje/JAK-WYDAC-NOWA-WERSJE.md`.)
4. Opcjonalnie dodaj własne ogłoszenie w `data/ogloszenia.json`.
5. Uruchom generator i sprawdź poprawność:
   ```bash
   python3 -m json.tool manifest.json > /dev/null && python3 -m json.tool data/wydania.json > /dev/null
   python3 generuj.py
   python3 -m http.server 8088      # podgląd: http://localhost:8088
   ```
6. Wyślij zmienione pliki na hosting.

Gdy Bursztyn OS Lite będzie gotowy: w `data/wydania.json` w karcie `bursztyn-os-lite` wpisz
`data`, `plik`, `rozmiar`, `sha256`, `url` i zmień `status` na `"gotowe"`, potem `python3 generuj.py`.

## Powiadomienia o nowej wersji w systemie

System Bursztyn OS czyta manifest z adresu `MANIFEST_URL` w `~/bursztyn/wersje.conf`
(w zainstalowanym systemie: `/etc/bursztyn/wersje.conf`). Po opublikowaniu strony ustaw:

```
MANIFEST_URL=https://<adres-strony>/manifest.json
```

Od tej chwili **wydanie nowej wersji = podmiana `manifest.json` na stronie** – wszystkie komputery
z Bursztyn OS pokażą „★ Nowa wersja” i okno „Co nowego”. Pole `pobierz` w manifeście warto ustawić
na `https://<adres-strony>/pobierz.html` (przycisk „Pobierz” w oknie „Co nowego”); teraz jest puste,
więc przycisk jest wyszarzony.

## Hosting (wszystkie opcje są darmowe)

Przed publikacją wpisz docelowy adres w `data/strona.json` (`adres`) i uruchom `python3 generuj.py`
– inaczej linki w `feed.xml` będą wskazywać na przykładowy `https://bursztyn-os.example`.

- **GitHub Pages** – utwórz repozytorium (np. `bursztyn-os`), wrzuć zawartość folderu,
  w *Settings → Pages* wybierz gałąź `main` i folder `/ (root)`. Adres:
  `https://<konto>.github.io/bursztyn-os/`. Plik `.nojekyll` jest już dodany.
  Uwaga: GitHub nie przyjmie pliku ISO 2 GB do repozytorium (limit 100 MB) – ISO wrzuć do
  *Releases* (limit 2 GiB na plik; ISO 1.1 ma 1 823 358 976 bajtów = 1,70 GiB).
- **Netlify** – *Add new site → Deploy manually* i przeciągnij folder (lub połącz z repozytorium GitHub).
  Nie wymaga ustawień budowania.
- **Cloudflare Pages** – *Create → Pages → Upload assets* (lub połączenie z GitHubem), bez polecenia
  budowania, katalog wyjściowy `/`. Pojedynczy plik do 25 MiB, więc ISO trzymaj gdzie indziej.

Własną domenę można podpiąć w każdej z tych usług.

## Do uzupełnienia (TODO)

- Pliki ISO obu edycji są w GitHub Releases: https://github.com/dawidrosa026-lang/bursztyn-os/releases/tag/v1.1
- Strona opublikowana: https://dawidrosa026-lang.github.io/bursztyn-os/ (repozytorium github.com/dawidrosa026-lang/bursztyn-os).
