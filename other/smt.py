import sys
from subprocess import call, check_output
from xml.etree.ElementTree import ElementTree

from svgpathtools import (
    Arc,
    CubicBezier,
    Path,
    QuadraticBezier,
    disvg,
    svg2paths2,
    wsvg,
)


def append_subpath(path, subpath):
    for node in subpath:
        path.append(node)


def bbox_to_barea(bbox):
    return (bbox[1] - bbox[0]) * (bbox[3] - bbox[2])


def scale_path_to_bbox(path, bbox):
    """
    Scales a path to be contained by a bounding box.
    Expands the path from the center of the bounding box.
    Does not place the path in the center of the bounding box.

    bbox has the same format as svgpathtools', (x1, y1, x2, y2)
    """
    original_bbox = path.bbox()

    bbox_center = compute_bbox_center(bbox)
    # we'll be comparing each path bbox coordinate to the bbox center
    # it's easier done if we have a tuple with 4 elements for the center too
    two_centers = (
        bbox_center.real,
        bbox_center.imag,
        bbox_center.real,
        bbox_center.imag,
    )
    # furthest projection is the path bbox coordinate that has the most
    #   difference with the bbox center
    # destination is the corresponding wanted bbox coordinate
    # center is the corresponding center coordinate
    furthest_projection, destination, center = max(
        zip(original_bbox, bbox, two_centers), key=lambda t: abs(t[0] - t[2])
    )
    scale = abs(center - destination) / abs(center - furthest_projection)

    # if we just applied the scaling factor, the path would be shifted
    #   in a top-left to bottom-right motion so we need to translate the path
    #   back to make the scaling effect from the bbox' center
    translation_constant = bbox_center * (1 - scale)

    new_path = Path()
    for node in path:
        node.start = node.start * scale + translation_constant
        node.end = node.end * scale + translation_constant
        if isinstance(node, CubicBezier):
            node.control1 = node.control1 * scale + translation_constant
            node.control2 = node.control2 * scale + translation_constant
        elif isinstance(node, QuadraticBezier):
            node.control = node.control * scale
        elif isinstance(node, Arc):
            node.radius = node.radius * scale
        new_path.append(node)
    return new_path


def bbox_as_two_points(bbox):
    """Returns a tuple of points (complex numbers) representing the bbox"""
    return (bbox[0] + bbox[1] * 1j, bbox[2] + bbox[3] * 1j)


def points_center(p1, p2):
    """Returns the center of two points"""
    return (p1 + p2) / 2


def compute_bbox_center(bbox):
    p1, p2 = bbox_as_two_points(bbox)
    return points_center(p1, p2)


def extract_base_icon(input_file, output_file):
    """Also scales the shape to use more space in the drawing"""
    center = 24 + 24j
    paths, attributes, svg_attributes = svg2paths2(input_file)
    if len(paths) > 1:
        raise NotImplementedError("Can't handle more than one path for now")
    path = paths[0]
    subpaths = path.continuous_subpaths()
    outer_shape = max(subpaths, key=lambda x: bbox_to_barea(x.bbox()))
    subpaths.remove(outer_shape)

    # Generate a new path with the remaining shapes
    new_path = Path()
    for subpath in subpaths:
        append_subpath(new_path, subpath)

    # Scale path up
    new_path = scale_path_to_bbox(new_path, (2, 2, 46, 46))
    wsvg(
        [new_path],
        attributes=attributes,
        svg_attributes=svg_attributes,
        filename=output_file,
    )


def add_circle(input_file, output_file):
    """
    Adds a circle around the base icon. This will have the effect to invert
    the mask.
    """
    paths, attributes, svg_attributes = svg2paths2(input_file)
    if len(paths) > 1:
        raise NotImplementedError("Can't handle more than one path for now")
    path = paths[0]

    # Scale path down
    new_path = scale_path_to_bbox(path, (6, 6, 42, 42))

    # Add circle
    new_path.append(Arc(24 + 2j, 22+22j, 180, 0, 1, 24 + 46j))
    new_path.append(Arc(24 + 46j, 22+22j, 180, 0, 1, 24 + 2j))

    wsvg(
        [new_path],
        attributes=attributes,
        svg_attributes=svg_attributes,
        filename=output_file,
    )


def main():
    base_name = sys.argv[1]
    input_file = f"icons/{base_name}.svg"
    output_file = f"icons/{base_name}.new.svg"
    try:
        extract_base_icon(input_file, output_file)
    except Exception as ex:
        print(ex)


main()
