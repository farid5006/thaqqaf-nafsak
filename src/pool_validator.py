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
    res.extend([(q, "سرعة") for q in pool.get("round_3", [])]); return res

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

    starters = active.get("starter_speed", [])
    if len(starters) < 5: errors.append(f"فقرة السرعة لتحديد البادئ (بدون مجالات): متاح {len(starters)} أسئلة غير مكررة فقط، والمطلوب 5 أسئلة على الأقل (لتأمين أسئلة التخطي).")
    for q in pool.get("starter_speed", []):
        if not q.get("correct_answer"): errors.append(f"فقرة تحديد البادئ: السؤال '{q.get('question', '')[:30]}' بدون إجابة.")

    r1 = active.get("round_1", {})
    r1_ready = [f for f, qs in r1.items() if len(qs) >= 3]
    total_r1 = sum(len(qs) for qs in r1.values())
    parts = []
    if len(r1) < 12: parts.append(f"الملف به {len(r1)} مجالات فقط من أصل 12 (المتاح: {'، '.join(r1.keys())}) وينقصه {12 - len(r1)} مجالات جديدة")
    def_f = [f"[{f}] (متاح {len(qs)} والمطلوب 3)" for f, qs in r1.items() if len(qs) < 3]
    if def_f: parts.append(f"نقص رصيد الأسئلة والاحتياطي في: {'، '.join(def_f)}")
    detail = f" - {'. '.join(parts)}" if parts else ""
    if total_r1 < 24: errors.append(f"الفقرة الأولى: متاح {total_r1} أسئلة غير مكررة فقط، والمطلوب 24 سؤالاً على الأقل للمباراة (12 سؤالاً لكل فريق).{detail}")
    elif len(r1_ready) < 12: errors.append(f"الفقرة الأولى: متاح {total_r1} أسئلة غير مكررة ({len(r1_ready)} مجالات مكتملة)، والمطلوب 36 سؤالاً (12 مجالاً بكل منها 3 أسئلة: 2 للمباراة + 1 احتياطي).{detail}")
    for f, qs in pool.get("round_1", {}).items():
        for q in qs:
            if not q.get("choices") or len(q.get("choices", [])) != 4: errors.append(f"الفقرة الأولى ({f}): السؤال '{q.get('question', '')[:25]}' بدون 4 خيارات.")
            if not q.get("correct_answer"): errors.append(f"الفقرة الأولى ({f}): السؤال '{q.get('question', '')[:25]}' بدون إجابة صحيحة.")

    r2 = active.get("round_2", {})
    r2_ready = [f for f, qs in r2.items() if len(qs) >= 7]
    def_r2 = [f"[{f}] (متاح {len(qs)} والمطلوب 7)" for f, qs in r2.items() if len(qs) < 7]
    if len(r2_ready) < 2: errors.append(f"الفقرة الثانية (اختر مجالك): مطلوب مجالان مكتملان (بكل منهما 7 أسئلة غير مكررة)، المتاح {len(r2_ready)} مجالات فقط." + (f" - النقص في: {', '.join(def_r2)}" if def_r2 else ""))
    elif def_r2: errors.append(f"الفقرة الثانية (اختر مجالك): تنبيه بنقص في بعض المجالات: {', '.join(def_r2)}.")
    for f, qs in pool.get("round_2", {}).items():
        for q in qs:
            if not q.get("correct_answer"): errors.append(f"الفقرة الثانية ({f}): السؤال '{q.get('question', '')[:25]}' بدون إجابة.")

    r3 = active.get("round_3", [])
    if len(r3) < 16: errors.append(f"الفقرة الثالثة: أسئلة السرعة (بدون مجالات): متاح {len(r3)} أسئلة غير مكررة فقط، والمطلوب 16 سؤالاً على الأقل (12 للمباراة + 4 احتياطي وتخطي وكسر تعادل).")
    for q in pool.get("round_3", []):
        if not q.get("correct_answer"): errors.append(f"الفقرة الثالثة: السؤال '{q.get('question', '')[:30]}' بدون إجابة.")

    if is_filtered and errors and rep_pct > 0:
        max_allowed = int(71 * (rep_pct / 100.0))
        total_avail = len(pool.get("starter_speed", [])) + sum(len(qs) for qs in pool.get("round_1", {}).values()) + sum(len(qs) for qs in pool.get("round_2", {}).values()) + len(pool.get("round_3", []))
        total_unused = len(starters) + total_r1 + sum(len(qs) for qs in r2.values()) + len(r3)
        deficit = max(0, 71 - total_unused)
        if deficit <= max_allowed and total_avail >= 71:
            warnings.append(f"تمت الموافقة على سد نقص {deficit} أسئلة من الأسئلة السابقة وفق نسبة التكرار المحددة ({rep_pct}%).")
            errors.clear()
        else: errors.insert(0, f"نسبة التكرار المحددة ({rep_pct}%) تسمح بـ {max_allowed} أسئلة مكررة كحد أقصى، بينما النقص يبلغ {deficit} سؤالاً.")

    if is_filtered and errors and repeated: errors.insert(0, f"تنبيه: تم اكتشاف {len(repeated)} أسئلة في الملف مكررة ومطروحة في مباريات سابقة:")
    elif repeated and not errors: warnings.append(f"ملاحظة: يحتوي الملف على {len(repeated)} أسئلة مكررة من مباريات سابقة ولكن الرصيد الجديد كافٍ.")
    return len(errors) == 0, errors, warnings

def can_bypass_r1_deficit(pool: Dict[str, Any], used_ids: Optional[Set[str]] = None, rep_pct: int = 0, errors: Optional[List[str]] = None) -> bool:
    act = pool if rep_pct >= 100 else filter_available_pool(pool, used_ids)
    if sum(len(qs) for qs in act.get("round_1", {}).values()) < 24: return False
    if len(act.get("starter_speed", [])) < 5 or len(act.get("round_3", [])) < 12: return False
    if len([f for f, qs in act.get("round_2", {}).items() if len(qs) >= 7]) < 2: return False
    for qs in pool.get("round_1", {}).values():
        if any(not q.get("correct_answer") or len(q.get("choices", [])) != 4 for q in qs): return False
    return True

def summarize_pool(pool: Dict[str, Any]) -> Dict[str, Any]:
    return {"starters_count": len(pool.get("starter_speed", [])), "r1_fields": len(pool.get("round_1", {})), "r1_questions": sum(len(q) for q in pool.get("round_1", {}).values()), "r2_fields": len(pool.get("round_2", {})), "r2_questions": sum(len(q) for q in pool.get("round_2", {}).values()), "r3_questions": len(pool.get("round_3", []))}
