"""موديول بدء وتجهيز مباراة جديدة والتحقق من بنك الأسئلة."""
import webbrowser

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
        valid, errs, _ = pool_validator.validate_match_pool(q_data, used_ids=used, rep_pct=rep)
        if not valid:
            can_bp = getattr(pool_validator, "can_bypass_r1_deficit", lambda *a, **k: False)(q_data, used, rep, errs)
            bp_fn = getattr(gui_dialogs, "prompt_bypass_alert", None)
            if can_bp and bp_fn:
                if not bp_fn("تنبيه بخصوص مجالات الأسئلة:\n- " + "\n- ".join(errs), parent=parent): continue
            else:
                gui_dialogs.show_error_alert("نقص في بنك الأسئلة:\n- " + "\n- ".join(errs), parent=parent); continue
        bank["file_path"], bank["questions"] = f, q_data; bank_storage.save_bank(bank)
        st = match_state.MatchState(t1, t2, q_data=q_data, used_ids=used, tournament=tournament_manager.get_active_tournament(), rep_pct=rep)
        s_dict = st.to_dict(); bank_storage.save_active_match(s_dict)
        url = start_server_cb(st, s_dict)
        if url: webbrowser.open(url)
        if snd and rec: rec.play_rules_intro()
        return st
