from xml.etree.ElementTree import ElementTree
from svg.path import parse_path, Path, Close, CubicBezier, QuadraticBezier, Arc, Move
from cmath import polar
from subprocess import check_output, call
import sys

def open_xml(filename):
    print('opening xml file')
    xml = ElementTree()
    xml.parse(filename)
    return xml

def find_svg_center(xml):
    print('searching svg center')
    viewbox = xml.getroot().attrib.get('viewBox').split(' ')
    viewbox = list(map(lambda x: float(x), viewbox))
    center = (viewbox[0] + viewbox[2])/2 + (viewbox[1] + viewbox[3])*1j/2
    return center

def extract_path_from_svg(xml):
    print('extracting path from svg')
    paths = list(xml.getroot())
    if len(paths) != 1:
        # svg with multiple paths are not handled yet 
        print('wtf')
        print(input_name)
        raise NotImplementedError
    else:
        data = paths[0].get('d')
    return parse_path(data)

def analyze_path(path, center):
    """Returns a list of dicts with the following keys:
    - data: the split shape object
    - distances: list of distances from the shape's points to the center
    - meandistance: mean of distances
    """
    print('analysing path data')
    group = {}
    groups = []
    for node in list(path):
        group.setdefault('data', []).append(node)
        # Compute distance to center for each point in the path
        group.setdefault('distances', []).append(
                polar(node.start - center)[0]
                )
        # Each shape ends with a Close node
        if type(node) == Close:
            groups.append(group)
            group['meandistance'] = sum(group['distances'])/len(group['distances'])
            group = {}
    return groups

def remove_outer_shape(input_name, output_name):
    """Also scales back the shape to fill the drawing"""
    print('deleting outer shape')
    # todo remove extractions, and fix the size to 48 px
    # or use a parameter, whatever
    xml = open_xml(input_name)
    center = find_svg_center(xml)
    path = extract_path_from_svg(xml)
    groups = analyze_path(path, center)

    # The mean distance to the center is used to find the outermost shape
    to_remove = max(groups, key=lambda x: x['meandistance'])
    groups.remove(to_remove)

    # Generate a new path with the remaining shapes
    new_path = Path()
    for group in groups:
        for node in group['data']:
            new_path.append(node)

    # Write output file
    xml.getroot()[0].set('d', new_path.d())
    xml.write(output_name)

    # Find output file size
    width, height = extract_svg_size(output_name)
    ratio = get_optimal_scaling_ratio(height, width, 48)
    resized_path = resize_path(new_path, ratio)

    # Write output file
    xml.getroot()[0].set('d', new_path.d())
    xml.write(output_name)

    # Center drawing
    call(['inkscape', '--verb', 'EditSelectAll', '--verb', 'AlignHorizontalCenter', '--verb', 'AlignVerticalCenter', '--verb', 'FileSave', '--verb', 'FileQuit', output_name])
    

def extract_svg_size(filename):
    print('extracting svg size')
    width = float(check_output(['inkscape', '-W', filename]))
    height = float(check_output(['inkscape', '-H', filename]))
    print(f'found svg size: {width} {height}')
    return width, height

def get_optimal_scaling_ratio(height, width, target):
    """Finds the scaling ratio that should be applied in order for the graphics to be contained in a square of a target size."""
    print('computing scaling ratio')
    if height > width:
        ratio = target / height
    else:
        ratio = target / width
    print(f'scaling ratio is {ratio}')
    return ratio

def resize_path(path, ratio):
    print('resizing path')
    new_path = Path()
    for node in path:
        node.start = node.start * ratio
        node.end = node.end * ratio
        if isinstance(node, CubicBezier):
            node.control1 = node.control1 * ratio
            node.control2 = node.control2 * ratio
        elif isinstance(node, QuadraticBezier):
            node.control = node.control * ratio
        elif isinstance(node, Arc):
            node.radius = node.radius * ratio
        new_path.append(node)
    return new_path 

# base_names = ['feeder', 'forecastie', 'keepassdx', 'downloads', 'casper', 'cythara', 'clover', 'bus_circle', 'a2048', 'aimsicd', 'anydesk', 'apex', 'arbetsfor', 'atomic', 'audinaut', 'authy', 'battery', 'bible', 'birthdayadapter', 'bitcoin', 'bluetooth']
# for base_name in base_names:
#     input_file = f'icons/{base_name}.svg'
#     output_file = f'icons/{base_name}.new.svg'
#     try:
#         remove_outer_shape(input_file, output_file)
#     except Exception:
#         print('fail')
#         print(base_name)

def main():
    # print(sys.argv[1])
    base_name = sys.argv[1]
    # base_name = 'blabla_circle'
    input_file = f'icons/{base_name}.svg'
    output_file = f'icons/{base_name}.new.svg'
    try:
        remove_outer_shape(input_file, output_file)
    except Exception as ex:
        print(ex)
        

# base_name = 'blabla_circle'
# input_file = f'icons/{base_name}.svg'
# xml = open_xml(input_file)
# path = extract_path_from_svg(xml)
main()
