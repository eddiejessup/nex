"""
Define the list of physical units that TeX can deal with, and their sizes.
Internally, everything is done in terms of 'scaled points', 'sp' for short,
defined such that 65536 scaled points = 1 point.
"""
from typing import Dict

from enum import Enum


class Unit(Enum):
    point = 'pt'
    pica = 'pc'
    inch = 'in'
    big_point = 'bp'
    centimetre = 'cm'
    millimetre = 'mm'
    didot_point = 'dd'
    cicero = 'cc'
    scaled_point = 'sp'
    fil = 'fil'


class MuUnit(Enum):
    mu = 'mu'


class InternalUnit(Enum):
    em = 'em'
    ex = 'ex'


units_in_sp: Dict[Unit, int] = {}
units_in_sp[Unit.scaled_point] = 1
units_in_sp[Unit.point] = 65536 * units_in_sp[Unit.scaled_point]
units_in_sp[Unit.pica] = 12 * units_in_sp[Unit.point]
units_in_sp[Unit.inch] = round(72.27 * units_in_sp[Unit.point])
units_in_sp[Unit.big_point] = round((1 / 72) * units_in_sp[Unit.inch])
units_in_sp[Unit.centimetre] = round((1 / 2.54) * units_in_sp[Unit.inch])
units_in_sp[Unit.millimetre] = round(0.1 * units_in_sp[Unit.centimetre])
units_in_sp[Unit.didot_point] = round((1238 / 1157) * units_in_sp[Unit.point])
units_in_sp[Unit.cicero] = 12 * units_in_sp[Unit.didot_point]


# TeXbook page 58.
# "TeX will not deal with dimensions whose absolute value is 2^30 sp or more."
MAX_DIMEN: int = 2 ** 30 - 1
