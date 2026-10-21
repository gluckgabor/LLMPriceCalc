# Telepítési útmutató: agent.py futtatása

## Áttekintés

Az `agent.py` egy Playwright szkript, amely az
[Artificial Analysis LLM árkalkulátorát](https://artificialanalysis.ai/tools/llm-price-calculator)
ellenőrzi. Kitölti a "Calculate by tokens" űrlapot rögzített értékekkel, elküldi, kiolvassa egy
adott modell sorát az eredménytáblából, majd összehasonlítja a kiolvasott értékeket a szkriptben
beégetett elvárt értékekkel. Ha minden egyezik, `0` kilépési kóddal tér vissza, ha bármi eltér,
akkor `1`-gyel — így CI ellenőrzésként is használható.

**Nincs benne LLM.** A projekt korábbi változata a `browser-use` könyvtárral és egy Mistral
modellel hajtotta a böngészőt, amely lépésenként döntött. Ezt egyszerű Playwright váltotta fel,
mert a feladat bemenetei rögzítettek és az elvárt eredmény ismert: az LLM csak bizonytalanságot
adott hozzá (egy futás 22–83 másodpercig tartott, és három futásból egyszer töltötte ki helyesen
az űrlapot), míg a Playwright változat nagyjából 1,4 másodperc alatt lefut, és minden alkalommal
ugyanazt csinálja. A `MISTRAL_API_KEY`-t és a `.env` fájlt az `agent.py` már nem olvassa.

A "Mistral" szó továbbra is szerepel a szkriptben `TARGET_MODEL = "Mistral Large 4 Preview"`
formában — ez csak a weboldalon árazott sor neve, nem egy meghívott API.

## Opcionális: VS Code beállítás

Az útmutató kényelmesebb olvasásához és szerkesztéséhez VS Code-ban:

1. **Markdown Preview Enhanced bővítmény telepítése:**
   - Nyissa meg a VS Code-ot
   - Nyissa meg a Bővítmények nézetet (Ctrl+Shift+X vagy Cmd+Shift+X)
   - Keressen rá: "Markdown Preview Enhanced"
   - Kattintson a Telepítés gombra

## Előfeltételek

### 1. Python futtatókörnyezet

- **Követelmény**: Python 3.10 vagy újabb (ez a projekt 3.11.9-en fut)
- **Ellenőrzés**: `python --version`
- **Telepítés**: [python.org](https://www.python.org/downloads/)

### 2. Playwright és egy Chromium böngésző

A Playwrighthoz két dolog kell: a Python csomag és egy letöltött böngésző bináris. A csomag
telepítése önmagában nem elég — a böngésző letöltése külön parancs, lásd a 3. lépést. A Chromium
körülbelül 120 MB, és Windowson a `%LOCALAPPDATA%\ms-playwright` könyvtárba kerül.

## Telepítési lépések

### 1. lépés: Virtuális környezet létrehozása (ajánlott)

```bash
cd "C:/Users/Gluck Gabor/Mistral_projects/LLMPriceCalc"
python -m venv venv
```

**A környezet aktiválása:**

- Windows (CMD): `venv\Scripts\activate`
- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- Windows (Git Bash): `source venv/Scripts/activate`
- macOS/Linux: `source venv/bin/activate`

### 2. lépés: A Python csomag telepítése

```bash
pip install playwright
```

Ez az egyetlen közvetlen függőség. Magával hozza a `greenlet` és a `pyee` csomagot. A jelenleg
telepített verziók: `playwright==1.64.0`, `greenlet==3.5.6`, `pyee==13.0.1`.

### 3. lépés: A Chromium böngésző telepítése

```bash
playwright install chromium
```

Ez kötelező előfeltétel, nem opcionális kiegészítő — nélküle a szkript induláskor elhasal
`Executable doesn't exist at ...` hibával. Csak a Chromium kell; a `playwright install` paraméter
nélkül a Firefoxot és a WebKitet is letölti, amelyeket ez a projekt nem használ.

### 4. lépés: A konfiguráció áttekintése

Minden állítható érték az `agent.py` tetején lévő konstansokban van. Sem `.env` fájl, sem API kulcs
nem kell hozzá.

| Konstans | Mire való |
|---|---|
| `HEADLESS` | `True` esetén láthatatlanul fut. `False`-ra állítva látszik a böngésző munkája. |
| `TARGET_MODEL` | Melyik sort olvassa ki az eredménytáblából. |
| `INPUT_TOKENS`, `RESPONSE_TOKENS`, `REASONING_TOKENS`, `API_CALLS` | Az űrlapba beírt négy érték. |
| `EXPECTED_TOTAL_COST`, `EXPECTED_COST_PER_CALL` | Az elvárt eredmény, amivel a kiolvasott értékeket összeveti. |
| `RESULTS_TIMEOUT_MS` | Mennyit vár az eredménytáblára a Calculate gomb megnyomása után. |

**Ha a négy bemeneti érték bármelyikét módosítja, a két elvárt értéket is frissítenie kell**,
különben a futás — helyesen — hibára fut. Lásd lentebb: "Az elvárt értékek frissítése".

### 5. lépés: Futtatás

```bash
python agent.py
```

## Mit csinál a szkript

1. Megnyitja a kalkulátort
2. Megkeresi a "Calculate by tokens" űrlapot
3. – 6. Beállítja az `Input tokens`, `Response tokens`, `Reasoning tokens` és `API calls` mezőket
7. Visszaolvassa mind a négy mezőt, és ellenőrzi, hogy a beírt értékeket tartalmazzák
8. Rákattint a "Calculate" gombra
9. Megvárja, amíg megjelenik a `Mistral Large 4 Preview` sor
10. Kiolvassa a sort, és összeveti az elvárt értékekkel

A 7. lépésre azért van szükség, mert az oldal **mind a négy mezőt visszaállítja az alapértelmezett
értékre abban a pillanatban, amikor a Calculate gombra kattint**, miközben az eredménytábla
továbbra is az elküldött futás értékeit mutatja. A kattintás előtti pillanat az egyetlen, amikor a
beírt értékek ellenőrizhetők.

## Kimenet

A konzolon minden lépés PASS vagy FAIL jelöléssel jelenik meg, majd az ellenőrzések:

```
--- Validations ---
[PASS] Scrape produced a row: {...}
[PASS] Model name: expected 'Mistral Large 4 Preview', actual 'Mistral Large 4 Preview'
[PASS] Total cost: expected '$7.63', actual '$7.63'
[PASS] Cost per call: expected '$0.01', actual '$0.01'
[PASS] API calls: expected 1000, actual 1000
0 failed, 5 passed.  (1.4s)
```

A `results/price_check_<időbélyeg>.md` fájlba időbélyeges markdown riport készül, amely tartalmazza
a bemeneteket, az elvárt értékeket, az eredményt, az ellenőrzések tábláját és a lépések tábláját.

Kilépési kódok: `0` = minden ellenőrzés sikeres, `1` = legalább egy hibára futott.

## Az elvárt értékek frissítése

Az `EXPECTED_TOTAL_COST` és az `EXPECTED_COST_PER_CALL` a teszt referenciaértéke. Ezeket az élő
oldalon 2026-10-21-én ellenőriztük. Ha valamelyik hibára fut, annak két oka lehet:

- **A szkript rossz sort olvasott ki, vagy rossz bemenetekkel küldte el az űrlapot** — valódi hiba,
  érdemes megvizsgálni.
- **Az Artificial Analysis megváltoztatta a modell árazását** — ez nem hiba; nyissa meg kézzel a
  kalkulátort, írja be ugyanazt a négy értéket, és másolja át a sor új értékeit a két konstansba.

2026-10-21-én mért referenciaértékek a `Mistral Large 4 Preview` modellre:

| Bemenetek (input / response / reasoning / calls) | Cost per call | Total cost |
|---|---|---|
| 1000 / 500 / 1000 / 1000 (ezt használja a szkript) | $0.01 | $7.63 |
| 1000 / 3000 / 5000 / 1000 (az oldal alapértelmezései) | $0.03 | $34.80 |
| 1000 / 500 / 1000 / 10000 | $0.01 | $76.30 |

A középső sor a fontos: ha a szkript valaha `$34.80`-at jelez, akkor az űrlap az alapértelmezett
értékekkel lett elküldve.

## Hibaelhárítás

**1. `Executable doesn't exist at ...chrome-headless-shell.exe`**
A böngésző bináris nem lett letöltve. Futtassa: `playwright install chromium`. A pip csomag
telepítése önmagában ezt nem végzi el.

**2. `ModuleNotFoundError: No module named 'playwright'`**
A virtuális környezet nincs aktiválva, vagy a csomag másik interpreterbe került. Aktiválja a
venv-et, és futtassa újra: `pip install playwright`. Az aktuális interpreter ellenőrzése:
`python -c "import sys; print(sys.executable)"`.

**3. `TimeoutError` a keresett sorra várva**
Az eredménytábla nem jelent meg a `RESULTS_TIMEOUT_MS` (30 másodperc) alatt. Általában lassú
hálózat vagy oldalváltozás okozza. Állítsa a `HEADLESS` értékét `False`-ra, és nézze meg, mi
történik; a riport lépéstáblájából pontosan látszik, melyik lépésnél futott ki az idő.

**4. Az `expect(locator).to_have_count(1)` hibára fut az űrlapnál**
Megváltozott az oldal felépítése. Az űrlapot az azonosítja, hogy az tartalmazza az
`input[name="reasoning"]` mezőt, mivel az oldalon két "API calls" mező van — szekciónként egy. Az
elemek id-jait a React generálja (például `_r_14_-form-item`), és renderelésenként változnak, ezért
szándékosan nem használjuk őket.

**5. Az ellenőrzés `$7.63` helyett `$34.80`-at talál**
Az űrlap az alapértelmezett értékekkel lett elküldve. Ellenőrizze, hogy a 7. lépés sikeres volt-e a
riportban.

**6. Lefut, de szeretné látni működés közben**
Állítsa a `HEADLESS` értékét `False`-ra az `agent.py`-ban.

## Megjegyzések

- Nincs `requirements.txt`; az egyetlen függőség és a böngésző letöltése a 2. és 3. lépés két
  parancsa, amelyek az `agent.py` modul docstringjében is szerepelnek.
- Az első `playwright install chromium` hosszabb ideig tart — körülbelül 120 MB-ot tölt le.
- Egy teljes futás headless módban nagyjából 1,4 másodperc.
- A `.env` fájl még megvan a projektkönyvtárban, de az `agent.py` már nem olvassa. Törölhető, ha a
  projektben semmi más nem használja.
- Linuxon a Playwrighthoz kellhetnek további rendszerkönyvtárak:
  `playwright install-deps chromium`.
