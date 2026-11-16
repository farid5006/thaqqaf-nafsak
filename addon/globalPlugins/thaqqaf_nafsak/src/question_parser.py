"""موديول تحليل واستخراج بنك الأسئلة من النصوص المهيكلة مع التوليد التلقائي للمعرفات."""
import re
from typing import Dict, List, Any

def _qid(q_text: str, field: str = "") -> str:
    try: from .bank_storage import compute_question_id
    except ImportError: from bank_storage import compute_question_id
    return compute_question_id(q_text, field)

def parse_questions_content(raw_text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    data = {"starter_speed": [], "round_1": {}, "round_2": {}, "round_3": []}
    current_round, current_field = "starter_speed", "تحديد البادئ"
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        is_q = any(line.startswith(p) for p in ("سؤال:", "س:", "س/", "*سؤال")) or re.match(r"^\d+[\.-]\s*", line)
        if not is_q:
            if any(kw in line for kw in ("البادئ", "تحديد الفريق", "التمهيدية", "سرعة البداية")):
                current_round, current_field = "starter_speed", "تحديد البادئ"
                idx += 1; continue
            if "الفقرة الأولى" in line or "الفقرة 1" in line:
                current_round, current_field = "round_1", "عام"
                idx += 1; continue
            if "الفقرة الثانية" in line or "الفقرة 2" in line or "اختر مجالك" in line:
                current_round, current_field = "round_2", "عام"
                idx += 1; continue
            if "الفقرة الثالثة" in line or "الفقرة 3" in line or "سرعة" in line:
                current_round, current_field = "round_3", "سرعة"
                idx += 1; continue
            if line.startswith(("[", "مجال:", "مجال ")):
                clean_field = re.sub(r"^\[?\s*(?:مجال\s*:\s*)?", "", line).rstrip("]\r\n\t ").strip()
                current_field = clean_field or "عام"
                idx += 1; continue
            has_q = line.endswith(("؟", "?"))
            nxt_ans = False
            if idx + 1 < len(lines):
                nxt = lines[idx + 1]
                nxt_ans = any(nxt.startswith(p) for p in ("الإجابة:", "إجابة:", "ج:", "ج/", "الجواب:", "جواب:", "*")) or bool(re.match(r"^[أ-ي0-9]+[\.\-\)]\s*", nxt))
            if not has_q and not nxt_ans:
                idx += 1; continue

        if current_round == "round_1":
            q_obj, idx = _parse_round_1_question(lines, idx, current_field)
            if q_obj: data["round_1"].setdefault(current_field, []).append(q_obj)
        else:
            q_obj, idx = _parse_direct_question(lines, idx, current_field)
            if current_round == "round_2": data["round_2"].setdefault(current_field, []).append(q_obj)
            elif current_round == "round_3": data["round_3"].append(q_obj)
            else:
                if len(q_obj["question"]) > 3: data["starter_speed"].append(q_obj)
    return data

def _parse_direct_question(lines: List[str], idx: int, field: str):
    q_text = re.sub(r"^(سؤال:|س:|س/|\d+[\.-]|\*)\s*", "", lines[idx]).strip()
    idx += 1
    answer = ""
    if idx < len(lines):
        next_line = lines[idx]
        if any(next_line.startswith(p) for p in ("الإجابة:", "إجابة:", "ج:", "ج/", "الجواب:", "جواب:", "*")):
            answer = re.sub(r"^(الإجابة:|إجابة:|الجواب:|جواب:|ج:|ج/|\*)\s*", "", next_line).strip()
            idx += 1
    return {"id": _qid(q_text, field), "question": q_text, "field": field, "correct_answer": answer}, idx

def _parse_round_1_question(lines: List[str], idx: int, field: str):
    q_text = re.sub(r"^(سؤال:|س:|س/|\d+[\.-]|\*)\s*", "", lines[idx]).strip()
    idx += 1
    choices, correct_idx = [], 0
    while idx < len(lines) and len(choices) < 4:
        c_line = lines[idx]
        if any(kw in c_line for kw in ("الفقرة", "مجال:")) or c_line.startswith("["): break
        is_correct = "*" in c_line
        clean_choice = re.sub(r"^([أ-ي0-9]+[\.\-\)]|\*)\s*", "", c_line).strip()
        if is_correct: correct_idx = len(choices)
        choices.append(clean_choice); idx += 1
    correct_ans = choices[correct_idx] if choices and correct_idx < len(choices) else ""
    return {"id": _qid(q_text, field), "question": q_text, "field": field, "choices": choices, "correct_index": correct_idx, "correct_answer": correct_ans}, idx
