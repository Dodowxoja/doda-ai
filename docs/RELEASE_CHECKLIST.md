# DODA — Release Checklist

> Har **production release**дан oldin to'liq bajarilادi. Biror band ❌ bo'lса — release YO'Q.
> Har release'да nusxa olib belgilanadi.

---

## 🔒 Kod sifati
- [ ] **Tests passed** — unit + integration + contract (barcha yashил)
- [ ] **Coverage** ≥ 80% (yadro mantiqда)
- [ ] **Type checking** — `mypy --strict` toza
- [ ] **Lint** — `ruff` toza
- [ ] **Format** — `black` toza
- [ ] Vaqtinchalik kod / `TODO` / quick-fix YO'Q

## 📚 Hujjatlar
- [ ] **Documentation** yangilangan (README, arxitektura, API)
- [ ] **CHANGELOG.md** yangi versiya bilan
- [ ] **Release Notes** yozildi ([RELEASE_NOTES pattern])
- [ ] Yangi/o'zgargan API `/api/v1` hujjatlanган

## 🔢 Versiya
- [ ] **Version bump** — `VERSION` + `pubspec.yaml` + tag (SemVer)
- [ ] Migratsiya kerak bo'lса — skript + test tayyor

## 🔐 Xavfsizlik
- [ ] **Security Review** — sir kodда/logда yo'q; auth ishlaydi
- [ ] Sirlar keychain'да; DB shifri; token-xesh
- [ ] Yangi ruxsat/permission ko'rib chiqildi
- [ ] Bog'liqlik (deps) zaiflik skani

## ⚡ Performance & Barqarorlik
- [ ] **Performance Check** — CPU/RAM/latency me'yorда (24/7 sizish yo'q)
- [ ] Watchdog/health ishlaydi
- [ ] Battery-aware (desktop)

## 📦 Packaging & Installer
- [ ] **Packaging** — Python binar (har OS) quriladi
- [ ] **Installer** — DMG (mac 2 arch) / MSI-EXE / AppImage / DEB
- [ ] **Kod imzo** — macOS notarization + Windows sign (yoki ogohlantirish qayd etilган)
- [ ] **Auto-update** feed yangilanган + imzo tekshirildi
- [ ] Toza mashinада o'rnatish sinovдан o'tди

## 🧪 QA
- [ ] **Manual QA** — asosiy oqim (chat/voice/vision/tasks/settings) qo'lда sinaldi
- [ ] Har OS (mac/win/linux) da smoke-test
- [ ] Eski v1.0.0 buzilmagani tasdiqlanди (migratsiya davri)

## 💾 Zaxira & Chiqarish
- [ ] **Backup** — foydalanuvchi DB/config zaxirasi (migratsiya oldidan)
- [ ] **CI/CD** yashил — GitHub Actions barcha job o'tди
- [ ] GitHub Release + installerlar yuklandi
- [ ] Rollback rejasi tayyor (auto-update buzilса)

---

## Yakuniy
- [ ] **Release Manager tasdig'i** (barcha yuqoridagilar ✅)
- [ ] Release e'lon qilindi
- [ ] Post-release monitoring (Telemetry) kuzatilyapti

> Har band [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) + [RISK_REGISTER.md](RISK_REGISTER.md) bilan bog'liq.
