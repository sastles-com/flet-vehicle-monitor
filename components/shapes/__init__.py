"""
Shape components for vehicle monitoring application
"""

from .bar_circumference import (
    BarCircumferenceManager, 
    CircumferencePoint, 
    Position,
    create_bar_circumference_from_json
)

from .bar_shape_integration import (
    IntegratedBarShape,
    BarShapeFactory
)

__all__ = [
    'BarCircumferenceManager',
    'CircumferencePoint', 
    'Position',
    'IntegratedBarShape',
    'BarShapeFactory',
    'create_bar_circumference_from_json'
]