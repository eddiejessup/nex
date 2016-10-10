from datetime import datetime

from .common import TerminalToken


integer_parameters = {
    'pretolerance': 0,
    'tolerance': 10000,
    'hbadness': 0,
    'vbadness': 0,
    'linepenalty': 0,
    'hyphenpenalty': 0,
    'exhyphenpenalty': 0,
    'binoppenalty': 0,
    'relpenalty': 0,
    'clubpenalty': 0,
    'widowpenalty': 0,
    'displaywidowpenalty': 0,
    'brokenpenalty': 0,
    'predisplaypenalty': 0,
    'postdisplaypenalty': 0,
    'interlinepenalty': 0,
    'floatingpenalty': 0,
    'outputpenalty': 0,
    'doublehyphendemerits': 0,
    'finalhyphendemerits': 0,
    'adjdemerits': 0,
    'looseness': 0,
    'pausing': 0,
    'holdinginserts': 0,
    'tracingonline': 0,
    'tracingmacros': 0,
    'tracingstats': 0,
    'tracingparagraphs': 0,
    'tracingpages': 0,
    'tracingoutput': 0,
    'tracinglostchars': 0,
    'tracingcommands': 0,
    'tracingrestores': 0,
    'language': 0,
    'uchyph': 0,
    'lefthyphenmin': 0,
    'righthyphenmin': 0,
    'globaldefs': 0,
    'maxdeadcycles': 25,
    'hangafter': 1,
    'fam': 0,
    'mag': 1000,
    'escapechar': ord('\\'),
    'defaulthyphenchar': 0,
    'defaultskewchar': 0,
    'endlinechar': ord('\r'),
    'newlinechar': 0,
    'delimiterfactor': 0,
    # These time ones will be set in get_initial_parameters.
    'time': None,
    'day': None,
    'month': None,
    'year': None,
    'showboxbreadth': 0,
    'showboxdepth': 0,
    'errorcontextlines': 0,
}

dimen_parameters = {
    'hfuzz': 0,
    'vfuzz': 0,
    'overfullrule': 0,
    'hsize': 0,
    'vsize': 0,
    'maxdepth': 0,
    'splitmaxdepth': 0,
    'boxmaxdepth': 0,
    'lineskiplimit': 0,
    'delimitershortfall': 0,
    'nulldelimiterspace': 0,
    'scriptspace': 0,
    'mathsurround': 0,
    'predisplaysize': 0,
    'displaywidth': 0,
    'displayindent': 0,
    'parindent': 0,
    'hangindent': 0,
    'hoffset': 0,
    'voffset': 0,
}

glue_keys = ('dimen', 'stretch', 'shrink')
get_zero_glue = lambda: {k: 0 for k in glue_keys}
glue_parameter_names = (
    'baselineskip',
    'lineskip',
    'parskip',
    'abovedisplayskip',
    'abovedisplayshortskip',
    'belowdisplayskip',
    'belowdisplayshortskip',
    'leftskip',
    'rightskip',
    'topskip',
    'splittopskip',
    'tabskip',
    'spaceskip',
    'xspaceskip',
    'parfillskip',
)
glue_parameters = {p: get_zero_glue() for p in glue_parameter_names}

mu_glue_parameter_names = (
    'thinmuskip',
    'medmuskip',
    'thickmuskip',
)
mu_glue_parameters = {p: get_zero_glue() for p in mu_glue_parameter_names}

get_empty_token_list = lambda: TerminalToken(type_='BALANCED_TEXT_AND_RIGHT_BRACE',
                                             value=[])
token_parameter_names = (
    'output',
    'everypar',
    'everymath',
    'everydisplay',
    'everyhbox',
    'everyvbox',
    'everyjob',
    'everycr',
    'errhelp',
)
token_parameters = {p: get_empty_token_list() for p in token_parameter_names}

default_parameters = {
    'INTEGER_PARAMETER': integer_parameters,
    'DIMEN_PARAMETER': dimen_parameters,
    'GLUE_PARAMETER': glue_parameters,
    'MU_GLUE_PARAMETER': mu_glue_parameters,
    'TOKEN_PARAMETER': token_parameters,
}

parameter_types = default_parameters.keys()


def is_parameter_type(type_):
    return type_ in parameter_types


special_integer_names = (
    'spacefactor',
    'prevgraf',
    'deadcycles',
    'insertpenalties',
)

special_dimen_names = (
    'prevdepth',
    'pagegoal',
    'pagetotal',
    'pagestretch',
    'pagefilstretch',
    'pagefillstretch',
    'pagefilllstretch',
    'pageshrink',
    'pagedepth',
)

special_quantity_types = (
    'SPECIAL_INTEGER',
    'SPECIAL_DIMEN',
)


def get_initial_parameters():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    minutes_since_midnight = int(seconds_since_midnight // 60)
    integer_parameters_ = integer_parameters.copy()
    integer_parameters_['time'] = minutes_since_midnight
    integer_parameters_['day'] = now.day
    integer_parameters_['month'] = now.month
    integer_parameters_['year'] = now.year
    return Parameters(integer_parameters_,
                      dimen_parameters,
                      glue_parameters,
                      mu_glue_parameters,
                      token_parameters)


def get_local_parameters():
    return Parameters(integers={}, dimens={}, glues={}, mu_glues={}, tokens={})


class Parameters(object):

    def __init__(self, integers, dimens, glues, mu_glues, tokens):
        self.parameter_maps = {
            'integer': integers,
            'dimen': dimens,
            'glue': glues,
            'mu_glue': mu_glues,
            'token': tokens,
        }

    def _get_parameter_map_by_name(self, name):
        for parameter_map in self.parameter_maps.values():
            if name in parameter_map:
                return parameter_map
        raise KeyError

    def get_parameter_value(self, name):
        parameter_map = self._get_parameter_map_by_name(name)
        return parameter_map[name]

    def set_parameter_value(self, name, value):
        parameter_map = self._get_parameter_map_by_name(name)
        parameter_map[name] = value
