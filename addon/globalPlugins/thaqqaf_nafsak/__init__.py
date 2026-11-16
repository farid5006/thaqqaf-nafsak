# -*- coding: UTF-8 -*-
import os, sys, webbrowser
try:
    import globalPluginHandler, gui, wx
except ImportError:
    globalPluginHandler = gui = wx = None

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "src"), os.path.abspath(os.path.join(_HERE, "..", "..", "..", "src"))):
    if os.path.isdir(_p) and _p not in sys.path: sys.path.insert(0, _p)

try:
    from . import recording_bridge, gui_dialogs
    from .src import file_reader, question_parser, pool_validator, match_state, server, action_dispatcher, bank_storage, review_dialog, tournament_manager
except ImportError:
    import recording_bridge, gui_dialogs
    import file_reader, question_parser, pool_validator, match_state, server, action_dispatcher, bank_storage, review_dialog, tournament_manager

_BasePlugin = globalPluginHandler.GlobalPlugin if globalPluginHandler else object

class GlobalPlugin(_BasePlugin):
    def __init__(self):
        super().__init__()
        self._server, self._menu_item, self._rec_bridge = None, None, recording_bridge.RecordingBridge()
        if wx:
            try: wx.CallAfter(self._addMenuItem)
            except Exception: pass

    def _addMenuItem(self):
        try:
            if hasattr(gui, "mainFrame") and gui.mainFrame and getattr(gui.mainFrame, "sysTrayIcon", None):
                self._menu_item = gui.mainFrame.sysTrayIcon.toolsMenu.Append(wx.ID_ANY, "ثقف نفسك - مسابقة المعلومات العامة...", "إدارة وتحكيم مسابقة ثقف نفسك")
                gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.on_launch, self._menu_item)
        except Exception: pass

    def on_launch(self, event=None):
        parent = getattr(gui, "mainFrame", None)
        while True:
            cur_tour = tournament_manager.get_active_tournament()
            action = gui_dialogs.show_main_menu(parent, active_tour=cur_tour)
            if action == "new":
                self._start_new_match(parent); break
            elif action == "new_tournament":
                t_name = gui_dialogs.prompt_new_tournament(parent)
                if t_name:
                    tournament_manager.start_new_tournament(t_name)
                    gui_dialogs.show_info_alert(f"تم بدء بطولة جديدة بنجاح:\n'{t_name}'\nجميع المباريات القادمة ستسجل ضمن هذه البطولة.", parent=parent)
                continue
            elif action == "review":
                review_dialog.show_matches_review(parent); break
            else: break

    def _start_new_match(self, parent):
        t1, t2, f_path, snd, rep = "الفريق الأول", "الفريق الثاني", bank_storage.get_last_file_path(), True, 0
        while True:
            params = gui_dialogs.prompt_new_match(parent, default_file=f_path, default_t1=t1, default_t2=t2, default_snd=snd, default_rep=rep)
            if not params or not params[2]: return
            t1, t2, f_path, snd, rep = params
            try:
                raw_content = file_reader.read_text_from_file(f_path)
                q_data = question_parser.parse_questions_content(raw_content)
            except Exception as err:
                gui_dialogs.show_error_alert(f"تعذر قراءة ملف الأسئلة:\n{err}", parent=parent); continue

            bank = bank_storage.load_bank()
            used_ids = set(bank.get("used", {}).keys())

            is_valid, errors, _ = pool_validator.validate_match_pool(q_data, used_ids=used_ids, rep_pct=rep)
            if not is_valid:
                gui_dialogs.show_error_alert("نقص في بنك الأسئلة:\n- " + "\n- ".join(errors), parent=parent); continue

            self._stop_server()
            bank["file_path"], bank["questions"] = f_path, q_data
            bank_storage.save_bank(bank)

            tour_name = tournament_manager.get_active_tournament()
            state = match_state.MatchState(t1, t2, q_data=q_data, used_ids=used_ids, tournament=tour_name, rep_pct=rep)
            self._server = server.MatchServer(state=state.to_dict(), on_action=lambda a, b, s: action_dispatcher.dispatch_web_action(state, a, b, s))
            url = self._server.start()
            if url: webbrowser.open(url)
            if snd: self._rec_bridge.play_rules_intro()
            break

    def _stop_server(self):
        if self._server:
            try: self._server.stop()
            except Exception: pass
            self._server = None

    def terminate(self):
        self._stop_server()
        try:
            if hasattr(self, "_menu_item") and self._menu_item and hasattr(gui, "mainFrame"):
                gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self._menu_item)
        except Exception: pass
        if globalPluginHandler: super().terminate()
