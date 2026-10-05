"""
DODA ko'rish (vision) moduli — kamera va ekrandan rasm oladi.

TUZILISH (3 qatlam):
  1. RASM OLISH (Claude'siz):
       capture_screen()  — ekran surati (screencapture, built-in)
       capture_camera()  — webcam'dan bitta kadr (ffmpeg avfoundation)
  2. TUSHUNISH (Claude API orqali, asistent.py'da):
       rasmni Claude'ga yuborib, nima ko'rinayotganini aytadi
  3. YUZ XOTIRA (lokal face_recognition kutubxonasi — o'rnatilgan, ishlaydi):
       remember_face(), identify_faces()  — yuzni ism bilan saqlab, keyin taniydi.

Buyruqlar asistent.py ichida EMAS — alohida faylda (sizning tamoyilingizga ko'ra).
"""

import os
import time
import base64
import tempfile
import subprocess

# --- Sozlamalar ---
CAMERA_INDEX = "0"          # ffmpeg avfoundation video qurilma raqami (0 = FaceTime HD Camera)
CAMERA_SIZE = "1280x720"    # kamera kadr o'lchami
FACES_DIR = os.path.expanduser("~/.doda_faces")   # tanilgan yuzlar shu yerda saqlanadi


def _tmp(prefix, ext="jpg"):
    return os.path.join(tempfile.gettempdir(), f"{prefix}_{int(time.time()*1000)}.{ext}")


# ===== 1-QATLAM: RASM OLISH (Claude'siz ishlaydi) =====

def capture_screen(path=None, fmt="png"):
    """Ekran suratini oladi. Rasm fayl yo'lini qaytaradi (yoki None).
    fmt='png' — matn tiniqroq chiqadi (standart); 'jpg' — kichikroq hajm."""
    path = path or _tmp("doda_screen", "png" if fmt == "png" else "jpg")
    try:
        # -x = tovushsiz; -t = format (png tiniqroq, jpg kichikroq)
        subprocess.run(["screencapture", "-x", "-t", fmt, path],
                       check=False, timeout=15)
    except Exception as e:
        print("capture_screen xato:", e)
        return None
    return path if os.path.exists(path) and os.path.getsize(path) > 0 else None


def capture_camera(path=None):
    """Webcam'dan bitta kadr oladi (ffmpeg). Rasm fayl yo'lini qaytaradi (yoki None).

    Eslatma: birinchi ishlatilganda macOS kamera ruxsatini so'raydi.
    Birinchi kadrlar qora/yashil bo'lishi mumkin, shuning uchun bir nechta kadr
    olib, oxirgisini saqlaymiz (-frames:v 6 + -update 1).
    """
    path = path or _tmp("doda_cam")
    cmd = [
        "ffmpeg", "-y",
        "-f", "avfoundation",
        "-framerate", "30",
        "-video_size", CAMERA_SIZE,
        "-i", CAMERA_INDEX,
        "-frames:v", "6",       # bir nechta kadr (isishi uchun)
        "-update", "1",         # har kadrda shu faylni yangilab boradi -> oxirgisi qoladi
        path,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        print("capture_camera: timeout (kamera javob bermadi)")
        return None
    except Exception as e:
        print("capture_camera xato:", e)
        return None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    # Ruxsat berilmagan bo'lsa ffmpeg xato beradi
    if "permission" in (r.stderr or "").lower() or "denied" in (r.stderr or "").lower():
        print("capture_camera: kamera ruxsati yo'q (System Settings > Privacy > Camera)")
    return None


def record_camera(seconds=5, path=None):
    """Webcam'dan qisqa video yozadi (standart 5 soniya). MP4 fayl yo'lini qaytaradi."""
    path = path or _tmp("doda_camvid", "mp4")
    cmd = [
        "ffmpeg", "-y", "-f", "avfoundation",
        "-framerate", "30", "-video_size", CAMERA_SIZE,
        "-i", CAMERA_INDEX, "-t", str(seconds),
        "-pix_fmt", "yuv420p", path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=seconds + 20)
    except Exception as e:
        print("record_camera xato:", e)
        return None
    return path if os.path.exists(path) and os.path.getsize(path) > 1000 else None


def record_screen(seconds=5, path=None):
    """Ekrandan qisqa video yozadi (standart 5 soniya). macOS 'screencapture -V'.
    MOV fayl yo'lini qaytaradi."""
    path = path or _tmp("doda_scrvid", "mov")
    try:
        # -V <sekund> = video yozish; -x = tovushsiz
        subprocess.run(["screencapture", "-x", "-V", str(seconds), path],
                       check=False, timeout=seconds + 20)
    except Exception as e:
        print("record_screen xato:", e)
        return None
    return path if os.path.exists(path) and os.path.getsize(path) > 1000 else None


def image_to_base64(path):
    """Rasmni base64 ga o'giradi (Claude'ga yuborish uchun). (data, media_type) qaytaradi."""
    ext = os.path.splitext(path)[1].lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


# ===== 2-QATLAM: TUSHUNISH (Claude kerak) =====
# Bu qism asistent.py da chaqiriladi (u yerda Claude klienti bor).
# describe_image() ni asistent.py ichida yozamiz, chunki Claude klienti o'sha yerda.
# Bu yerda faqat rasm tayyorlab beramiz (yuqoridagi funksiyalar).


# ===== 3-QATLAM: YUZ XOTIRA (lokal, face_recognition kutubxonasi kerak) =====

def _faces_available():
    """face_recognition kutubxonasi o'rnatilganmi?"""
    try:
        import face_recognition  # noqa: F401
        return True
    except Exception:
        return False


def remember_face(name, image_path, only_unknown=False):
    """Rasmdan yuzni topib, ism bilan saqlaydi (keyingi tanish uchun).

    only_unknown=True bo'lsa VA allaqachon tanilgan yuzlar bo'lsa — rasmdagi
    ALLAQACHON TANILGAN yuzni emas, NOTANISH (yangi) yuzni saqlaydi. Bu «men +
    yonimda yangi odam» holatida yangi odamni to'g'ri eslab qolish uchun.

    face_recognition kutubxonasi kerak. O'rnatilmagan bo'lsa (False, sabab) qaytaradi.
    """
    if not _faces_available():
        return False, "Yuz tanish kutubxonasi hali o'rnatilmagan (face_recognition)."
    import face_recognition
    import numpy as np
    os.makedirs(FACES_DIR, exist_ok=True)
    img = face_recognition.load_image_file(image_path)
    encs = face_recognition.face_encodings(img)
    if not encs:
        return False, "Rasmda yuz topilmadi."
    chosen = encs[0]
    if only_unknown and len(encs) > 1:
        # tanilgan yuzlarni yuklaymiz, mos kelmaydigan (notanish) yuzni tanlaymiz
        known = []
        if os.path.isdir(FACES_DIR):
            for fn in os.listdir(FACES_DIR):
                if fn.endswith(".npy"):
                    try:
                        known.append(np.load(os.path.join(FACES_DIR, fn)))
                    except Exception:
                        pass
        for e in encs:
            if not known or True not in face_recognition.compare_faces(known, e, tolerance=0.6):
                chosen = e
                break
    np.save(os.path.join(FACES_DIR, f"{name}.npy"), chosen)
    return True, f"{name} yuzini eslab qoldim."


def identify_faces(image_path, tolerance=0.6):
    """Rasmdagi yuzlarni saqlangan yuzlar bilan solishtiradi. Ismlar ro'yxatini qaytaradi.

    face_recognition kerak. O'rnatilmagan bo'lsa (None, sabab) qaytaradi.
    """
    if not _faces_available():
        return None, "Yuz tanish kutubxonasi hali o'rnatilmagan (face_recognition)."
    import face_recognition
    import numpy as np
    if not os.path.isdir(FACES_DIR):
        return [], "Hali hech kimning yuzi saqlanmagan. Meni yodlashim uchun kameraга qarab «meni eslab qol» deng."
    known_names, known_encs = [], []
    for fn in os.listdir(FACES_DIR):
        if fn.endswith(".npy"):
            known_names.append(fn[:-4])
            known_encs.append(np.load(os.path.join(FACES_DIR, fn)))
    if not known_encs:
        return [], "Hali hech kimning yuzi saqlanmagan. Meni yodlashim uchun kameraга qarab «meni eslab qol» deng."
    img = face_recognition.load_image_file(image_path)
    found = []
    for enc in face_recognition.face_encodings(img):
        matches = face_recognition.compare_faces(known_encs, enc, tolerance=tolerance)
        name = "notanish"
        if True in matches:
            name = known_names[matches.index(True)]
        found.append(name)
    return found, None
