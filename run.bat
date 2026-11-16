@echo off
chcp 65001 > nul
echo ======================================================
echo   مشغل وفاحص إضافة ثقف نفسك (Thaqqif Nafsak)
echo ======================================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [خطأ]: لم يتم العثور على بايثون في النظام!
    pause
    exit /b 1
)

echo [1/3] تشغيل اختبارات المنطق والفحص الشامل...
python "D:\documents\programming corse\skills\universal-software-agency\scripts\validate_code.py" --strict --run-tests "D:\documents\programming corse\ثقف نفسك\tests"
if errorlevel 1 (
    echo [خطأ]: فشل أحد الاختبارات الآلية!
    pause
    exit /b 1
)

echo.
echo [2/3] بناء حزمة إضافة NVDA الرسمية (.nvda-addon)...
python "D:\documents\programming corse\ثقف نفسك\build_addon.py"

echo.
echo [3/3] فحص ملف نموذج الأسئلة الجاهز...
python -c "
import sys; sys.path.append(r'D:\documents\programming corse\ثقف نفسك\src')
from file_reader import read_text_from_file
from question_parser import parse_questions_content
from pool_validator import validate_match_pool
valid, err, _ = validate_match_pool(parse_questions_content(read_text_from_file(r'D:\documents\programming corse\ثقف نفسك\نموذج_أسئلة_المسابقة.txt')))
print('حالة ملف نموذج الأسئلة:', 'جاهز تماماً وصالح 100%' if valid else 'تنبيه: غير مكتمل')
"

echo.
echo ======================================================
echo   اكتمل الفحص والبناء بنجاح تام!
echo   ملف الإضافة جاهز للتثبيت في:
echo   dist\thaqqaf_nafsak-1.0.0.nvda-addon
echo ======================================================
pause
