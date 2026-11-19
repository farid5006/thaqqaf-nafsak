"""موديول مربع حوار تأكيد الحذف مع خيار تصفير الأسئلة اختارياً."""
try:
    import wx
except ImportError:
    wx = None

def confirm_delete_with_reset(parent, title: str, message: str) -> tuple[bool, bool]:
    if wx is None:
        return False, False
    dlg = wx.Dialog(parent, title=title, size=(460, 220))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(wx.StaticText(dlg, label=message), 0, wx.ALL, 12)
    chk = wx.CheckBox(dlg, label="تفريغ وتصفير الأسئلة المستخدمة (إتاحتها من جديد كأنها لم تُطرح)")
    chk.SetValue(False)
    sizer.Add(chk, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_yes = wx.Button(dlg, wx.ID_YES, label="نعم، احذف")
    btn_no = wx.Button(dlg, wx.ID_NO, label="إلغاء")
    btn_sizer.Add(btn_yes, 1, wx.RIGHT, 6)
    btn_sizer.Add(btn_no, 0)
    sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

    btn_yes.Bind(wx.EVT_BUTTON, lambda e: dlg.EndModal(wx.ID_YES))
    btn_no.Bind(wx.EVT_BUTTON, lambda e: dlg.EndModal(wx.ID_NO))
    btn_no.SetFocus()

    dlg.SetSizerAndFit(sizer)
    dlg.CenterOnParent()
    dlg.Raise()
    dlg.RequestUserAttention()

    confirmed = (dlg.ShowModal() == wx.ID_YES)
    reset_q = chk.GetValue() if confirmed else False
    dlg.Destroy()
    return confirmed, reset_q
