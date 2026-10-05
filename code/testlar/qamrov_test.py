import sys, glob, collections
sys.path.insert(0, "/Users/dodow/Code/my_project/voice_ai")
import openpyxl

# --- Yon ta'sirlarni o'chirish (hech narsa ochilmasin/tarmoqqa chiqmasin) ---
import subprocess, webbrowser, urllib.request, os
_noop = lambda *a, **k: None
class _R:  # subprocess natijasi o'rniga
    returncode = 0; stdout = ""; stderr = ""
subprocess.run = lambda *a, **k: _R()
subprocess.Popen = lambda *a, **k: _R()
subprocess.call = lambda *a, **k: 0
subprocess.check_output = lambda *a, **k: b""
webbrowser.open = _noop
os.system = _noop
def _boom(*a, **k):
    raise RuntimeError("net-off")
urllib.request.urlopen = _boom

import code.asistent as asistent
asistent.say = _noop
asistent.say_random = _noop
asistent.AI_CHAT_ENABLED = False

def covered(cmd):
    """_dispatch moslashsa True. Handler mock I/O da yiqilsa ham = moslashgan."""
    try:
        if asistent._dispatch(cmd):
            return True
    except SystemExit:
        return True          # xayrlashuv
    except Exception:
        return True          # moslashdi, keyin mock I/O da yiqildi
    # autocorrect ikkinchi urinish
    try:
        corr = asistent._autocorrect(cmd)
        if corr != asistent._norm(cmd):
            try:
                if asistent._dispatch(corr):
                    return True
            except SystemExit:
                return True
            except Exception:
                return True
    except Exception:
        pass
    return False

total = 0
miss = 0
miss_by_intent = collections.Counter()
miss_samples = collections.defaultdict(list)

for f in sorted(glob.glob("/Users/dodow/Code/my_project/voice_ai/buyruqlar/pack/*.xlsx")):
    wb = openpyxl.load_workbook(f, read_only=True)
    ws = wb.active
    it = ws.iter_rows(values_only=True)
    hdr = next(it)  # header
    ci = hdr.index("Command")          # Command ustunini sarlavhadan top
    ii = hdr.index("Intent")
    for row in it:
        if not row or len(row) <= ci:
            continue
        intent, cmd = row[ii], row[ci]
        if not cmd:
            continue
        total += 1
        if not covered(str(cmd)):
            miss += 1
            miss_by_intent[intent] += 1
            if len(miss_samples[intent]) < 6:
                miss_samples[intent].append(str(cmd))
    wb.close()

print("=" * 50)
print("JAMI:", total, " QAMROV:", round(100*(total-miss)/total, 2), "%",
      " (mos kelmagan:", miss, ")")
print("=" * 50)
print("MOS KELMAGANLAR (intent bo'yicha):")
for intent, n in miss_by_intent.most_common():
    print(f"  {intent:28} {n:6}   e.g. {miss_samples[intent][:3]}")
