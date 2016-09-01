from datetime import datetime

now = datetime.now()
midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
seconds_since_midnight = (now - midnight).total_seconds()
minutes_since_midnight = int(seconds_since_midnight // 60)

glue_keys = ('dimen', 'stretch', 'shrink')


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
    'time': minutes_since_midnight,
    'day': now.day,
    'month': now.month,
    'year': now.year,
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

default_parameters = {
    'INTEGER_PARAMETER': integer_parameters,
    'DIMEN_PARAMETER': dimen_parameters,
    'GLUE_PARAMETER': glue_parameters,
    'MU_GLUE_PARAMETER': mu_glue_parameters,
}
