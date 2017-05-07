# from test_baniser import DummyState, test_char_to_cat


# def string_to_banisher(s, cs_map=None, char_to_cat=None, param_map=None):
#     scope = DummyState(cs_map=cs_map,
#                        param_map=param_map, char_to_cat=char_to_cat)
#     state = GlobalState(global_font_state=None, initial_scope=scope,
#                         get_local_scope_func=None)
#     instrs = Instructioner.from_string(s, get_cat_code_func=state.get_cat_code)
#     return Banisher(instrs, state, instrs.lexer.reader)


# def test():
#     b = string_to_banisher()
#     with safe_chunk_grabber(banisher, command_parser) as command_grabber:
#         executor = Executor(command_grabber, state, banisher, reader)
#         executor.advance_to_end()
