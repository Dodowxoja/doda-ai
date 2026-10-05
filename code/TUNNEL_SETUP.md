# DODA — Doimiy (o'zgarmas) tunnel sozlash

Bepul `trycloudflare` tunnel har qayta ishga tushganда **yangi URL** oladi — Telegram Mini App uchun noqulay. Doimiy URL uchun **Cloudflare named tunnel** sozlanadi (bir marta). Buning uchun sizда **Cloudflare akkaunt** va **domen** bo'lishi kerak (bepul akkaunt yetadi; domen — masalan `.uz` yoki `.com`).

## Sozlash (bir martalik, terminalda O'ZINGIZ bajarasiz)

1. Cloudflare'ga kirish (brauzer ochiladi):
   ```
   cloudflared tunnel login
   ```

2. Tunnel yaratish (masalan nomi `doda`):
   ```
   cloudflared tunnel create doda
   ```
   Bu `~/.cloudflared/<UUID>.json` hisob faylini yaratadi.

3. DNS'ни ulash (masalan `doda-ai.uz`):
   ```
   cloudflared tunnel route dns doda doda-ai.uz
   ```

4. `~/.cloudflared/config.yml` yarating:
   ```yaml
   tunnel: doda
   credentials-file: /Users/dodow/.cloudflared/<UUID>.json
   ingress:
     - hostname: doda-ai.uz
       service: http://localhost:8765
     - service: http_status:404
   ```

5. DODA'ga doimiy tunnelni aytish — `~/.doda_named_tunnel` faylini yarating (2 qator):
   ```
   echo "doda" > ~/.doda_named_tunnel
   echo "https://doda-ai.uz" >> ~/.doda_named_tunnel
   chmod 600 ~/.doda_named_tunnel
   ```

6. Tunnelни qayta ishga tushiring:
   ```
   launchctl kickstart -k gui/$(id -u)/com.doda.tunnel
   ```

## Natija
- URL endi **hech qаchon o'zgarmaydi**: `https://doda-ai.uz/`
- `/app` har doim shu barqaror havolаni beradi — Mini App ishonchli ochiladi.
- Brauzer ovozли rejimi ham ishlaydi (HTTPS).

## Eslatma
- `~/.doda_named_tunnel` fayli **bo'lmasa**, DODA avvalgidek vaqtinchalik (quick) tunnel ishlatadi — hech narsa buzilmaydi.
- Domen bo'lmasa: Cloudflare Zero Trust'да bepul `*.cfargotunnel.com` yoki boshqa provayder (masalan `ngrok` doimiy domen — pullik) ham variant.
