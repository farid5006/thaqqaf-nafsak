"""نافذة استعراض مباريات بطولة محددة ونتائجها وتقاريرها وحذفها."""
import os, webbrowser
try: import wx
except ImportError: wx = None
try:
    from .bank_storage import get_data_dir, load_matches_history
    from .match_reporter import generate_html_report
    from .tournament_ops import get_matches_for_tournament, assign_match_to_tournament, delete_match
    from .delete_confirm_dialog import confirm_delete_with_reset
except ImportError:
    from bank_storage import get_data_dir, load_matches_history
    from match_reporter import generate_html_report
    from tournament_ops import get_matches_for_tournament, assign_match_to_tournament, delete_match
    from delete_confirm_dialog import confirm_delete_with_reset

def show_tournament_matches(parent, tour_name: str) -> None:
    if wx is None: return
    matches = list(reversed(get_matches_for_tournament(tour_name)))
    dlg = wx.Dialog(parent, title=f"مباريات {tour_name}", size=(680, 440))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(wx.StaticText(dlg, label=f"قائمة مباريات [{tour_name}] (اختر مباراة لعرض تقريرها أو حذفها):"), 0, wx.ALL, 10)
    
    choices = [f"[{m.get('date', '')}] {m.get('team_a')} ({m.get('score_a', 0)}) - ({m.get('score_b', 0)}) {m.get('team_b')} | الفائز: {m.get('winner', 'تعادل')}" for m in matches]
    lb = wx.ListBox(dlg, choices=choices, style=wx.LB_SINGLE)
    sizer.Add(lb, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_view = wx.Button(dlg, label="عرض تقرير المباراة")
    btn_del = wx.Button(dlg, label="حذف المباراة...")
    btn_assign = wx.Button(dlg, label="إضافة مباراة سابقة")
    btn_close = wx.Button(dlg, wx.ID_CANCEL, label="إغلاق")
    btn_sizer.Add(btn_view, 1, wx.RIGHT, 4); btn_sizer.Add(btn_del, 1, wx.RIGHT, 4); btn_sizer.Add(btn_assign, 1, wx.RIGHT, 4); btn_sizer.Add(btn_close, 0)
    sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

    def on_view(e):
        sel = lb.GetSelection()
        if sel != wx.NOT_FOUND:
            m_data = matches[sel]
            html = generate_html_report(m_data)
            p = os.path.join(get_data_dir(), f"report_{m_data.get('match_id', sel)}.html")
            with open(p, "w", encoding="utf-8") as f: f.write(html)
            webbrowser.open(f"file:///{os.path.abspath(p).replace(os.sep, '/')}")

    def on_del(e):
        sel = lb.GetSelection()
        if sel == wx.NOT_FOUND or sel >= len(matches): return
        m = matches[sel]
        mid = str(m.get("match_id", ""))
        desc = f"{m.get('team_a')} ضد {m.get('team_b')} [{m.get('date', '')}]"
        cf, reset = confirm_delete_with_reset(dlg, "تأكيد حذف مباراة", f"هل أنت متأكد من حذف مباراة '{desc}' نهائياً؟")
        if cf:
            delete_match(mid, reset_questions=reset)
            msg = "تم حذف المباراة بنجاح."
            if reset: msg += "\n(تم تصفير وتفريغ أسئلة المباراة لتصبح متاحة من جديد)."
            else: msg += "\n(تم الإبقاء على أسئلة المباراة مسجلة كمكررة لمنع تكرارها)."
            wx.MessageBox(msg, "تم", wx.OK | wx.ICON_INFORMATION, dlg)
            dlg.EndModal(wx.ID_OK)

    def on_assign(e):
        all_m = load_matches_history()
        other_m = [m for m in all_m if (m.get("tournament") or "").strip() != tour_name.strip()]
        if not other_m:
            wx.MessageBox("لا توجد مباريات في بطولات أخرى لنقلها.", "تنبيه", wx.OK | wx.ICON_INFORMATION, dlg); return
        pick_choices = [f"[{m.get('tournament', 'عام')}] [{m.get('date', '')}] {m.get('team_a')} ضد {m.get('team_b')}" for m in other_m]
        p_dlg = wx.SingleChoiceDialog(dlg, "اختر المباراة المراد نقلها وإضافتها لهذه البطولة:", "إضافة مباراة للبطولة", pick_choices)
        if p_dlg.ShowModal() == wx.ID_OK:
            s_idx = p_dlg.GetSelection()
            target_id = other_m[s_idx].get("match_id")
            if target_id and assign_match_to_tournament(target_id, tour_name):
                wx.MessageBox("تمت إضافة ونقل المباراة بنجاح إلى هذه البطولة.", "نجاح", wx.OK | wx.ICON_INFORMATION, dlg)
                dlg.EndModal(wx.ID_OK)
        p_dlg.Destroy()

    btn_view.Bind(wx.EVT_BUTTON, on_view); lb.Bind(wx.EVT_LISTBOX_DCLICK, on_view)
    btn_del.Bind(wx.EVT_BUTTON, on_del); btn_assign.Bind(wx.EVT_BUTTON, on_assign)
    if choices: lb.SetSelection(0); lb.SetFocus()
    dlg.SetSizer(sizer); dlg.CenterOnParent(); dlg.ShowModal(); dlg.Destroy()
