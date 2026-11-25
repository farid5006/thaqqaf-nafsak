# -*- coding: UTF-8 -*-
import os, sys, threading, webbrowser
try: import globalPluginHandler, gui, ui, wx
except ImportError: globalPluginHandler = gui = ui = wx = None
try: from scriptHandler import script
except ImportError: script = lambda *a, **k: lambda f: f

_H = os.path.dirname(os.path.abspath(__file__))
[sys.path.insert(0, _p) for _p in (_H, os.path.join(_H, "src"), os.path.abspath(os.path.join(_H, "..", "..", "..", "src"))) if os.path.isdir(_p) and _p not in sys.path]

try:
    from . import recording_bridge, gui_dialogs; from .src import file_reader, question_parser, pool_validator, match_state, server, action_dispatcher, bank_storage, review_dialog, tournament_manager, tournament_dialog, state_restorer, match_launcher
except ImportError:
    import recording_bridge, gui_dialogs, file_reader, question_parser, pool_validator, match_state, server, action_dispatcher, bank_storage, review_dialog, tournament_manager, tournament_dialog, state_restorer, match_launcher

_Base = globalPluginHandler.GlobalPlugin if globalPluginHandler else object

class GlobalPlugin(_Base):
    scriptCategory, __gestures = "ثقف نفسك", {"kb:NVDA+shift+q": "launch"}

    def __init__(self):
        super().__init__()
        self._server, self._menu_item, self._rec, self._cur_state, self._dialog_open = None, None, recording_bridge.RecordingBridge(), None, False
        if wx:
            try: wx.CallAfter(self._addMenu)
            except Exception: pass

    def _addMenu(self):
        try:
            icon = getattr(getattr(gui, "mainFrame", None), "sysTrayIcon", None)
            if icon:
                self._menu_item = icon.toolsMenu.Append(wx.ID_ANY, "ثقف نفسك - مسابقة المعلومات العامة...", "إدارة وتحكيم مسابقة ثقف نفسك")
                icon.Bind(wx.EVT_MENU, self.on_launch, self._menu_item)
        except Exception: pass

    @script(description="فتح نافذة مسابقة ثقف نفسك", gesture="kb:NVDA+shift+q")
    def script_launch(self, gesture):
        if self._server and getattr(self._cur_state, "phase", "") not in ("", "finished"):
            if ui and hasattr(ui, "message"): ui.message("العودة إلى شاشة عرض أسئلة المباراة")
            webbrowser_url = self._server.get_url()
            threading.Thread(target=webbrowser.open, args=(webbrowser_url,), daemon=True).start(); return
        if self._dialog_open:
            if ui and hasattr(ui, "message"): ui.message("نافذة مسابقة ثقف نفسك مفتوحة بالفعل")
            return
        if wx: wx.CallAfter(self.on_launch)
        else: self.on_launch()

    def on_launch(self, event=None):
        if self._dialog_open: return
        self._dialog_open = True
        try:
            parent = getattr(gui, "mainFrame", None)
            while True:
                cur, act_m = tournament_manager.get_active_tournament(), bank_storage.load_active_match()
                act = gui_dialogs.show_main_menu(parent, active_tour=cur, active_match=act_m)
                if act == "resume": self._resume_match(act_m); break
                elif act == "abort_match":
                    if wx and wx.MessageBox("هل تريد إنهاء وإلغاء المباراة الجارية نهائياً؟", "تأكيد", wx.YES_NO, parent) == wx.YES: self._stop_server(); bank_storage.clear_active_match(); continue
                elif act == "new":
                    self._stop_server()
                    st = match_launcher.launch_new_match(parent, self._rec, self._start_server_cb, gui_dialogs, file_reader, question_parser, pool_validator, bank_storage, match_state, tournament_manager)
                    if st: self._cur_state = st; break
                elif act == "tour_list": tournament_dialog.show_tournaments_dialog(parent); continue
                elif act == "new_tournament":
                    t = gui_dialogs.prompt_new_tournament(parent)
                    if t: tournament_manager.start_new_tournament(t); gui_dialogs.show_info_alert(f"تم بدء بطولة:\n'{t}'", parent=parent)
                    continue
                elif act == "review": review_dialog.show_matches_review(parent); break
                else: break
        finally: self._dialog_open = False

    def _start_server_cb(self, st, s_dict):
        self._cur_state = st
        self._server = server.MatchServer(state=s_dict, on_action=lambda a, b, s: action_dispatcher.dispatch_web_action(st, a, b, s))
        return self._server.start()

    def _resume_match(self, act_m):
        if not self._server:
            bank = bank_storage.load_bank()
            st = self._cur_state or state_restorer.restore_match_state(act_m, bank.get("questions") or {}, used_ids=set(bank.get("used", {}).keys()))
            url = self._start_server_cb(st, st.to_dict())
        else: url = self._server.get_url()
        if url: threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()

    def _stop_server(self):
        srv = self._server
        self._server, self._cur_state = None, None
        if srv:
            threading.Thread(target=srv.stop, daemon=True).start()

    def terminate(self):
        self._stop_server()
        try:
            icon = getattr(getattr(gui, "mainFrame", None), "sysTrayIcon", None)
            if icon and self._menu_item: icon.toolsMenu.Remove(self._menu_item)
        except Exception: pass
        if globalPluginHandler: super().terminate()
