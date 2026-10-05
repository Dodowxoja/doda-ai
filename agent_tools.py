"""
DODA agent asboblari (tools) — Claude "kod agenti" bo'lishi uchun.

Bu yerdagi har bir funksiya @beta_tool bilan bezatilgan — Claude ularni
o'zi chaqiradi (fayl o'qi, yoz, terminal buyruq bajar h.k.), tool_runner
esa aylanani (loop) avtomatik boshqaradi.

XAVFSIZLIK: hamma fayl amallari faqat WORKSPACE papkasi ichida ishlaydi
(papkadan tashqariga chiqolmaydi). Terminal buyruqlarida xavfli buyruqlar
(rm -rf /, sudo, disk formatlash h.k.) bloklanadi.

Buyruqlar asistent.py ichida EMAS — sizning tamoyilingizga ko'ra alohida faylda.
"""

import os
import re
import subprocess

from anthropic import beta_tool

# --- Sozlamalar ---
# Agent faqat shu papka ichida ishlaydi (fayl o'qish/yozish). Tashqariga chiqolmaydi.
WORKSPACE = os.path.expanduser("~/Code")
# Terminal buyruq uchun maksimal kutish vaqti (soniya).
COMMAND_TIMEOUT = 60
# Bitta o'qishda qaytariladigan maksimal belgilar (juda katta faylni cheklaydi).
MAX_READ_CHARS = 20000

# Terminalda MUTLAQO taqiqlangan naqshlar (regex). Xavfli/qaytarib bo'lmaydigan amallar.
_BLOCKED_PATTERNS = [
    r"\brm\s+-rf?\s+/",          # rm -rf /  (ildizni o'chirish)
    r"\brm\s+-rf?\s+~",          # rm -rf ~  (uy papkani o'chirish)
    r"\brm\s+-rf?\s+\*",         # rm -rf *  (hammasini o'chirish)
    r"\bsudo\b",                 # sudo     (administrator huquqi)
    r"\bmkfs\b",                 # disk formatlash
    r"\bdd\s+if=",               # disk yozish
    r">\s*/dev/",                # qurilmaga yozish
    r":\(\)\s*\{",               # fork bomb
    r"\bshutdown\b",             # o'chirish
    r"\breboot\b",               # qayta yuklash
    r"\bhalt\b",
    r"\bkillall\b",              # hamma jarayonni o'ldirish
    r"\bchmod\s+-R\s+777\b",     # ochiq ruxsat
    r"\bcurl\b.*\|\s*(sh|bash|zsh)\b",   # internetdan olib bajarish
    r"\bwget\b.*\|\s*(sh|bash|zsh)\b",
    r"\bgit\s+push\b.*--force",  # majburiy push
    r"\b>\s*/etc/",              # tizim fayllarini o'zgartirish
]


def set_workspace(path):
    """Agent ishlaydigan papkani o'zgartiradi (asistent.py chaqiradi)."""
    global WORKSPACE
    WORKSPACE = os.path.expanduser(path)


def _safe_path(path):
    """path'ni WORKSPACE ichida ekanini tekshiradi. Tashqarida bo'lsa xato beradi."""
    root = os.path.realpath(WORKSPACE)
    # Nisbiy yo'lni WORKSPACE'ga nisbatan hisoblaymiz
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    full = os.path.realpath(os.path.expanduser(path))
    if full != root and not full.startswith(root + os.sep):
        raise ValueError(
            f"Xavfsizlik: '{path}' ish papkasidan ({WORKSPACE}) tashqarida. Ruxsat yo'q."
        )
    return full


# ===== FAYL ASBOBLARI =====

@beta_tool
def read_file(path: str) -> str:
    """Read a text file and return its contents with line numbers.

    Use this to look at code or any text file before editing it.

    Args:
        path: File path, relative to the workspace or absolute inside it.
    """
    try:
        full = _safe_path(path)
    except ValueError as e:
        return f"XATO: {e}"
    if not os.path.isfile(full):
        return f"XATO: '{path}' fayli topilmadi."
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(MAX_READ_CHARS + 1)
    except Exception as e:
        return f"XATO: o'qib bo'lmadi — {e}"
    truncated = len(text) > MAX_READ_CHARS
    text = text[:MAX_READ_CHARS]
    numbered = "\n".join(f"{i+1}\t{ln}" for i, ln in enumerate(text.splitlines()))
    if truncated:
        numbered += "\n... (fayl uzun, qolgani ko'rsatilmadi)"
    return numbered or "(bo'sh fayl)"


@beta_tool
def write_file(path: str, content: str) -> str:
    """Create a new file or completely overwrite an existing one.

    For small edits to an existing file, prefer edit_file instead.

    Args:
        path: File path, relative to the workspace or absolute inside it.
        content: The full text to write into the file.
    """
    try:
        full = _safe_path(path)
    except ValueError as e:
        return f"XATO: {e}"
    try:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"XATO: yozib bo'lmadi — {e}"
    return f"OK: '{path}' saqlandi ({len(content)} belgi)."


@beta_tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace an exact piece of text in a file with new text.

    old_text must appear exactly once in the file. Read the file first to
    copy the exact text (including indentation) you want to replace.

    Args:
        path: File path, relative to the workspace or absolute inside it.
        old_text: The exact existing text to find (must be unique in the file).
        new_text: The replacement text.
    """
    try:
        full = _safe_path(path)
    except ValueError as e:
        return f"XATO: {e}"
    if not os.path.isfile(full):
        return f"XATO: '{path}' fayli topilmadi."
    try:
        with open(full, "r", encoding="utf-8") as f:
            data = f.read()
    except Exception as e:
        return f"XATO: o'qib bo'lmadi — {e}"
    count = data.count(old_text)
    if count == 0:
        return "XATO: old_text faylda topilmadi. Avval read_file bilan aniq matnni oling."
    if count > 1:
        return f"XATO: old_text faylda {count} marta uchradi. Uni noyob (unique) qiling."
    try:
        with open(full, "w", encoding="utf-8") as f:
            f.write(data.replace(old_text, new_text, 1))
    except Exception as e:
        return f"XATO: yozib bo'lmadi — {e}"
    return f"OK: '{path}' tahrirlandi."


@beta_tool
def list_dir(path: str = ".") -> str:
    """List files and folders inside a directory in the workspace.

    Args:
        path: Directory path, relative to the workspace or absolute inside it. Defaults to workspace root.
    """
    try:
        full = _safe_path(path)
    except ValueError as e:
        return f"XATO: {e}"
    if not os.path.isdir(full):
        return f"XATO: '{path}' papka emas yoki topilmadi."
    try:
        entries = sorted(os.listdir(full))
    except Exception as e:
        return f"XATO: {e}"
    if not entries:
        return "(bo'sh papka)"
    lines = []
    for name in entries:
        if name.startswith("."):
            continue
        p = os.path.join(full, name)
        lines.append(f"{name}/" if os.path.isdir(p) else name)
    return "\n".join(lines) or "(faqat yashirin fayllar bor)"


@beta_tool
def search_code(pattern: str, path: str = ".") -> str:
    """Search for a text pattern across files in the workspace (like grep).

    Returns matching lines with their file path and line number.

    Args:
        pattern: The text or regex to search for.
        path: Directory to search in, relative to the workspace. Defaults to workspace root.
    """
    try:
        full = _safe_path(path)
    except ValueError as e:
        return f"XATO: {e}"
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"XATO: noto'g'ri naqsh — {e}"
    hits = []
    for dirpath, dirnames, filenames in os.walk(full):
        # Katta/keraksiz papkalarni o'tkazib yuboramiz
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "node_modules", "__pycache__", ".venv", "venv", "build", "dist")]
        for fn in filenames:
            if fn.startswith("."):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if rx.search(line):
                            rel = os.path.relpath(fp, os.path.realpath(WORKSPACE))
                            hits.append(f"{rel}:{i}: {line.strip()[:200]}")
                            if len(hits) >= 50:
                                hits.append("... (juda ko'p natija, to'xtatildi)")
                                return "\n".join(hits)
            except Exception:
                continue
    return "\n".join(hits) if hits else "Hech narsa topilmadi."


# ===== TERMINAL ASBOBI =====

@beta_tool
def run_command(command: str) -> str:
    """Run a shell command in the workspace and return its output.

    Use for things like: git status, ls, python script.py, npm install,
    running tests. Dangerous commands (deleting the system, sudo, formatting
    disks) are blocked for safety.

    Args:
        command: The shell command to run.
    """
    low = command.lower()
    for pat in _BLOCKED_PATTERNS:
        if re.search(pat, low):
            return (f"BLOKLANDI: '{command}' xavfli buyruq hisoblanadi va bajarilmadi. "
                    "Xavfsizlik uchun bunday buyruqlar taqiqlangan.")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"XATO: buyruq {COMMAND_TIMEOUT} soniyada tugamadi (timeout)."
    except Exception as e:
        return f"XATO: {e}"
    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    parts = []
    if out:
        parts.append(out[:8000])
    if err:
        parts.append(f"[stderr]\n{err[:4000]}")
    parts.append(f"[exit code: {result.returncode}]")
    return "\n".join(parts)


# Barcha asboblar ro'yxati (asistent.py shuni import qiladi)
AGENT_TOOLS = [read_file, write_file, edit_file, list_dir, search_code, run_command]
