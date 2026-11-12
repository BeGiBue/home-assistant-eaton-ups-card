#!/usr/bin/env python3
"""Chromium-Tests mit lokalen Home-Assistant-Attrappen; keine realen Geräteaufrufe.

  python tests/browser.py             # Prüfungen
  python tests/browser.py --preview   # zusätzlich Vorschaubilder nach tests/out/

Benötigt: pip install -r requirements-dev.txt  und  playwright install chromium
(oder PLAYWRIGHT_CHROMIUM_EXECUTABLE auf einen vorhandenen Chromium/Chrome setzen).
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

PAGE = """<!doctype html><meta charset="utf-8"><style>
body{margin:0;padding:14px;background:#e9edf1;font-family:Roboto,Inter,sans-serif;font-size:14px;
--primary-text-color:#141414;--secondary-text-color:#6b6f76;--primary-color:#009ac7;--success-color:#43a047;
--warning-color:#ff9800;--error-color:#e53935;--card-background-color:#fff}
</style><div id="w"></div><script>
window.__errors = [];
window.addEventListener('error', (e) => window.__errors.push(String(e.message || e)));
window.addEventListener('unhandledrejection', (e) => window.__errors.push('rejection: ' + e.reason));
customElements.define('ha-card',class extends HTMLElement{constructor(){super();this.attachShadow({mode:'open'}).innerHTML=
  '<style>:host{display:block;background:#fff;border-radius:16px;border:1px solid #dfe3e8;box-sizing:border-box;padding:0}</style><slot></slot>'}});
customElements.define('ha-icon',class extends HTMLElement{connectedCallback(){(this.shadowRoot||this.attachShadow({mode:'open'})).innerHTML=
  '<style>:host{display:inline-flex;width:var(--mdc-icon-size,24px);height:var(--mdc-icon-size,24px)}i{flex:1;border-radius:30%;background:currentColor;opacity:.55}</style><i></i>'}});
window.st = (state, unit) => ({state, attributes: unit ? {unit_of_measurement: unit} : {}});
window.baseStates = () => ({
  'sensor.ups_status': st('OL'), 'sensor.ups_statusdaten': st('OL CHRG'),
  'sensor.ups_ausgangsspannung': st('230.4', 'V'), 'sensor.ups_last': st('23', '%'),
  'sensor.ups_akkulaufzeit': st('42', 'min'), 'sensor.waschkeller_ups_wirkleistung': st('117', 'W'),
});
window.fixture = ({width = 350, config = {}, language = 'de', states = window.baseStates()} = {}) => {
  const w = document.getElementById('w');
  w.replaceChildren();
  w.style.width = width + 'px';
  const card = document.createElement('eaton-ups-card'), events = [];
  card.addEventListener('hass-more-info', (e) => events.push(e.detail.entityId));
  const mk = (s) => ({states: s, language, locale: {language}});
  card.setConfig(config);
  w.appendChild(card);
  card.hass = mk(states);
  return {card, events, set: (s) => { card.hass = mk(s); }};
};
</script>"""

TEST_JS = r"""
async () => {
  const results = [], check = (name, pass) => results.push({name, pass: !!pass});
  const attack = '"><img id="injected" src=x onerror="window.__injected=1"><script>window.__injected=1<\/script>&';
  const turn = (ms = 0) => new Promise((r) => setTimeout(r, ms));
  const frames = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const {fixture, baseStates, st} = window;
  const q = (card, sel) => card.shadowRoot.querySelector(sel);
  const qa = (card, sel) => [...card.shadowRoot.querySelectorAll(sel)];
  const text = (el) => el?.textContent.replace(/\s+/g, ' ').trim();
  const tile = (card, key) => q(card, `.tile[data-more="${key}"]`);
  const clean = (root) => !root.querySelector('#injected, script') && !window.__injected &&
    ![...root.querySelectorAll('*')].some((el) => [...el.attributes].some((a) => /^on/i.test(a.name)));

  // ---- Aufbau und Inhalt ----
  {
    const {card, events} = fixture();
    await frames();
    check('Titel, Status-Pill und vier Kacheln vorhanden', text(q(card, 'h1')) === 'Eaton 3S 850' && !!text(q(card, '.pill b')) && qa(card, '.tile').length === 4);
    check('Netzbetrieb: grüner Ton', q(card, 'ha-card').classList.contains('tone-success'));
    check('Lastbalken folgt dem Wert', q(card, '.tile[data-more="sensor.ups_last"] .bar u').style.width === '23%');
    tile(card, 'sensor.ups_last').click();
    tile(card, 'sensor.ups_akkulaufzeit').click();
    check('Klick öffnet die passende Entität', events.join() === 'sensor.ups_last,sensor.ups_akkulaufzeit');
  }

  // ---- Angleichen statt Neuaufbau ----
  {
    const {card, events, set} = fixture();
    await turn(50);
    const keep = () => ({card: q(card, 'ha-card'), img: q(card, 'img'), load: tile(card, 'sensor.ups_last'), bar: q(card, '.tile[data-more="sensor.ups_last"] .bar u'),
      volt: tile(card, 'sensor.ups_ausgangsspannung'), pill: q(card, '.pill'), icon: q(card, '.tile ha-icon')});
    const before = keep();
    before.load.focus();
    const s = baseStates();
    s['sensor.ups_last'] = st('92', '%');
    s['sensor.ups_ausgangsspannung'] = st('228.1', 'V');
    s['sensor.ups_status'] = st('OB');
    s['sensor.ups_statusdaten'] = st('OB DISCHRG');
    set(s);
    const after = keep();
    check('Neue Werte erscheinen (Last, Spannung, Status)', text(q(card, '.tile[data-more="sensor.ups_last"] .val b')) === '92' && /228/.test(text(after.volt)) && after.card.classList.contains('tone-warning'));
    check('Kein Neuaufbau: Card, Bild, Kacheln, Symbole und Balken bleiben dieselben Elemente', Object.keys(before).every((k) => before[k] === after[k]));
    check('Lastbalken wird am bestehenden Element gesetzt (kann gleiten) und färbt nach Schwellwert', after.bar.style.width === '92%' && after.load.classList.contains('tone-error'));
    check('Tastaturfokus bleibt nach einer Wertänderung erhalten', card.shadowRoot.activeElement === before.load);
    after.load.click();
    check('Klick löst nach Aktualisierungen genau einmal aus', events.length === 1 && events[0] === 'sensor.ups_last');
    s['sensor.ups_last'] = st('unavailable', '%');
    set({...s});
    check('Nicht verfügbare Last: „—", kein Balken, Kachel bleibt bestehen', text(q(card, '.tile[data-more="sensor.ups_last"] .val b')) === '—' && !q(card, '.tile[data-more="sensor.ups_last"] .bar') && tile(card, 'sensor.ups_last') === before.load);
    s['sensor.ups_last'] = st('40', '%');
    set({...s});
    check('Balken kehrt zurück', q(card, '.tile[data-more="sensor.ups_last"] .bar u').style.width === '40%');
    const node = q(card, '.tile[data-more="sensor.ups_ausgangsspannung"] .val b').firstChild;
    set({...s, 'sensor.fremd': st('1')});
    check('Fremde Zustandsänderung fasst nichts an', q(card, '.tile[data-more="sensor.ups_ausgangsspannung"] .val b').firstChild === node);
    card.setConfig({name: 'Neu'});
    check('Geänderte Einstellung baut neu auf', text(q(card, 'h1')) === 'Neu' && q(card, 'ha-card') !== before.card);
    card.setConfig({name: 'Neu', show_status_data: false});
    check('Statusdetails abschaltbar', !q(card, '.info p'));
  }

  // ---- Angeglichene Card entspricht einer frisch aufgebauten ----
  {
    const variants = [
      (s) => { s['sensor.ups_last'] = st('71', '%'); },
      (s) => { s['sensor.ups_status'] = st('OB LB'); s['sensor.ups_akkulaufzeit'] = st('3', 'min'); },
      (s) => { delete s['sensor.ups_ausgangsspannung']; s['sensor.ups_last'] = st('unknown', '%'); },
      (s) => { s['sensor.ups_status'] = st('FSD'); s['sensor.waschkeller_ups_wirkleistung'] = st('0', 'W'); },
      (s) => { Object.assign(s, baseStates()); },
    ];
    const a = fixture({width: 480}), s = baseStates();
    const box = document.createElement('div'); box.style.width = '480px'; document.body.appendChild(box);
    const snap = (c) => q(c, 'ha-card').outerHTML.replace(/\s+/g, ' ');
    let same = true, at = -1;
    for (let i = 0; i < variants.length && same; i++) {
      variants[i](s);
      a.set({...s});
      const fresh = document.createElement('eaton-ups-card');
      fresh.setConfig({});
      box.replaceChildren(fresh);
      fresh.hass = {states: {...s}, language: 'de', locale: {language: 'de'}};
      await frames();
      if (snap(a.card) !== snap(fresh)) { same = false; at = i; }
    }
    box.remove();
    check('Angeglichene Card entspricht nach jedem Schritt einer frisch aufgebauten' + (same ? '' : ' (Abweichung in Schritt ' + at + ')'), same);
  }

  // ---- HTML-Injection: erster Aufbau und Angleichen ----
  {
    const {card} = fixture({config: {name: attack, image: attack, load_entity: 'sensor.x' + attack, image_mode: 'inline'}});
    await turn(50);
    check('Injection über Konfiguration bleibt Text', clean(card.shadowRoot) && text(q(card, 'h1')).includes('<img id="injected"'));
    const {card: c2, set} = fixture();
    const s = baseStates();
    for (const id of Object.keys(s)) s[id] = st(attack, attack);
    set(s);
    await turn(50);
    check('Injection über Zustände und Einheiten bleibt beim Angleichen Text', clean(c2.shadowRoot) && text(q(c2, '.pill b')).includes('<img id="injected"') && text(tile(c2, 'sensor.ups_last')).includes('<img id="injected"'));
  }

  // ---- Bild-Optionen und Sprache ----
  {
    let requests = 0;
    const bad = 'http://127.0.0.1:9/gibt-es-nicht.png';
    const {card, set} = fixture({config: {image: bad}});
    for (let i = 0; i < 40 && !q(card, 'img').getAttribute('src').startsWith('data:image/'); i++) await turn(100);
    check('Fehlendes eigenes Bild fällt auf das eingebettete zurück', q(card, 'img').getAttribute('src').startsWith('data:image/'));
    const img = q(card, 'img');
    const s = baseStates(); s['sensor.ups_last'] = st('55', '%');
    set(s);
    await turn(200);
    check('Fehlendes Bild wird bei späteren Werten nicht erneut angefordert', q(card, 'img') === img && img.getAttribute('src').startsWith('data:image/'));
    // Neuaufbau, während das eigene Bild noch lädt: Das neue Bild muss trotzdem auf das eingebettete zurückfallen
    for (const early of [true, false]) {
      const bad2 = 'http://127.0.0.1:9/noch-eins-' + early + '.png';
      const w = document.getElementById('w');
      w.replaceChildren();
      const c = document.createElement('eaton-ups-card');
      if (early) c.hass = {states: baseStates(), language: 'de', locale: {language: 'de'}};
      c.setConfig({image: bad2});
      w.appendChild(c);
      if (!early) c.hass = {states: baseStates(), language: 'de', locale: {language: 'de'}};
      c.setConfig({image: bad2, name: 'y'});
      for (let i = 0; i < 40 && !q(c, 'img').getAttribute('src').startsWith('data:image/'); i++) await turn(100);
      await turn(200);
      const im = q(c, 'img');
      check('Neuaufbau während des Ladens (' + (early ? 'Werte zuerst' : 'Einstellung zuerst') + '): Ersatzbild sichtbar', im.getAttribute('src').startsWith('data:image/') && getComputedStyle(im).display !== 'none' && im.naturalWidth > 0);
    }
    const b = fixture({config: {image_mode: 'inline'}}).card;
    check('Bild neben dem Titel', !!q(b, '.art img') && !q(b, '.bgimg'));
    const e = fixture({language: 'en'}).card, d = fixture({language: 'de'}).card;
    check('Englisch, wenn Home Assistant nicht deutsch ist', text(q(e, '.pill b')) !== text(q(d, '.pill b')) || text(q(e, '.lbl')) !== text(q(d, '.lbl')));
  }

  // ---- Layout: Schriftstufen, Klassen, kein Überlauf, Höhe ----
  for (const [width, fs, wide, slim] of [[300, '14px', false, true], [350, '14px', false, false], [480, '15px', false, false], [800, '19px', true, false], [1100, '22px', true, false]]) {
    for (const mode of ['background', 'inline']) {
      const {card} = fixture({width, config: {image_mode: mode}});
      await frames();
      const hc = q(card, 'ha-card'), r = hc.getBoundingClientRect();
      const inside = qa(card, '.tile, h1, .pill, .val b').every((el) => { const b = el.getBoundingClientRect(); return b.left >= r.left - .5 && b.right <= r.right + .5; });
      const noClip = qa(card, '.val b, .pill b').every((el) => el.scrollWidth <= el.clientWidth + 1);
      const cols = new Set(qa(card, '.tile').map((t) => Math.round(t.getBoundingClientRect().left))).size;
      check(`${width} px (${mode}): Schriftstufe ${fs}, ${wide ? 'vier Kacheln in einer Reihe' : 'zwei Spalten'}${slim ? ', schmal' : ''}`,
        card.style.getPropertyValue('--fs') === fs && hc.classList.contains('wide') === wide && hc.classList.contains('slim') === slim && cols === (wide ? 4 : 2));
      check(`${width} px (${mode}): nichts ragt aus der Card, Werte vollständig`, inside && noClip && hc.scrollWidth <= hc.clientWidth + 1);
      const rows = card.getGridOptions().min_rows, h = hc.offsetHeight;
      check(`${width} px (${mode}): gemeldete Mindesthöhe deckt den Inhalt`, rows * 64 - 8 >= h - 1);
    }
  }
  for (const [start, steps, expect, read] of [
    [395, [405, 395, 409, 414, 392, 386], ['14px', '14px', '14px', '14px', '15px', '15px', '14px'], (c) => c.style.getPropertyValue('--fs')],
    [695, [705, 695, 709, 714, 692, 686], ['n', 'n', 'n', 'n', 'w', 'w', 'n'], (c) => (c.shadowRoot.querySelector('ha-card').classList.contains('wide') ? 'w' : 'n')],
    [335, [345, 335, 349, 354, 332, 326], ['s', 's', 's', 's', 'n', 'n', 's'], (c) => (c.shadowRoot.querySelector('ha-card').classList.contains('slim') ? 's' : 'n')],
  ]) {
    const {card} = fixture({width: start, config: {image_mode: 'inline'}});
    await frames();
    const w = document.getElementById('w'), seen = [read(card)];
    for (const px of steps) { w.style.width = px + 'px'; await frames(); await frames(); seen.push(read(card)); }
    check('Hysterese um ' + (start + 5) + ' px: ±12 px kippen nichts (' + seen.join(' ') + ')', seen.join() === expect.join());
  }
  // Nachgebildete Scrollleiste: Ist die Card höher als H, wird ihr Platz 15 px schmaler (wie bei einer
  // einblendenden Scrollleiste). Um jede Layout-Schwelle darf die Breite danach nicht dauerhaft hin- und herkippen.
  for (const mode of ['background', 'inline']) for (const T of [340, 400, 600, 700, 800, 1000]) {
    const host = document.getElementById('w');
    host.replaceChildren();
    host.style.width = 'auto';
    const hass = {states: baseStates(), language: 'de', locale: {language: 'de'}};
    const mk = (W) => {
      const box = document.createElement('div'); box.style.width = W + 'px';
      const c = document.createElement('eaton-ups-card'); c.setConfig({image_mode: mode}); box.appendChild(c); host.appendChild(box); c.hass = hass;
      return {box, c};
    };
    const height = (c) => c.shadowRoot.querySelector('ha-card').offsetHeight;
    const probe = [T - 20, T + 20].map(mk);
    await frames();
    const hs = probe.map((p) => height(p.c)), lo = Math.min(...hs) - 3, hi = Math.max(...hs) + 3;
    host.replaceChildren();
    const cards = [];
    for (let W = T - 14; W <= T + 30; W += 2) for (let H = lo; H <= hi; H += Math.max(2, Math.ceil((hi - lo) / 6))) cards.push({...mk(W), W, H, cur: W, n: 0});
    await frames();
    for (let f = 0; f < 60; f++) {
      const now = cards.map((o) => height(o.c));
      cards.forEach((o, i) => { const want = o.W - (now[i] > o.H ? 15 : 0); if (want !== o.cur) { o.cur = want; o.box.style.width = want + 'px'; o.n++; } });
      await new Promise((r) => requestAnimationFrame(r));
    }
    const worst = Math.max(...cards.map((o) => o.n));
    check(`Scrollleiste um ${T} px (${mode}): Breite pendelt sich ein (höchstens ${worst} Wechsel in 60 Bildern)`, worst <= 4);
  }
  {
    const {card, set} = fixture({width: 800});
    await frames();
    set({...baseStates(), 'sensor.ups_last': st('24', '%')});
    check('Breites Layout übersteht eine Wertänderung', q(card, 'ha-card').classList.contains('wide'));
    card.setConfig({name: 'X'});
    check('Breites Layout übersteht einen Neuaufbau', q(card, 'ha-card').classList.contains('wide'));
    card.remove();
    document.getElementById('w').appendChild(card);
    await frames();
    check('Entfernen und Wiedereinhängen ohne Fehler', text(q(card, 'h1')) === 'X');
    const first = q(card, '.tile');
    first.focus();
    check('Sichtbarer Fokusrahmen', !first.matches(':focus-visible') || parseFloat(getComputedStyle(first).outlineWidth) >= 2);
    const w = document.getElementById('w');
    w.replaceChildren();
    const early = document.createElement('eaton-ups-card');
    early.hass = {states: baseStates(), language: 'de'};
    w.appendChild(early);
    early.setConfig({});
    check('Werte vor der Einstellung gesetzt: Aufbau ohne Fehler', qa(early, '.tile').length === 4);
    const empty = fixture({states: {}}).card;
    check('Ohne jede Entität: Aufbau ohne Fehler, Werte „—"', qa(empty, '.val b').every((b) => text(b) === '—'));
  }
  await frames();
  check('Keine Fehlermeldungen des Browsers, auch kein „ResizeObserver loop" (' + window.__errors.length + ')', window.__errors.length === 0);
  return results;
}
"""


def launch(p):
    executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    return p.chromium.launch(**({"executable_path": executable, "args": ["--no-sandbox"]} if executable else {}))


def main():
    source = (ROOT / "eaton-ups-card.js").read_text(encoding="utf8")
    errors = []
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": 1200, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_content(PAGE)
        page.add_script_tag(content=source)
        results = page.evaluate(TEST_JS)
        results.append({"name": "keine JavaScript-Fehler", "pass": not errors})
        if "--preview" in sys.argv:
            out = ROOT / "tests" / "out"
            out.mkdir(exist_ok=True)
            for width in (300, 350, 800):
                for mode in ("background", "inline"):
                    shot = browser.new_page(viewport={"width": width + 28, "height": 400}, device_scale_factor=2)
                    shot.set_content(PAGE)
                    shot.add_script_tag(content=source)
                    shot.evaluate("([width, mode]) => { window.fixture({width, config: {image_mode: mode}}); }", [width, mode])
                    shot.wait_for_timeout(200)
                    shot.screenshot(path=str(out / f"eaton-{mode}-{width}.png"), full_page=True)
                    shot.close()
        browser.close()
    for result in results:
        print(("PASS " if result["pass"] else "FAIL ") + result["name"])
    failures = sum(not result["pass"] for result in results)
    print(f"\n{len(results)} Prüfungen, {failures} Fehler")
    if errors:
        print(errors)
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
