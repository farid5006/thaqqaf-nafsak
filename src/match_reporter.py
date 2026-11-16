from datetime import datetime
from typing import Any, Dict, List, Tuple


def _escape_html(text: Any) -> str:
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _parse_match(
    match_data: Dict[str, Any]
) -> Tuple[str, str, int, int, str, str, List[Dict[str, Any]], Dict[str, Any]]:
    team_a = str(match_data.get("team_a", "الفريق الأول"))
    team_b = str(match_data.get("team_b", "الفريق الثاني"))
    scores = match_data.get("scores", {})
    score_a = int(match_data.get("score_a", scores.get(team_a, 0)))
    score_b = int(match_data.get("score_b", scores.get(team_b, 0)))
    if score_a > score_b:
        result = f"الفائز: {team_a}"
    elif score_b > score_a:
        result = f"الفائز: {team_b}"
    else:
        result = "النتيجة: تعادل بين الفريقين"
    date_str = str(match_data.get("date") or datetime.now().strftime("%Y-%m-%d %H:%M"))
    rounds: List[Dict[str, Any]] = list(match_data.get("rounds", []))[:3]
    totals = {
        "questions": match_data.get("total_questions", sum(int(r.get("questions", 0)) for r in rounds)),
        "rebounds": match_data.get("rebounds", sum(int(r.get("rebounds", 0)) for r in rounds)),
        "lifelines": match_data.get("lifelines", sum(int(r.get("lifelines", 0)) for r in rounds)),
    }
    return team_a, team_b, score_a, score_b, result, date_str, rounds, totals


def generate_text_report(match_data: Dict[str, Any]) -> str:
    team_a, team_b, score_a, score_b, result, date_str, rounds, totals = _parse_match(match_data)
    lines = [
        "تقرير مباراة مسابقة ثقف نفسك",
        f"التاريخ: {date_str}",
        "-" * 40,
        f"الفريقان: {team_a} مقابل {team_b}",
        f"النتيجة النهائية: {team_a} ({score_a}) - ({score_b}) {team_b}",
        result,
        "-" * 40,
        "ملخص الجولات الثلاث:",
    ]
    for idx in range(3):
        r = rounds[idx] if idx < len(rounds) else {}
        name = r.get("name", f"الجولة {idx + 1}")
        lines.append(
            f"- {name}: نقاط {team_a}={r.get('score_a', 0)}، نقاط {team_b}={r.get('score_b', 0)}، "
            f"الأسئلة={r.get('questions', 0)}، التحويلات المرتدة={r.get('rebounds', 0)}، "
            f"وسائل المساعدة={r.get('lifelines', 0)}"
        )
    lines.extend([
        "-" * 40,
        "الإحصاءات الإجمالية:",
        f"- إجمالي الأسئلة: {totals['questions']}",
        f"- التحويلات المرتدة: {totals['rebounds']}",
        f"- وسائل المساعدة المستخدمة: {totals['lifelines']}",
    ])
    return "\n".join(lines)


def generate_html_report(match_data: Dict[str, Any]) -> str:
    team_a, team_b, score_a, score_b, result, date_str, rounds, totals = _parse_match(match_data)
    rows_html = []
    for idx in range(3):
        r = rounds[idx] if idx < len(rounds) else {}
        name = _escape_html(r.get("name", f"الجولة {idx + 1}"))
        rows_html.append(
            f"<tr><th scope='row'>{name}</th><td>{int(r.get('score_a', 0))}</td>"
            f"<td>{int(r.get('score_b', 0))}</td><td>{int(r.get('questions', 0))}</td>"
            f"<td>{int(r.get('rebounds', 0))}</td><td>{int(r.get('lifelines', 0))}</td></tr>"
        )
    ta, tb = _escape_html(team_a), _escape_html(team_b)
    return "\n".join([
        "<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='UTF-8'>",
        "<title>تقرير مباراة مسابقة ثقف نفسك</title>",
        "<style>body{font-family:Arial,sans-serif;background:#fff;color:#000;line-height:1.6;margin:24px}"
        "table{width:100%;border-collapse:collapse;margin-top:12px}th,td{border:2px solid #000;padding:8px;text-align:center}"
        "thead th{background:#000;color:#fff}</style></head><body><main>",
        "<header><h1>تقرير مباراة مسابقة ثقف نفسك</h1>",
        f"<p>التاريخ: {_escape_html(date_str)}</p></header>",
        "<section aria-labelledby='res-h'>",
        f"<h2 id='res-h'>النتيجة النهائية</h2><p>{ta} ({score_a}) - ({score_b}) {tb}</p>",
        f"<p><strong>{_escape_html(result)}</strong></p></section>",
        "<section aria-labelledby='tbl-h'><h2 id='tbl-h'>ملخص الجولات الثلاث والإحصاءات</h2>",
        "<table><caption>تفاصيل الجولات الثلاث وإجمالي الإحصاءات</caption><thead><tr>"
        f"<th scope='col'>الجولة</th><th scope='col'>نقاط {ta}</th><th scope='col'>نقاط {tb}</th>"
        "<th scope='col'>الأسئلة</th><th scope='col'>التحويلات المرتدة</th><th scope='col'>وسائل المساعدة</th>"
        f"</tr></thead><tbody>{''.join(rows_html)}</tbody>"
        f"<tfoot><tr><th scope='row'>الإجمالي</th><td>{score_a}</td><td>{score_b}</td>"
        f"<td>{totals['questions']}</td><td>{totals['rebounds']}</td><td>{totals['lifelines']}</td></tr></tfoot>"
        "</table></section></main></body></html>",
    ])
