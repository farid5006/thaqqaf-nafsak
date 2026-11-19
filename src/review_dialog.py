"""موديول واجهة مراجعة المباريات السابقة وعرض تقاريرها وحذفها لقارئ الشاشة."""
import os, webbrowser
try: import wx
except ImportError: wx = None

try:
    from . import bank_storage, match_reporter
    from .tournament_ops import delete_match
    from .delete_confirm_dialog import confirm_delete_with_reset
except ImportError:
    import bank_storage, match_reporter
    from tournament_ops import delete_match
    from delete_confirm_dialog import confirm_delete_with_reset

def show_matches_review(parent=None) -> None:
    if wx is None: return
    matches = bank_storage.load_matches_history()
    if not matches:
        dlg = wx.MessageDialog(parent, "لا توجد أي مباريات سابقة مسجلة في سجل المسابقة حتى الآن.", "مراجعة المباريات", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal(); dlg.Destroy(); return

    dlg = wx.Dialog(parent, title="ثقف نفسك - مراجعة المباريات والبطولات السابقة", size=(660, 440))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(wx.StaticText(dlg, label="قائمة المباريات السابقة (اختر مباراة لعرض تقريرها أو حذفها):"), 0, wx.ALL, 10)

    rev_matches = list(reversed(matches))
    choices = []
    for m in rev_matches:
        d = m.get("date", "")
        tour = m.get("tournament", "عام")
        ta, tb = m.get("team_a", "الفريق الأول"), m.get("team_b", "الفريق الثاني")
        sa, sb = m.get("score_a", 0), m.get("score_b", 0)
        win = m.get("winner", "تعادل")
        choices.append(f"[{tour}] [{d}] {ta} ({sa}) - ({sb}) {tb} | الفائز: {win}")

    lb = wx.ListBox(dlg, choices=choices, style=wx.LB_SINGLE)
    sizer.Add(lb, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_open = wx.Button(dlg, label="عرض تقرير المباراة")
    btn_del = wx.Button(dlg, label="حذف المباراة...")
    btn_close = wx.Button(dlg, wx.ID_CANCEL, label="إغلاق")
    btn_sizer.Add(btn_open, 1, wx.RIGHT, 6); btn_sizer.Add(btn_del, 1, wx.RIGHT, 6); btn_sizer.Add(btn_close, 0)
    sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

    def on_view(e):
        sel = lb.GetSelection()
        if sel != wx.NOT_FOUND:
            m_data = rev_matches[sel]
            html_text = match_reporter.generate_html_report(m_data)
            rep_path = os.path.join(bank_storage.get_data_dir(), f"report_{m_data.get('match_id', sel)}.html")
            with open(rep_path, "w", encoding="utf-8") as f: f.write(html_text)
            webbrowser.open(f"file:///{os.path.abspath(rep_path).replace(os.sep, '/')}")

    def on_del(e):
        sel = lb.GetSelection()
        if sel == wx.NOT_FOUND or sel >= len(rev_matches): return
        m = rev_matches[sel]
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

    btn_open.Bind(wx.EVT_BUTTON, on_view); lb.Bind(wx.EVT_LISTBOX_DCLICK, on_view)
    btn_del.Bind(wx.EVT_BUTTON, on_del)
    if choices: lb.SetSelection(0); lb.SetFocus()
    dlg.SetSizer(sizer); dlg.CenterOnParent(); dlg.ShowModal(); dlg.Destroy()
