"""سكريبت فحص وبناء حزمة إضافة NVDA الرسمية (.nvda-addon)."""
import os, shutil, zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(BASE_DIR, "addon")
SRC_DIR = os.path.join(BASE_DIR, "src")
DIST_DIR = os.path.join(BASE_DIR, "dist")
TARGET_ADDON = os.path.join(DIST_DIR, "thaqqaf_nafsak-3.0.0.nvda-addon")

def _clean_pycache(folder: str) -> None:
    for root, dirs, files in os.walk(folder, topdown=False):
        for f in files:
            if f.endswith((".pyc", ".pyo", ".tmp")):
                os.remove(os.path.join(root, f))
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)

def build():
    print("بدء تجهيز حزمة إضافة NVDA: ثقف نفسك v3.0.0...")
    os.makedirs(DIST_DIR, exist_ok=True)
    _clean_pycache(ADDON_DIR)

    internal_src = os.path.join(ADDON_DIR, "globalPlugins", "thaqqaf_nafsak", "src")
    if os.path.exists(internal_src): shutil.rmtree(internal_src)
    shutil.copytree(SRC_DIR, internal_src, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.tmp"))

    if os.path.exists(TARGET_ADDON): os.remove(TARGET_ADDON)

    with zipfile.ZipFile(TARGET_ADDON, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ADDON_DIR):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith((".pyc", ".pyo", ".tmp")):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, ADDON_DIR)
                zf.write(full_path, rel_path)

    size_kb = os.path.getsize(TARGET_ADDON) / 1024
    print(f"تم بناء الحزمة بنجاح: {TARGET_ADDON} (الحجم: {size_kb:.2f} كيلوبايت)")

if __name__ == "__main__":
    build()
