(function () {
  "use strict";
  var LS = "bursztyn-tester-k";
  var pakietEl = document.getElementById("bursztyn-szyfr");
  var form = document.getElementById("formularz-testerow");
  var pole = document.getElementById("haslo-testerow");
  var pamietaj = document.getElementById("zapamietaj-testerow");
  var blad = document.getElementById("blad-testerow");
  var cel = document.getElementById("tresc-testerow");
  if (!pakietEl || !form || !pole || !cel) return;

  function b64doBuf(s) {
    var bin = atob(s);
    var u = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    return u.buffer;
  }
  function bufDoB64(buf) {
    var u = new Uint8Array(buf);
    var s = "";
    for (var i = 0; i < u.length; i++) s += String.fromCharCode(u[i]);
    return btoa(s);
  }
  function pokazBlad(tak) {
    if (!blad) return;
    blad.hidden = !tak;
  }
  function pokazTresc(html) {
    cel.innerHTML = html;
    cel.hidden = false;
    form.hidden = true;
    pokazBlad(false);
  }
  function wczytajPakiet() {
    var d = JSON.parse(pakietEl.textContent);
    if (d.kdf !== "PBKDF2-SHA256" || !d.sol || !d.iv || !d.dane) throw new Error("pakiet");
    if ((d.iter | 0) < 600000) throw new Error("iter");
    return d;
  }
  function wyprowadzKlucz(haslo, sol, iter) {
    return crypto.subtle.importKey("raw", new TextEncoder().encode(haslo), "PBKDF2", false, ["deriveKey"])
      .then(function (material) {
        return crypto.subtle.deriveKey(
          { name: "PBKDF2", salt: sol, iterations: iter, hash: "SHA-256" },
          material,
          { name: "AES-GCM", length: 256 },
          true,
          ["decrypt"]
        );
      });
  }
  function odszyfrujKluczem(klucz, iv, dane) {
    return crypto.subtle.decrypt({ name: "AES-GCM", iv: iv }, klucz, dane)
      .then(function (buf) { return new TextDecoder("utf-8").decode(buf); });
  }
  function zapiszKlucz(solB64, iter, klucz) {
    return crypto.subtle.exportKey("raw", klucz).then(function (surowy) {
      try {
        localStorage.setItem(LS, JSON.stringify({ sol: solB64, iter: iter, klucz: bufDoB64(surowy) }));
      } catch (e) { /* brak pamięci / tryb prywatny */ }
    });
  }
  function wczytajZapisany(solB64, iter) {
    try {
      var s = localStorage.getItem(LS);
      if (!s) return Promise.resolve(null);
      var o = JSON.parse(s);
      if (!o || o.sol !== solB64 || o.iter !== iter || !o.klucz) return Promise.resolve(null);
      return crypto.subtle.importKey("raw", b64doBuf(o.klucz), { name: "AES-GCM" }, false, ["decrypt"]);
    } catch (e) {
      return Promise.resolve(null);
    }
  }
  function usunZapis() {
    try { localStorage.removeItem(LS); } catch (e) {}
  }

  var pakiet;
  try { pakiet = wczytajPakiet(); } catch (e) { return; }
  var sol = b64doBuf(pakiet.sol);
  var iv = b64doBuf(pakiet.iv);
  var dane = b64doBuf(pakiet.dane);

  wczytajZapisany(pakiet.sol, pakiet.iter).then(function (klucz) {
    if (!klucz) return;
    return odszyfrujKluczem(klucz, iv, dane).then(pokazTresc, function () { usunZapis(); });
  });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    pokazBlad(false);
    var haslo = pole.value;
    if (!haslo) { pokazBlad(true); return; }
    var przycisk = form.querySelector('button[type="submit"]');
    if (przycisk) przycisk.disabled = true;
    wyprowadzKlucz(haslo, sol, pakiet.iter)
      .then(function (klucz) {
        return odszyfrujKluczem(klucz, iv, dane).then(function (html) {
          if (pamietaj && pamietaj.checked) zapiszKlucz(pakiet.sol, pakiet.iter, klucz);
          else usunZapis();
          pole.value = "";
          pokazTresc(html);
        });
      })
      .catch(function () { pokazBlad(true); })
      .then(function () { if (przycisk) przycisk.disabled = false; });
  });
})();
