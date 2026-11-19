from __future__ import annotations
try: import wx
except ImportError: wx = None

def show_main_menu(parent=None, active_tour: str = "", active_match: dict | None = None) -> str:
    if wx is None: return "cancel"
    dlg = wx.Dialog(parent, title="ثقف نفسك - القائمة الرئيسية")
    sizer = wx.BoxSizer(wx.VERTICAL)
    if active_tour: sizer.Add(wx.StaticText(dlg, label=f"البطولة الحالية: {active_tour}"), 0, wx.ALL, 8)
    sizer.Add(wx.StaticText(dlg, label="اختر الإجراء المطلوب:"), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
    choice, btns = ["cancel"], []

    def on_pick(res: str):
        choice[0] = res; dlg.EndModal(wx.ID_OK)

    if active_match:
        t1, t2 = active_match.get("team_a", "الفريق الأول"), active_match.get("team_b", "الفريق الثاني")
        btn_res = wx.Button(dlg, label=f"استئناف المباراة الجارية ({t1} ضد {t2})")
        btn_res.Bind(wx.EVT_BUTTON, lambda e: on_pick("resume")); btns.append(btn_res)
        btn_abort = wx.Button(dlg, label="إنهاء وإلغاء المباراة الجارية")
        btn_abort.Bind(wx.EVT_BUTTON, lambda e: on_pick("abort_match")); btns.append(btn_abort)
    else:
        btn_new = wx.Button(dlg, label="بدء مباراة جديدة")
        btn_new.Bind(wx.EVT_BUTTON, lambda e: on_pick("new")); btns.append(btn_new)

    btn_tl = wx.Button(dlg, label="قائمة البطولات")
    btn_tn = wx.Button(dlg, label="بدء بطولة جديدة")
    btn_rv = wx.Button(dlg, label="مراجعة مباراة سابقة")
    btn_ca = wx.Button(dlg, wx.ID_CANCEL, label="إلغاء")

    btn_tl.Bind(wx.EVT_BUTTON, lambda e: on_pick("tour_list"))
    btn_tn.Bind(wx.EVT_BUTTON, lambda e: on_pick("new_tournament"))
    btn_rv.Bind(wx.EVT_BUTTON, lambda e: on_pick("review"))
    btns.extend([btn_tl, btn_tn, btn_rv, btn_ca])

    for btn in btns: sizer.Add(btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
    dlg.SetSizerAndFit(sizer); dlg.CenterOnParent(); dlg.Raise(); dlg.RequestUserAttention(); btns[0].SetFocus(); dlg.ShowModal(); dlg.Destroy()
    return choice[0]

def prompt_new_match(parent=None, default_file: str = "", default_t1: str = "الفريق الأول", default_t2: str = "الفريق الثاني", default_snd: bool = True, default_rep: int = 0) -> tuple[str, str, str, bool, int]:
    if wx is None: return ("", "", "", False, 0)
    dlg = wx.Dialog(parent, title="إعداد مباراة جديدة")
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(wx.StaticText(dlg, label="اسم الفريق الأول:"), 0, wx.LEFT | wx.TOP, 8)
    t1 = wx.TextCtrl(dlg, value=default_t1 or "الفريق الأول"); sizer.Add(t1, 0, wx.EXPAND | wx.ALL, 5)
    sizer.Add(wx.StaticText(dlg, label="اسم الفريق الثاني:"), 0, wx.LEFT | wx.TOP, 6)
    t2 = wx.TextCtrl(dlg, value=default_t2 or "الفريق الثاني"); sizer.Add(t2, 0, wx.EXPAND | wx.ALL, 5)
    sizer.Add(wx.StaticText(dlg, label="ملف الأسئلة:"), 0, wx.LEFT | wx.TOP, 6)
    row, f_txt, f_btn = wx.BoxSizer(wx.HORIZONTAL), wx.TextCtrl(dlg, value=default_file), wx.Button(dlg, label="استعراض...")
    row.Add(f_txt, 1, wx.EXPAND | wx.RIGHT, 5); row.Add(f_btn, 0); sizer.Add(row, 0, wx.EXPAND | wx.ALL, 5)
    sizer.Add(wx.StaticText(dlg, label="نسبة السماح بتكرار الأسئلة السابقة (من 0% إلى 100%):"), 0, wx.LEFT | wx.TOP, 6)
    rep_opts = [f"{i}% (حظر التكرار تماماً - افتراضي)" if i == 0 else (f"{i}% (السماح بكافة الأسئلة)" if i == 100 else f"{i}%") for i in range(101)]
    choice_rep = wx.Choice(dlg, choices=rep_opts); choice_rep.SetSelection(min(max(0, default_rep), 100))
    sizer.Add(choice_rep, 0, wx.EXPAND | wx.ALL, 5)
    chk_snd = wx.CheckBox(dlg, label="تشغيل القواعد الصوتية"); chk_snd.SetValue(default_snd); sizer.Add(chk_snd, 0, wx.ALL, 5)
    btns = dlg.CreateButtonSizer(wx.OK | wx.CANCEL)
    if btns: sizer.Add(btns, 0, wx.EXPAND | wx.ALL, 6)

    def on_browse(e):
        fd = wx.FileDialog(dlg, "اختر ملف الأسئلة", wildcard="ملفات الأسئلة (*.docx;*.txt;*.html;*.md)|*.docx;*.txt;*.html;*.md|كل الملفات (*.*)|*.*")
        if fd.ShowModal() == wx.ID_OK: f_txt.SetValue(fd.GetPath())
        fd.Destroy()

    f_btn.Bind(wx.EVT_BUTTON, on_browse); dlg.SetSizerAndFit(sizer); dlg.CenterOnParent(); dlg.Raise(); dlg.RequestUserAttention(); t1.SetFocus()
    res = ("", "", "", False, 0)
    if dlg.ShowModal() == wx.ID_OK:
        res = (t1.GetValue().strip(), t2.GetValue().strip(), f_txt.GetValue().strip(), chk_snd.GetValue(), choice_rep.GetSelection())
    dlg.Destroy(); return res

def prompt_new_tournament(parent=None) -> str:
    if wx is None: return ""
    dlg = wx.TextEntryDialog(parent, "أدخل اسم البطولة الجديدة (مثال: بطولة رمضان، دوري المعرفة...):", "بدء بطولة جديدة")
    res = dlg.GetValue().strip() if dlg.ShowModal() == wx.ID_OK else ""
    dlg.Destroy(); return res

def show_error_alert(message: str, title: str = "ثقف نفسك", parent=None) -> None:
    if wx: dlg = wx.MessageDialog(parent, message, title, wx.OK | wx.ICON_ERROR); dlg.ShowModal(); dlg.Destroy()

def show_info_alert(message: str, title: str = "ثقف نفسك", parent=None) -> None:
    if wx: dlg = wx.MessageDialog(parent, message, title, wx.OK | wx.ICON_INFORMATION); dlg.ShowModal(); dlg.Destroy()

def prompt_bypass_alert(message: str, title: str = "تنبيه نقص مجالات الأسئلة", parent=None) -> bool:
    if wx is None: return False
    body = message + "\n\nهل تريد تخطي هذا النقص وبدء المباراة بالاعتماد على الفائض في المجالات الأخرى؟"
    dlg = wx.MessageDialog(parent, body, title, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
    try: dlg.SetYesNoLabels("تخطي وبدء المباراة", "إلغاء")
    except Exception: pass
    res = (dlg.ShowModal() == wx.ID_YES)
    dlg.Destroy(); return res
