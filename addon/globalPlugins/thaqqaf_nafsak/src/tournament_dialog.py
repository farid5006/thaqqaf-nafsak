"""نافذة قائمة البطولات وإدارتها وعرض سياق خياراتها لمستخدمي قارئ الشاشة."""
try: import wx
except ImportError: wx = None
try:
    from .tournament_manager import list_tournaments, get_active_tournament, set_active_tournament
    from .tournament_ops import delete_tournament
    from .tournament_matches_dialog import show_tournament_matches
    from .delete_confirm_dialog import confirm_delete_with_reset
except ImportError:
    from tournament_manager import list_tournaments, get_active_tournament, set_active_tournament
    from tournament_ops import delete_tournament
    from tournament_matches_dialog import show_tournament_matches
    from delete_confirm_dialog import confirm_delete_with_reset

def show_tournaments_dialog(parent=None) -> None:
    if wx is None: return
    tours = list_tournaments()
    active_t = get_active_tournament()
    dlg = wx.Dialog(parent, title="ثقف نفسك - قائمة البطولات", size=(580, 420))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(wx.StaticText(dlg, label="قائمة البطولات (اضغط زر التطبيقات أو كليك يمين لفتح خيارات البطولة):"), 0, wx.ALL, 10)

    choices = [f"{t} (البطولة النشطة حالياً)" if t == active_t else t for t in tours]
    lb = wx.ListBox(dlg, choices=choices, style=wx.LB_SINGLE)
    sizer.Add(lb, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_matches = wx.Button(dlg, label="عرض مباريات البطولة")
    btn_menu = wx.Button(dlg, label="خيارات البطولة (قائمة السياق)...")
    btn_close = wx.Button(dlg, wx.ID_CANCEL, label="إغلاق")
    btn_sizer.Add(btn_matches, 1, wx.RIGHT, 5); btn_sizer.Add(btn_menu, 1, wx.RIGHT, 5); btn_sizer.Add(btn_close, 0)
    sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

    def get_selected():
        sel = lb.GetSelection()
        return tours[sel] if sel != wx.NOT_FOUND and sel < len(tours) else None

    def on_view(e):
        t = get_selected()
        if t: show_tournament_matches(dlg, t)

    def on_set_active(t):
        set_active_tournament(t)
        wx.MessageBox(f"تم تعيين '{t}' كبطولة نشطة حالياً بنجاح.", "تم", wx.OK | wx.ICON_INFORMATION, dlg)
        dlg.EndModal(wx.ID_OK)

    def on_delete(t):
        if len(tours) <= 1:
            wx.MessageBox("لا يمكن حذف البطولة الوحيدة المتبقية.", "تنبيه", wx.OK | wx.ICON_WARNING, dlg); return
        cf, reset = confirm_delete_with_reset(dlg, "تأكيد حذف البطولة", f"هل أنت متأكد من حذف بطولة '{t}' نهائياً؟\nسيتم حذف سجل كافة مبارياتها من البطولة.")
        if cf:
            delete_tournament(t, reset_questions=reset)
            msg = f"تم حذف بطولة '{t}' بنجاح."
            if reset: msg += "\n(تم تصفير الأسئلة المستخدمة في البطولة وتفريغها لتصبح متاحة من جديد)."
            else: msg += "\n(تم الإبقاء على الأسئلة مسجلة كمكررة لمنع تكرارها في المباريات القادمة)."
            wx.MessageBox(msg, "تم", wx.OK | wx.ICON_INFORMATION, dlg)
            dlg.EndModal(wx.ID_OK)

    def show_context_menu(e=None):
        t = get_selected()
        if not t: return
        menu = wx.Menu()
        m_view = menu.Append(wx.ID_ANY, f"عرض مباريات [{t}]")
        m_set = menu.Append(wx.ID_ANY, f"تعيين [{t}] كبطولة نشطة حالياً")
        m_del = menu.Append(wx.ID_ANY, f"حذف بطولة [{t}]")
        dlg.Bind(wx.EVT_MENU, lambda evt: show_tournament_matches(dlg, t), m_view)
        dlg.Bind(wx.EVT_MENU, lambda evt: on_set_active(t), m_set)
        dlg.Bind(wx.EVT_MENU, lambda evt: on_delete(t), m_del)
        dlg.PopupMenu(menu); menu.Destroy()

    btn_matches.Bind(wx.EVT_BUTTON, on_view); lb.Bind(wx.EVT_LISTBOX_DCLICK, on_view)
    btn_menu.Bind(wx.EVT_BUTTON, lambda e: show_context_menu())
    lb.Bind(wx.EVT_CONTEXT_MENU, show_context_menu)
    if choices: lb.SetSelection(0); lb.SetFocus()
    dlg.SetSizer(sizer); dlg.CenterOnParent(); dlg.ShowModal(); dlg.Destroy()
