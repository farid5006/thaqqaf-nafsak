"""موديول بدء وتجهيز مباراة جديدة والتحقق من بنك الأسئلة."""
import threading, webbrowser

def launch_new_match(parent, rec, start_server_cb, gui_dialogs, file_reader, question_parser, pool_validator, bank_storage, match_state, tournament_manager):
    t1, t2, f, snd, rep = "الفريق الأول", "الفريق الثاني", bank_storage.get_last_file_path(), True, 0
    while True:
        p = gui_dialogs.prompt_new_match(parent, default_file=f, default_t1=t1, default_t2=t2, default_snd=snd, default_rep=rep)
        if not p or not p[2]: return None
        t1, t2, f, snd, rep = p
        try: q_data = question_parser.parse_questions_content(file_reader.read_text_from_file(f))
        except Exception as err:
            gui_dialogs.show_error_alert(f"تعذر قراءة ملف الأسئلة:\n{err}", parent=parent); continue
        bank = bank_storage.load_bank()
        used = set(bank.get("used", {}).keys())
        valid, errs, warns = pool_validator.validate_match_pool(q_data, used_ids=used, rep_pct=rep)
        r2_warns = [w for w in (warns or []) if "تكرار المجال" in w]
        if not valid:
            all_msgs = list(errs) + r2_warns
            can_bp = getattr(pool_validator, "can_bypass_r1_deficit", lambda *a, **k: False)(q_data, used, rep, errs)
            bp_fn = getattr(gui_dialogs, "prompt_bypass_alert", None)
            if can_bp and bp_fn:
                if not bp_fn("تنبيه بخصوص مجالات الأسئلة:\n- " + "\n- ".join(all_msgs), parent=parent): continue
            else:
                gui_dialogs.show_error_alert("نقص في بنك الأسئلة:\n- " + "\n- ".join(all_msgs), parent=parent); continue
        elif r2_warns:
            bp_fn = getattr(gui_dialogs, "prompt_bypass_alert", None)
            if bp_fn and not bp_fn("ملاحظة قبل بدء المباراة:\n- " + "\n- ".join(r2_warns), title="تنبيه مجالات الفقرة الثانية", parent=parent):
                continue
        bank["file_path"], bank["questions"] = f, q_data; bank_storage.save_bank(bank)
        st = match_state.MatchState(t1, t2, q_data=q_data, used_ids=used, tournament=tournament_manager.get_active_tournament(), rep_pct=rep, play_rules=bool(snd))
        s_dict = st.to_dict(); bank_storage.save_active_match(s_dict)
        url = start_server_cb(st, s_dict)
        if url: threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
        return st
