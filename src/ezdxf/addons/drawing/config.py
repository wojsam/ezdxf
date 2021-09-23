import dataclasses
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from ezdxf import disassemble


class LinePolicy(Enum):
    """
    Attributes:
        SOLID: draw all lines as solid regardless of the linetype style
        APPROXIMATE: use the closest approximation available to the
            backend for rendering styled lines
        ACCURATE: analyse and render styled lines as accurately as
            possible. This approach is slower and is not well suited
            to interactive applications.
    """

    SOLID = auto()
    APPROXIMATE = auto()
    ACCURATE = auto()


class ProxyGraphicPolicy(Enum):
    """The action to take when an entity with a proxy graphic is encountered

    Note: To get proxy graphics support proxy graphics have to be loaded:
        Set the global option ezdxf.options.load_proxy_graphics to True.

    Note: This can not prevent drawing proxy graphic inside of blocks,
        because this is outside of the domain of the drawing add-on!

    Attributes:
        IGNORE: do not display proxy graphics (skip_entity will be called instead)
        SHOW: if the entity cannot be rendered directly (eg if not implemented)
            but a proxy is present: display the proxy
        PREFER: display proxy graphics even for entities where direct rendering
            is available
    """

    IGNORE = auto()
    SHOW = auto()
    PREFER = auto()


class HatchPolicy(Enum):
    """The action to take when a HATCH entity is encountered

    Attributes:
        IGNORE: do not show HATCH entities at all
        SHOW_OUTLINE: show only the outline of HATCH entities
        SHOW_SOLID: show HATCH entities but draw with solid fill
            regardless of the pattern
        SHOW_APPROXIMATE_PATTERN: show HATCH entities using the closest
            approximation available to the current backend

    """

    IGNORE = auto()
    SHOW_OUTLINE = auto()
    SHOW_SOLID = auto()
    SHOW_APPROXIMATE_PATTERN = auto()


class NestedPolygonDetectionMethod(Enum):
    NONE = auto()
    FAST = auto()


@dataclass(frozen=True)
class Configuration:
    """Configuration options for the rendering frontend

    Attributes:
        pdsize: the size to draw POINT entities (in drawing units)
            set to None to use the $PDSIZE value from the dxf document header
        pdmode: point styling mode (see POINT documentation)
            0     5% of draw area height
            <0    Specifies a percentage of the viewport size
            >0    Specifies an absolute size
            None  use the $PDMODE value from the dxf document header
        measurement: whether to use metric or imperial units
            0     use imperial units (in, ft, yd, ...)
            1     use metric units (ISO meters)
            None  use the $MEASUREMENT value from the dxf document header
        show_defpoints: whether to show or filter out POINT entities on the defpoints layer
        proxy_graphic_policy: the action to take when a proxy graphic is encountered
        line_policy: the method to use when drawing styled lines (eg dashed, dotted etc)
        hatch_policy: the method to use when drawing HATCH entities
        infinite_line_length: the length to use when drawing infinite lines
        lineweight_scaling:
            set to 0.0 for a constant minimal width
            the current result is correct, in SVG the line width is 0.7 points for 0.25mm as
            required, but it often looks too thick
        min_lineweight: the minimum line width in 1/300 inch
            None    let the backend choose
        min_dash_length: the minimum length for a dash when drawing a styled line
            (default value is arbitrary)
        max_flattening_distance: Max flattening distance in drawing units
            see Path.flattening documentation.
            The backend implementation should calculate an appropriate value,
            like 1 screen- or paper pixel on the output medium, but converted
            into drawing units. Sets Path() approximation accuracy
        circle_approximation_count: Approximate a full circle by `n` segments, arcs
            have proportional less segments
        approximation_max_sagitta:
            The sagitta (also known as the versine) is a line segment drawn
            perpendicular to a chord, between the midpoint of that chord and the
            arc of the circle. https://en.wikipedia.org/wiki/Circle not used yet!
            Could be used for all curves CIRCLE, ARC, ELLIPSE and SPLINE
            the default value of 0.01 => for drawing unit = 1m, max sagitta = 1cm
        nested_polygon_detection: required to draw polygons with holes, can be disabled
    """

    pdsize: Optional[int] = 1
    pdmode: Optional[int] = 0
    measurement: Optional[int] = None
    show_defpoints: bool = False
    proxy_graphic_policy: ProxyGraphicPolicy = ProxyGraphicPolicy.SHOW
    line_policy: LinePolicy = LinePolicy.APPROXIMATE
    hatch_policy: HatchPolicy = HatchPolicy.SHOW_APPROXIMATE_PATTERN
    infinite_line_length: float = 20
    lineweight_scaling: float = 1.0
    min_lineweight: Optional[float] = None
    min_dash_length: float = 0.1
    max_flattening_distance: float = disassemble.Primitive.max_flattening_distance
    circle_approximation_count: int = 128
    approximation_max_sagitta = 0.01
    nested_polygon_detection: NestedPolygonDetectionMethod = (
        NestedPolygonDetectionMethod.FAST
    )

    def with_changes(self, **kwargs) -> "Configuration":
        params = dataclasses.asdict(self)
        for k, v in kwargs.items():
            params[k] = v
        return Configuration(**params)
