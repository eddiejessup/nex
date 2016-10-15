from datetime import datetime

from .common import TerminalToken


integer_parameter_names = (
    'pretolerance',
    'tolerance',
    'hbadness',
    'vbadness',
    'linepenalty',
    'hyphenpenalty',
    'exhyphenpenalty',
    'binoppenalty',
    'relpenalty',
    'clubpenalty',
    'widowpenalty',
    'displaywidowpenalty',
    'brokenpenalty',
    'predisplaypenalty',
    'postdisplaypenalty',
    'interlinepenalty',
    'floatingpenalty',
    'outputpenalty',
    'doublehyphendemerits',
    'finalhyphendemerits',
    'adjdemerits',
    'looseness',
    'pausing',
    'holdinginserts',
    'tracingonline',
    'tracingmacros',
    'tracingstats',
    'tracingparagraphs',
    'tracingpages',
    'tracingoutput',
    'tracinglostchars',
    'tracingcommands',
    'tracingrestores',
    'language',
    'uchyph',
    'lefthyphenmin',
    'righthyphenmin',
    'globaldefs',
    'maxdeadcycles',
    'hangafter',
    'fam',
    'mag',
    'escapechar',
    'defaulthyphenchar',
    'defaultskewchar',
    'endlinechar',
    'newlinechar',
    'delimiterfactor',
    # These time ones will be set in get_initial_parameters.
    'time',
    'day',
    'month',
    'year',
    'showboxbreadth',
    'showboxdepth',
    'errorcontextlines',
)

dimen_parameter_names = (
    'hfuzz',
    'vfuzz',
    'overfullrule',
    'hsize',
    'vsize',
    'maxdepth',
    'splitmaxdepth',
    'boxmaxdepth',
    'lineskiplimit',
    'delimitershortfall',
    'nulldelimiterspace',
    'scriptspace',
    'mathsurround',
    'predisplaysize',
    'displaywidth',
    'displayindent',
    'parindent',
    'hangindent',
    'hoffset',
    'voffset',
)

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
glue_keys = ('dimen', 'stretch', 'shrink')

mu_glue_parameter_names = (
    'thinmuskip',
    'medmuskip',
    'thickmuskip',
)

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


parameter_type_to_names = {
    'INTEGER_PARAMETER': integer_parameter_names,
    'DIMEN_PARAMETER': dimen_parameter_names,
    'GLUE_PARAMETER': glue_parameter_names,
    'MU_GLUE_PARAMETER': mu_glue_parameter_names,
    'TOKEN_PARAMETER': token_parameter_names,
}
parameter_types = tuple(parameter_type_to_names.keys())


def is_parameter_type(type_):
    return type_ in parameter_types


def get_initial_parameters():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    minutes_since_midnight = int(seconds_since_midnight // 60)

    integer_parameters = {name: 0 for name in integer_parameter_names}
    integer_parameters['tolerance'] = 10000
    integer_parameters['maxdeadcycles'] = 25
    integer_parameters['hangafter'] = 1
    integer_parameters['mag'] = 1000
    integer_parameters['escapechar'] = ord('\\')
    integer_parameters['endlinechar'] = ord('\r')
    # These time ones will be set in get_initial_parameters.
    integer_parameters['time'] = minutes_since_midnight
    integer_parameters['day'] = now.day
    integer_parameters['month'] = now.month
    integer_parameters['year'] = now.year

    dimen_parameters = {name: 0 for name in dimen_parameter_names}

    get_zero_glue = lambda: {k: 0 for k in glue_keys}
    glue_parameters = {p: get_zero_glue() for p in glue_parameter_names}
    mu_glue_parameters = {p: get_zero_glue() for p in mu_glue_parameter_names}

    get_empty_token_list = lambda: TerminalToken(
        type_='BALANCED_TEXT_AND_RIGHT_BRACE',
        value=[],
        line_nr='scratch',
    )
    token_parameters = {p: get_empty_token_list()
                        for p in token_parameter_names}

    return Parameters(integer_parameters,
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
        raise KeyError('Parameter ''{}'' not known'.format(name))

    def get_parameter_value(self, name):
        parameter_map = self._get_parameter_map_by_name(name)
        return parameter_map[name]

    def set_parameter_value(self, name, value):
        parameter_map = self._get_parameter_map_by_name(name)
        parameter_map[name] = value
