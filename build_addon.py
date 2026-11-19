"""سكريبت فحص وبناء حزمة إضافة NVDA الرسمية (.nvda-addon)."""
import os, shutil, zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(BASE_DIR, "addon")
SRC_DIR = os.path.join(BASE_DIR, "src")
DIST_DIR = os.path.join(BASE_DIR, "dist")
TARGET_ADDON = os.path.join(DIST_DIR, "thaqqaf_nafsak-2.0.0.nvda-addon")

def build():
    print("بدء تجهيز حزمة إضافة NVDA: ثقف نفسك v2.0.0...")
    os.makedirs(DIST_DIR, exist_ok=True)

    internal_src = os.path.join(ADDON_DIR, "globalPlugins", "thaqqaf_nafsak", "src")
    if os.path.exists(internal_src): shutil.rmtree(internal_src)
    shutil.copytree(SRC_DIR, internal_src)

    if os.path.exists(TARGET_ADDON): os.remove(TARGET_ADDON)

    with zipfile.ZipFile(TARGET_ADDON, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(ADDON_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, ADDON_DIR)
                zf.write(full_path, rel_path)

    size_kb = os.path.getsize(TARGET_ADDON) / 1024
    print(f"تم بناء الحزمة بنجاح: {TARGET_ADDON} (الحجم: {size_kb:.2f} كيلوبايت)")

if __name__ == "__main__":
    build()
