/* Bursztyn OS – drobny JavaScript strony (bez bibliotek).
   Strona działa też bez JS: treść wydań i ogłoszeń jest wstawiona statycznie przez generuj.py.
   Ten skrypt dodaje menu mobilne, podgląd zrzutów, kopiowanie sum SHA-256
   i odświeża wydania/ogłoszenia prosto z plików JSON (gdy ktoś zapomni uruchomić generuj.py). */
(function () {
  "use strict";
  document.documentElement.classList.remove("bez-js");

  var MIESIACE = ["stycznia","lutego","marca","kwietnia","maja","czerwca","lipca","sierpnia","września","października","listopada","grudnia"];
  function e(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#x27;"}[c]; }); }
  function dataPl(iso) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || ""); return m ? (+m[3]) + " " + MIESIACE[+m[2] - 1] + " " + m[1] : (iso || ""); }
  function slug(t) { return String(t).toLowerCase().replace(/[ąćęłńóśźż]/g, function (c) { return "acelnoszz"["ąćęłńóśźż".indexOf(c)]; }).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
  function pobierzJSON(u) { return fetch(u, {cache: "no-cache"}).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }

  /* Menu mobilne */
  var przel = document.querySelector(".menu-przelacznik"), nav = document.getElementById("nawigacja");
  if (przel && nav) przel.addEventListener("click", function () {
    var o = nav.classList.toggle("otwarta"); przel.setAttribute("aria-expanded", o ? "true" : "false");
  });

  /* Podgląd zrzutów ekranu */
  var dlg = document.createElement("dialog");
  dlg.className = "lightbox";
  dlg.innerHTML = '<button type="button" aria-label="Zamknij podgląd">✕ Zamknij</button><img alt=""><p></p>';
  if (typeof dlg.showModal === "function") {
    document.body.appendChild(dlg);
    dlg.querySelector("button").addEventListener("click", function () { dlg.close(); });
    dlg.addEventListener("click", function (ev) { if (ev.target === dlg) dlg.close(); });
    document.querySelectorAll("a[data-podglad]").forEach(function (a) {
      a.addEventListener("click", function (ev) {
        ev.preventDefault();
        var img = dlg.querySelector("img"), im = a.querySelector("img");
        img.src = a.getAttribute("href"); img.alt = im ? im.alt : "";
        dlg.querySelector("p").textContent = a.getAttribute("data-podglad");
        dlg.showModal();
      });
    });
  }

  /* Kopiowanie sum kontrolnych */
  function podepnijKopiowanie() {
    document.querySelectorAll("[data-kopiuj]").forEach(function (b) {
      if (!navigator.clipboard) return;
      b.hidden = false;
      b.onclick = function () {
        navigator.clipboard.writeText(b.getAttribute("data-kopiuj")).then(function () {
          b.textContent = "Skopiowano ✓"; setTimeout(function () { b.textContent = "Kopiuj"; }, 1800);
        });
      };
    });
  }

  /* Wydania (pobierz.html) – ten sam układ co w generuj.py */
  function htmlWydanie(w) {
    var gotowe = w.status === "gotowe", wk = '<span class="wkrotce">wkrótce</span>';
    var znaczek = gotowe ? '<span class="znaczek gotowe">Gotowe</span>' : '<span class="znaczek w-przygotowaniu">W przygotowaniu</span>';
    var sha = w.sha256 ? '<div class="sha"><code>' + e(w.sha256) + '</code><button class="przycisk drugi maly kopiuj" type="button" data-kopiuj="' + e(w.sha256) + '" hidden>Kopiuj</button></div>' : wk;
    var url = w.url || "#";
    var pob = url === "#"
      ? '<span class="przycisk wylaczony" aria-disabled="true" title="Plik nie jest jeszcze nigdzie opublikowany">⤓ Link wkrótce</span>'
      : '<a class="przycisk" href="' + e(url) + '">⤓ Pobierz ISO</a>';
    return '<article class="karta wydanie' + (gotowe ? " polecane" : "") + '" id="' + e(w.id) + '">' +
      '<div class="wydanie-gora"><img src="img/logo.svg" alt="" width="54" height="54"><div><h3>' + e(w.nazwa) + '</h3>' + znaczek + '</div></div>' +
      '<p class="opis">' + e(w.opis) + '</p>' +
      '<ul class="lista-tagi" aria-label="Aplikacje">' + (w.aplikacje || []).map(function (a) { return "<li>" + e(a) + "</li>"; }).join("") + '</ul>' +
      '<dl><dt>Edycja</dt><dd>' + e(w.edycja) + '</dd>' +
      '<dt>Data wydania</dt><dd>' + (w.data ? e(dataPl(w.data)) : wk) + '</dd>' +
      '<dt>Plik</dt><dd>' + (w.plik ? "<code>" + e(w.plik) + "</code>" : wk) + '</dd>' +
      '<dt>Rozmiar</dt><dd>' + (w.rozmiar ? e(w.rozmiar) : wk) + '</dd>' +
      '<dt>SHA-256</dt><dd>' + sha + '</dd>' +
      '<dt>Wymagania</dt><dd><ul class="wym">' + (w.wymagania || []).map(function (x) { return "<li>" + e(x) + "</li>"; }).join("") + '</ul></dd></dl>' +
      '<div class="akcje">' + pob + '</div></article>';
  }
  var bWyd = document.getElementById("wydania");
  if (bWyd) pobierzJSON("data/wydania.json").then(function (d) {
    bWyd.innerHTML = d.wydania.map(htmlWydanie).join("\n"); podepnijKopiowanie();
  }).catch(podepnijKopiowanie);
  else podepnijKopiowanie();

  /* Ogłoszenia (aktualnosci.html, index.html) – ten sam układ co w generuj.py */
  function wpisy(m, o) {
    var lista = (o.wpisy || []).map(function (w) {
      return {id: w.id || slug(w.tytul), tytul: w.tytul, data: w.data || "", rodzaj: "Ogłoszenie", akapity: w.tresc || [], zmiany: [], link: w.link || ""};
    });
    (m.historia || []).forEach(function (h) {
      var b = h.wersja === m.wersja, t = (b && m.nazwa) ? m.nazwa : "Bursztyn OS " + h.wersja;
      lista.push({id: "wydanie-" + slug(String(h.wersja)), tytul: "Wydanie: " + t, data: h.data || "", rodzaj: "Wydanie",
        akapity: b ? (h.zmiany || []) : [], zmiany: b ? (m.zmiany || []) : (h.zmiany || []), link: b ? (m.pobierz || "") : ""});
    });
    lista.sort(function (a, b) {
      var ka = a.data + (a.rodzaj === "Ogłoszenie" ? "1" : "0"), kb = b.data + (b.rodzaj === "Ogłoszenie" ? "1" : "0");
      return ka < kb ? 1 : ka > kb ? -1 : 0;
    });
    return lista;
  }
  function htmlWpis(w, skrot, poz) {
    var adr = "aktualnosci.html#" + e(w.id);
    var s = '<article class="karta wpis" id="' + e(w.id) + '"><time datetime="' + e(w.data) + '">' + e(dataPl(w.data)) + '</time><span class="rodzaj">' + e(w.rodzaj) + '</span>' +
      "<" + poz + '><a href="' + adr + '">' + e(w.tytul) + "</a></" + poz + ">";
    (skrot ? w.akapity.slice(0, 1) : w.akapity).forEach(function (a) { s += "<p>" + e(a) + "</p>"; });
    if (w.zmiany.length && !skrot) s += "<p><strong>Co nowego:</strong></p><ul>" + w.zmiany.map(function (z) { return "<li>" + e(z) + "</li>"; }).join("") + "</ul>";
    else if (w.zmiany.length) s += "<p>" + w.zmiany.length + " nowości w tym wydaniu.</p>";
    if (w.link && !skrot) s += '<p><a class="przycisk maly" href="' + e(w.link) + '">Pobierz</a></p>';
    if (skrot) s += '<p><a href="' + adr + '">Czytaj dalej →</a></p>';
    return s + "</article>";
  }
  var bWp = document.getElementById("wpisy"), bNaj = document.getElementById("najnowsze");
  if (bWp || bNaj) Promise.all([pobierzJSON("manifest.json"), pobierzJSON("data/ogloszenia.json")]).then(function (r) {
    var l = wpisy(r[0], r[1]);
    if (bWp) {
      bWp.innerHTML = l.map(function (w) { return htmlWpis(w, false, "h2"); }).join("\n");
      if (location.hash) { var c = document.getElementById(location.hash.slice(1)); if (c) c.scrollIntoView(); }
    }
    if (bNaj) bNaj.innerHTML = l.slice(0, 2).map(function (w) { return htmlWpis(w, true, "h3"); }).join("\n");
  }).catch(function () { /* zostaje wersja statyczna */ });
})();
