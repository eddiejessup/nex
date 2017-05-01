import operator

from . import evaluator as evaler


def execute_if_num(if_token, state):
    v = if_token.value
    left_number = evaler.evaluate_number(state, v['left_number'])
    right_number = evaler.evaluate_number(state, v['right_number'])
    operator_map = {
        '<': operator.lt,
        '=': operator.eq,
        '>': operator.gt,
    }
    op = operator_map[v['relation']]
    outcome = op(left_number, right_number)
    return outcome


def execute_if_case(if_token, state):
    v = if_token.value
    return evaler.evaluate_number(state, v['number'])


def execute_condition(condition_token, state):
    if_token = condition_token.value
    exec_func_map = {
        'if_num': execute_if_num,
        'if_case': execute_if_case,
        'if_true': lambda *args: True,
        'if_false': lambda *args: False,
    }
    exec_func = exec_func_map[if_token.type]
    outcome = exec_func(if_token, state)
    return outcome
