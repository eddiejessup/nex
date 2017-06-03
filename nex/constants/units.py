"""
Define the list of physical units that TeX can deal with, and their sizes.
Internally, everything is done in terms of 'scaled points', 'sp' for short,
defined such that 65536 scaled points = 1 point.
"""
from enum import Enum


class PhysicalUnit(Enum):
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


units_in_scaled_points = {}
units_in_scaled_points[PhysicalUnit.scaled_point] = 1
units_in_scaled_points[PhysicalUnit.point] = 65536 * units_in_scaled_points[PhysicalUnit.scaled_point]
units_in_scaled_points[PhysicalUnit.pica] = 12 * units_in_scaled_points[PhysicalUnit.point]
units_in_scaled_points[PhysicalUnit.inch] = 72.27 * units_in_scaled_points[PhysicalUnit.point]
units_in_scaled_points[PhysicalUnit.big_point] = (1.0 / 72.0) * units_in_scaled_points[PhysicalUnit.inch]
units_in_scaled_points[PhysicalUnit.centimetre] = (1.0 / 2.54) * units_in_scaled_points[PhysicalUnit.inch]
units_in_scaled_points[PhysicalUnit.millimetre] = 0.1 * units_in_scaled_points[PhysicalUnit.centimetre]
units_in_scaled_points[PhysicalUnit.didot_point] = (1238.0 / 1157.0) * units_in_scaled_points[PhysicalUnit.point]
units_in_scaled_points[PhysicalUnit.cicero] = 12 * units_in_scaled_points[PhysicalUnit.didot_point]


# TeXbook page 58.
# "TeX will not deal with dimensions whose absolute value is 2^30 sp or more."
MAX_DIMEN = 2 ** 30 - 1
