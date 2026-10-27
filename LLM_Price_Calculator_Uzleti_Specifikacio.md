# BA-SPEC-LLMPC-001 – LLM Price Calculator – Üzleti specifikáció

---

## Dokumentum azonosító

- **Dokumentum azonosító:** BA-SPEC-LLMPC-001
- **Verzió:** 1.0
- **Dátum:** 2026-10-20
- **Szerző:** Üzleti elemző (Business Analyst) – ISTQB CT-GenAI gyakorlati anyag
- **Státusz:** Felülvizsgálatra kész (Ready for review)

---

## Vizsgált rendszer

- **Rendszer neve:** Artificial Analysis – LLM Price Calculator
- **Vizsgált URL:** [https://artificialanalysis.ai/tools/llm-price-calculator](https://artificialanalysis.ai/tools/llm-price-calculator)
- **Forrás / validálás módja:** Élő bőngészős bejárás (Playwright-alapú automatizálás), 2026-10-20
- **Célközönség:** QA hallgatók – teszt oracle és tesztesetek készítése gyakorlat céljából

---

## Jognyilatkozat és a dokumentum eredete

Ez a dokumentum oktatási célra készült az ISTQB® CT-GenAI tanfolyam gyakorlati feladatához. A dokumentum egy ténylegesen létező, nyilvánosan elérhető weboldal (artificialanalysis.ai) egyetlen aloldalának ("slug": /tools/llm-price-calculator) 2026-10-20-án megfigyelt viselkedését írja le üzleti specifikáció formájában.

**Fontos:**
- A dokumentum NEM az Artificial Analysis cég hivatalos specifikációja
- A cég nem hagyta jóvá
- Nem feltétlenül tükrözi a rendszer jövőbeli vagy nem dokumentált működését
- A dokumentumot kizárólag oktatási céllal, tesztelési gyakorlat alapjául hozták létre

---

# 1. Bevezetés

A jelen üzleti specifikáció az Artificial Analysis portál "LLM Price Calculator" nevű eszközét írja le, amelynek célja, hogy a felhasználók token- vagy szóalapú bemenetek megadásával összehasonlíthassák a különböző nagy nyelvi modellek (LLM-ek) árazását egy adott felhasználási forgatókönyvre vetítve.

A specifikáció célja, hogy elegendő részletességgel írja le a funkcionális működést ahhoz, hogy abból teszt oracle-ök (elvárt eredmények) és tesztesetek legyenek levezethetők.

---

# 2. Üzleti háttér

**Üzleti háttér:** A vállalatok és fejlesztők egyre több nagy nyelvi modell közül választhatnak API-alapú integrációhoz. A modellek árazása szolgáltatónként és modellenként eltérő:

- Bemeneti token
- Kimeneti token
- Reasoning ("gondolkodó") modellek esetén a belső gondolkodási token alapján

A felhasználóknak jelenleg nincs egyszerű módjuk arra, hogy egy konkrét üzleti forgatókönyv (pl. napi 10 000 chatbot-hívás) becsült havi/összesített költségét gyorsan összehasonlítsák több modell között.

Az **LLM Price Calculator** ezt a hiányt hivatott pótolni egy önkiszolgáló, böngészőben futó kalkulátor formájában.

---

# 3. Célkitűzés

**Cél:** A felhasználó adjon meg egy felhasználási mintát (tokenszámok vagy natural language promptok formájában), válasszon ki egy vagy több LLM modellt, és kapjon vissza egy rendezhető táblázatot, amely modellenként bontva mutatja a becsült:

- Bemeneti költséget
- Kimeneti költséget
- Reasoning költséget
- Teljes költséget

Egy megadott API-hívásszámra vetítve.

---

# 4. Érintettek (Stakeholders)

| Érintett | Leírás |
|----------|--------|
| **Végfelhasználó** (fejlesztő / termékmenedzser / beszerzési döntéshozó) | Összehasonlítja a modellek árazását egy tervezett integráció előtt |
| **Artificial Analysis szerkesztőség** | Karbantartja a modell- és árazási adatbázist (444 modell, 1198 modell-szolgáltató kombináció a megfigyelés idején) |
| **QA / oktatási célközöség** (jelen dokumentum kontextusában) | A specifikációból teszteseteket és teszt oracle-öket vezet le, és ellenőrzi a dokumentum belső konzisztenciáját |

---

# 5. Felhasználói szerepkörök (perszónák)

| Szerepkör | Leírás |
|-----------|--------|
| **Beszerzési döntéshozó** | Gyors, nagyságrendi összehasonlítást keres több modell között egy üzleti esethez; nem feltétlenül ismeri a tokenizálás technikai részleteit, ezért valószínűbb, hogy a szóalapú ("Words") módot használja |
| **Fejlesztő / megoldásépítő** | Pontosan ismeri a várható token-mennyiségeket (pl. monitorozásból), ezért a tokenalapú módot használja, és konkrét modell-szolgáltató kombinációkat ad hozzá |

---

# 6. Hatókör

## 6.1 A specifikáció hatókörébe tartozik:

- [ ] A `/tools/llm-price-calculator` oldal tokenalapú ("Tokens") számítási módja
- [ ] A `/tools/llm-price-calculator` oldal szóalapú ("Words") számítási módja
- [ ] A három elvořre definiált terhelési sablon (Chatbot conversation, Code generation, Large doc processing) és azok "Apply" funkciója
- [ ] A modellválasztó komponens (modellek kiválasztása, keresés, szűrés, mentés/betöltés)
- [ ] A "modell és szolgáltató kombináció" hozzáadása konkrét szolgáltatóhoz kötve
- [ ] Az eredményáblázat megjelenése, oszlopai és rendezési funkciója
- [ ] A "Calculate" gomb viselkedése mindkét számítási módban

## 6.2 A specifikáció hatókörén kívül esik:

- [ ] A weboldal egyéb aloldalai (Models, Coding Agents, Leaderboards, Inference stb.)
- [ ] A "Premium" előfizetés és a "Log in" mögötti funkciók
- [ ] A hírlevél-feliratkozás ("Get notified about new articles") funkció
- [ ] A mobil natív alkalmazás – a specifikáció kizárólag az asztali böngészős nézetet dokumentálja 1516 px széles viewport mellett
- [ ] A tényleges szolgáltatói (OpenAI, Anthropic, Google stb.) számlázási API-k pontossága – ez a kalkulátor becslést ad, nem hivatalos számlát

---

# 7. Funkcionális követelmények

## FR-01 – Tokenalapú számítási mód ("Tokens" fül)

A felhasználó négy numerikus mezőt tölthet ki, amelyek alapján a rendszer modellenként kiszámítja a becsült költséget.

| Mező | Leírás | Alapértelmezett érték |
|------|--------|---------------------|
| **Input tokens** | A bemeneti promptban szereplő tokenek becsült száma | 1000 |
| **Response tokens** | A modell válaszában szereplő tokenek becsült száma | 3000 |
| **Reasoning tokens** | A modell belső "gondolkodási" tokenjeinek becsült száma. A mező felirata alatt megjelenő segédszöveg: "Reasoning models only" | 5000 |
| **API calls** | Az adott felhasználási mintázat hányszor ismétlődik | 1000 |

Mindegyik mező mellett egy (i) információs ikon jelenik meg, amely feltehetően további magyarázó szöveget (tooltip) ad.

---

## FR-02 – Szóalapú számítási mód ("Words" fül)

A "Tokens" és "Words" fülek kölcsönösen kizárják egymást: egy adott pillanatban csak az egyik beviteli forma látható.

A "Words" fülön a felhasználó természeti nyelvű szöveget ad meg a tokenszámok helyett.

| Mező | Helyőrző szöveg |
|------|----------------|
| **System prompt** | "You are a helpful assistant." |
| **User prompt** | "Write a summary about renewable\nenergy." |
| **Response** | "Renewable energy offers many benefits..." |
| **Reasoning** | "Let me think about the key benefits: 1) Environmental, 2) Economic..." |
| **API calls** | Azonos jelentésű mező, mint a Tokens fülön, de a két fül API calls értéke egymástól függetlenül tárolódik |

A fül tetején megjelenő figyelmeztető szöveg szó szerint:
> "Token counts are estimated with o200k_base. Actual billed tokens may vary by provider/model due to system formatting, special tokens, and tokenizer differences."

---

## FR-03 – Előre definiált terhelési sablonok (Presets)

A Tokens fülön három előre definiált sablon jelenik meg kártya formában, mindegyik saját "Apply" gombbal:

- Chatbot conversation
- Code generation
- Large doc processing

Az "Apply" gomb megnyomása a sablonhoz tartozó előre definiált értékekkel felülírja a Input tokens, Response tokens, Reasoning tokens és API calls mezőket.

**Megfigyelt példa:** A "Chatbot conversation" sablon alkalmazása után a mezők értéke:
- Input tokens = 1000
- Response tokens = 2000
- Reasoning tokens = 1000
- API calls = 10000

(Az eredeti 1000 / 3000 / 5000 / 1000 alapértelmezett értékek helyett).

A sablon alkalmazása önmagában NEM indítja el az újraszámítást – ehhez külön meg kell nyomni a Calculate gombot.

A sablonkártya fejlécén egy "+" ikon is látható; ennek pontos funkciója a megfigyelés során nem derült ki.

---

## FR-04 – Modellválasztó és szűrés

A bal oldali panel tetején egy légördülő lista jeleníti meg a jelenleg kiválasztott és az összesen elérhető modellek számát, a megfigyelés idején "26 of 444 models" formában.

A légördülő lista megnyitásakor keresőmező, majd a modellek listája jelenik meg (pipálható elemek, szolgáltatói logóval és névvel).

**Műveletek a lista alján:**
- "Clear" (kijelölés törlése)
- "Select all" (összes kijelölése)
- "Reset (to default)" (alapértelmezett 26 modellre visszaállítás)
- "Save" (aktuális kijelölés mentése)
- "Load" (korábban mentett kijelölés betöltése)

A lista melletti túlcsúszó ikon ("Filters") egy szűrőpanelt nyit meg az alábbi, külön címsorokkal csoportosított kategóriákkal:

- "Open Weights" (Open Source / Proprietary)
- "Size Class" (Tiny / Small / Medium / Large / Custom)
- "Reasoning" (Reasoning / Non Reasoning)
- "Input Modality" (Image / Speech / Video)

A szűrőpanel további, a megfigyelés során nem begörgetett kategóriákat is tartalmazhat.

---

## FR-05 – Modell és szolgáltató kombináció hozzáadása

A modellszámló doboz alatt megjelenik egy másodlik, hasonló felépítésű légördülő lista "0 of 1198 model & provider combinations" felirattal (alapértelmezetten "+ Add model from specific provider" gombként jelenik meg, amíg nincs kibontva).

Ez a lista azokat az eseteket kezeli, amikor ugyanazt a modellt több szolgáltató (pl. Amazon Bedrock, Vertex AI, közvetlen gyártói API) is kínálja eltérő árazással.

A lista szintén rendelkezik kereső mezővel.

---

## FR-06 – Számítás indítása ("Calculate" gomb)

Mindkét fülön (Tokens és Words) saját "Calculate" gomb található a beviteli mezők alatt.

A Calculate gomb megnyomása az aktuális fülön megadott bemeneti értékek alapján újraszámítja és megjeleníti az eredményáblázatot a jobb oldali panelen.

**Megfigyelt viselkedés:** A beviteli mezők módosítása VAGY a Tokens/Words fülek közötti váltás önmagában NEM frissíti automatikusan a már megjelenített eredményáblázatot; a táblázat mindaddig a korábbi számítás eredményét mutatja, amíg a felhasználó újra meg nem nyomja a Calculate gombot.

---

## FR-07 – Eredménytáblázat

A jobb oldali panelen megjelenő táblázat a kiválasztott modelleket sorolja fel, az alábbi oszlopokkal:

| Oszlop | Leírás |
|--------|--------|
| **Model** | A modell neve, alatta kisebb betűmérettel a szolgáltató neve (pl. Anthropic, OpenAI, Google, Alibaba, DeepSeek, Z AI, StepFun, Kimi, MiniMax, Meta, Mistral, SpaceXAI, Xiaomi, Institute of Foundation Models, Reflection, NVIDIA, Thinking Machines stb.) |
| **Input cost** | A bemeneti tokenek/szöveg becsült költsége |
| **Response cost** | A válasz tokenek/szöveg becsült költsége |
| **Reasoning cost** | A reasoning tokenek becsült költsége (nem reasoning modelleknél megfigyelt értékek: "< $0.01" vagy "$0.00", sosem üres mező) |
| **Cost per call** | Egyszeri API-hívás teljes becsült költsége (bemenet + válasz + reasoning) |
| **API calls** | A számításhoz megadott hívásszám |
| **Total cost** | A teljes becsült költség (Cost per call × API calls) |

A nagyon alacsony (1 cent alatti) költségeket a rendszer "< $0.01" formában jeleníti meg.

---

## FR-08 – Rendezés az eredményáblázatban

Minden numerikus oszlop fejlécében (Input cost, Response cost, Reasoning cost, Cost per call, Total cost) egy fel-le nyilakból álló rendezésikon található.

Az ikonra kattintva a táblázat az adott oszlop szerint rendeződik.

**Megfigyelve:** A Total cost oszlopra kattintva a táblázat csökkenő sorrendbe rendeződött (legdrágább modell felül).

---

## FR-09 – Modellkiválasztás mentése és betöltése

A modellválasztó lista alján elérhető "Save" és "Load" funkciók lehetővé teszik egy adott modell-kiválasztási kombináció elmentését és későbbi visszatöltését.

A mentett kiválasztás hatóköre (böngésző-munkamenet, böngésző helyi tárolója, vagy bejelentkezett felhasználó esetén fiókhoz kötött tárolás) a megfigyelés során nem került tisztázásra.

---

## FR-10 – Váltás a Tokens és Words módok között

A bal oldali panel tetején lévő "Tokens" / "Words" kapcsoló (tab) vezérli, hogy melyik beviteli forma látható.

A váltás megőrizi mindkét fül korábban beírt értékeit.

A lap kezdeti, még nem számított állapotában a Tokens és Words kalkulátor egyszerre, egymás mellett jelenik meg, külön-külön "Calculate" gombbal, eredményáblázat nélkül.

Az első Calculate gomb megnyomása után a nézet "eredmény állapotba" vált, ahol a két mód fül formájában, egymást kizáró módon jelenik meg, és egy közös eredményáblázat látható jobb oldalon.

---

# 8. Drótvázak (Wireframes)

Az alábbi két drótváz a felület két fő állapotát mutatja be:

1. **Kezdeti állapot:** A Tokens és a Words kalkulátor egymás mellett, eredményáblázat nélkül
2. **Eredmény állapot:** Modellválasztó + szűrő + fülváltó + bemeneti mezők balra, közös rendezhető eredményáblázat jobbra

A drótvázak alacsony hűségű (low-fidelity) vázlatok, amelyek a 2026-10-20-i élő megfigyelés alapján készültek; pontos pixelarányokat és márkaszíneket nem tükröznek.

---

# 9. Üzleti szabályok (Business Rules)

| Azonosító | Szabály |
|-----------|--------|
| **BR-01** | A "Cost per call" oszlop értéke az adott sor Input cost, Response cost és Reasoning cost értékeinek összege |
| **BR-02** | A "Total cost" oszlop értéke a "Cost per call" és az "API calls" mező szorzata |
| **BR-03** | A tokenszámok becslése az o200k_base nevű tokenizálóval történik a Words módban; a dokumentum megjegyzi, hogy "a ténylegesen számlázott tokenszám szolgáltatónként/modellenként eltérhet a rendszerformázás, speciális tokenek és eltérő tokenizálók miatt" – ez a kalkulátor tehát becslést, nem garantált árajánlatot ad |
| **BR-04** | Az eredményáblázat csak a "Calculate" gomb megnyomásakor frissül; a bemeneti mezők, a sablonok vagy a modellválasztás módosítása önmagában nem váltja ki az újraszámítást |
| **BR-05** | A Tokens és a Words fülön megadott "API calls" érték egymástól független állapotot képvisel (külön-külön tárolódik) |
| **BR-06** | Egy modellsor Reasoning cost értéke nem reasoning típusú modellek esetén is megjelenik (jellemzően "< $0.01" vagy "$0.00" értékekkel), annak ellenére, hogy a Reasoning tokens bemeneti mező segédszövege szerint ez a mező "Reasoning models only" jellegű |

---

# 10. Nem-funkcionális követelmények

| Azonosító | Követelmény | Leírás |
|-----------|-------------|--------|
| **NFR-01** | **Használhatóság** | A kalkulátor használatához nem szükséges bejelentkezés; a "Premium" és "Log in" funkciók a core kalkulátor funkcionalitástól függetlenek |
| **NFR-02** | **Teljesítmény** | A modellválasztó lista 444 modellt és 1198 modell-szolgáltató kombinációt kezel; a keresőmező valós idejű szűrést biztosít a listában |
| **NFR-03** | **Böngésző-kompatibilitás** | A megfigyelés Chromium-alapú asztali böngészőben, 1516–1568 px széles nézetben történt; más böngészőkre/nézetekre vonatkozó állítás a dokumentumban nem szerepel |
| **NFR-04** | **Nyelvezét** | A felhasználói felület angol nyelvű; magyar lokalizációra utaló elem a megfigyelés során nem volt található |
| **NFR-05** | **Pontosság / felelősség kizárása** | A felületen megjelenő figyelmeztető szöveg egyértelművé teszi, hogy a becsült értékek eltérhetnek a tényleges számlázástól |

---

# 11. Elfogadási kritériumok

Az alábbi elfogadási kritériumok Given/When/Then (Adott/Amikor/Akkor) szerkezetben, de magyar nyelven, folyó szövegben kerülnek megfogalmazásra. Ezek közvetlenül felhasználhatók teszteset-tervezéshez és teszt oracle meghatározásához.

## AC-01 – Alapértelmezett mezőértékek (Tokens mód)

Amikor a felhasználó először nyitja meg az oldalt és a Tokens fület, akkor:
- Az Input tokens mező értéke 1000
- A Response tokens mező értéke 3000
- A Reasoning tokens mező értéke 5000
- Az API calls mező értéke 1000

## AC-02 – Chatbot conversation sablon alkalmazása

Amikor a felhasználó a Chatbot conversation kártyán az Apply gombra kattint, akkor:
- Az Input tokens, Response tokens, Reasoning tokens és API calls mezők értéke a sablonhoz tartozó előre definiált értékekre változzon (megfigyelt érték: 1000 / 2000 / 1000 / 10000)
- Az eredményáblázat eddigi tartalma változatlan maradjon mindaddig, amíg a Calculate gombot meg nem nyomják

## AC-03 – Total cost számítása

Amikor a felhasználó megnyomja a Calculate gombot egy adott API calls értékkel, akkor minden megjelenített sorban a Total cost oszlop értékének meg kell egyeznie a Cost per call és az API calls szorzatával.

## AC-04 – Rendezés Total cost szerint

Amikor a felhasználó a Total cost oszlop rendezés ikonjára kattint, akkor a táblázat sorainak a Total cost oszlop szerint, csökkenő sorrendben kell megjelenniük (legnagyobb értékek felül).

## AC-05 – Fülváltás nem indít újraszámítást

Amikor a felhasználó a Words fülről átvált a Tokens fülre (vagy fordítva) anélkül, hogy megnyomná a Calculate gombot, akkor a jobb oldali eredményáblázatnak változatlannak kell maradnia (a legutóbb kiszámított módhoz tartozó adatokat kell mutatnia).

## AC-06 – Modellszám visszaállítása

Amikor a felhasználó a modellválasztó listában a "Reset (to default)" opcióra kattint, akkor a kiválasztott modellek számának vissza kell állnia az alapértelmezett 26 modellre.

## AC-07 – Szöveges helyőrzők a Words módban

Amikor a felhasználó megnyitja a Words fület, és az System prompt, User prompt, Response és Reasoning mezők üresek, akkor a mezőknek a specifikációban rögzített angol nyelvű helyőrző szöveget kell mutatniuk.

---

# 12. Verziótörténet

| Verzió | Dátum | Leírás |
|--------|-------|--------|
| 1.0 | 2026-10-20 | Első kiadás – élő rendszermegfigyelés alapján |

---

*Dokumentum vége*
