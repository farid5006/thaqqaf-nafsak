"""موديول فحص كفاية بنك الأسئلة والتحقق الصارم وكشف التكرار عبر كافة الملفات."""
from typing import Dict, Any, List, Tuple, Optional, Set

def _qid(q: Dict[str, Any], field: str) -> str:
    try: from .bank_storage import compute_question_id
    except ImportError: from bank_storage import compute_question_id
    return q.get("id") or compute_question_id(q.get("question", ""), field)

def get_pool_questions(pool: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    res = [(q, "بدء") for q in pool.get("starter_speed", [])]
    for f, qs in pool.get("round_1", {}).items(): res.extend([(q, f) for q in qs])
    for f, qs in pool.get("round_2", {}).items(): res.extend([(q, f) for q in qs])
    res.extend([(q, "سرعة") for q in pool.get("round_3", [])])
    return res

def filter_available_pool(pool: Dict[str, Any], used_ids: Optional[Set[str]] = None) -> Dict[str, Any]:
    if not used_ids: return pool
    return {
        "starter_speed": [q for q in pool.get("starter_speed", []) if _qid(q, "بدء") not in used_ids],
        "round_1": {f: [q for q in qs if _qid(q, f) not in used_ids] for f, qs in pool.get("round_1", {}).items()},
        "round_2": {f: [q for q in qs if _qid(q, f) not in used_ids] for f, qs in pool.get("round_2", {}).items()},
        "round_3": [q for q in pool.get("round_3", []) if _qid(q, "سرعة") not in used_ids],
    }

def validate_match_pool(pool: Dict[str, Any], used_ids: Optional[Set[str]] = None, rep_pct: int = 0) -> Tuple[bool, List[str], List[str]]:
    errors, warnings = [], []
    all_qs = get_pool_questions(pool)
    repeated = [q for q, f in all_qs if used_ids and _qid(q, f) in used_ids]
    active = pool if rep_pct >= 100 else filter_available_pool(pool, used_ids)
    is_filtered = bool(used_ids) and rep_pct < 100

    # 1. فحص أسئلة السرعة لتحديد البادئ (عامة بدون مجالات: 5 أسئلة على الأقل لتأمين التخطي والاحتياطي)
    starters = active.get("starter_speed", [])
    if len(starters) < 5: errors.append(f"فقرة السرعة لتحديد البادئ (بدون مجالات): متاح {len(starters)} أسئلة غير مكررة فقط، والمطلوب 5 أسئلة على الأقل (لتأمين أسئلة التخطي).")
    for q in pool.get("starter_speed", []):
        if not q.get("correct_answer"): errors.append(f"فقرة تحديد البادئ: السؤال '{q.get('question', '')[:30]}' بدون إجابة.")

    # 2. فحص الفقرة الأولى (المطلوب 8 مجالات بكل منها 3 أسئلة على الأقل = 24)
    r1 = active.get("round_1", {})
    r1_ready = [f for f, qs in r1.items() if len(qs) >= 3]
    total_r1 = sum(len(qs) for qs in r1.values())
    if len(r1_ready) < 8 or total_r1 < 24:
        errors.append(f"الفقرة الأولى: متاح {total_r1} أسئلة غير مكررة ({len(r1_ready)} مجالات مكتملة)، والمطلوب 24 سؤالاً على الأقل (8 مجالات بكل منها 3 أسئلة).")
    for f, qs in pool.get("round_1", {}).items():
        for q in qs:
            if not q.get("choices") or len(q.get("choices", [])) != 4: errors.append(f"الفقرة الأولى ({f}): السؤال '{q.get('question', '')[:25]}' بدون 4 خيارات.")
            if not q.get("correct_answer"): errors.append(f"الفقرة الأولى ({f}): السؤال '{q.get('question', '')[:25]}' بدون إجابة صحيحة.")

    # 3. فحص الفقرة الثانية (اختر مجالك: 7 أسئلة على الأقل لكل مجال)
    r2 = active.get("round_2", {})
    r2_ready = [f for f, qs in r2.items() if len(qs) >= 7]
    if len(r2_ready) < 2: errors.append(f"الفقرة الثانية: مطلوب مجالان بكل منهما 7 أسئلة غير مكررة، المتاح {len(r2_ready)}.")
    for f, qs in r2.items():
        if len(qs) < 7: errors.append(f"الفقرة الثانية ({f}): الأسئلة غير المكررة {len(qs)} فقط، والمطلوب 7 أسئلة.")
    for f, qs in pool.get("round_2", {}).items():
        for q in qs:
            if not q.get("correct_answer"): errors.append(f"الفقرة الثانية ({f}): السؤال '{q.get('question', '')[:25]}' بدون إجابة.")

    # 4. فحص الفقرة الثالثة (أسئلة السرعة العامة بدون مجالات: 12 سؤالاً على الأقل)
    r3 = active.get("round_3", [])
    if len(r3) < 12: errors.append(f"الفقرة الثالثة: أسئلة السرعة (بدون مجالات): متاح {len(r3)} أسئلة غير مكررة فقط، والمطلوب 12 سؤالاً على الأقل (8 للمباراة + 4 احتياطي وتخطي وكسر تعادل).")
    for q in pool.get("round_3", []):
        if not q.get("correct_answer"): errors.append(f"الفقرة الثالثة: السؤال '{q.get('question', '')[:30]}' بدون إجابة.")

    # معالجة نسبة السماح بالتكرار (إذا كانت > 0 وأقل من 100)
    if is_filtered and errors and rep_pct > 0:
        max_allowed = int(55 * (rep_pct / 100.0))
        total_avail_in_file = len(pool.get("starter_speed", [])) + sum(len(qs) for qs in pool.get("round_1", {}).values()) + sum(len(qs) for qs in pool.get("round_2", {}).values()) + len(pool.get("round_3", []))
        total_unused = len(starters) + total_r1 + sum(len(qs) for qs in r2.values()) + len(r3)
        deficit = max(0, 55 - total_unused)
        if deficit <= max_allowed and total_avail_in_file >= 55:
            warnings.append(f"تمت الموافقة على سد نقص {deficit} أسئلة من الأسئلة السابقة وفق نسبة التكرار المحددة ({rep_pct}%).")
            errors.clear()
        else:
            errors.insert(0, f"نسبة التكرار المحددة ({rep_pct}%) تسمح بـ {max_allowed} أسئلة مكررة كحد أقصى، بينما النقص يبلغ {deficit} سؤالاً.")

    if is_filtered and errors and repeated:
        errors.insert(0, f"تنبيه: تم اكتشاف {len(repeated)} أسئلة في الملف مكررة ومطروحة في مباريات سابقة:")
    elif repeated and not errors:
        warnings.append(f"ملاحظة: يحتوي الملف على {len(repeated)} أسئلة مكررة من مباريات سابقة ولكن الرصيد الجديد كافٍ.")

    return len(errors) == 0, errors, warnings

def summarize_pool(pool: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "starters_count": len(pool.get("starter_speed", [])),
        "r1_fields": len(pool.get("round_1", {})),
        "r1_questions": sum(len(q) for q in pool.get("round_1", {}).values()),
        "r2_fields": len(pool.get("round_2", {})),
        "r2_questions": sum(len(q) for q in pool.get("round_2", {}).values()),
        "r3_questions": len(pool.get("round_3", [])),
    }
