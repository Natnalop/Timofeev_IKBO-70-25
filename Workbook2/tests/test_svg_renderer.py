from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as element_tree
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'stage5'))
from depgraph import Package, Config, parse_index, build_graph
from svg_renderer import to_svg

NS = {'s': 'http://www.w3.org/2000/svg'}

class SvgTests(unittest.TestCase):
    def test_nodes_edges_and_monochrome(self):
        a, b = Package('A', '1'), Package('B', '1')
        root = element_tree.fromstring(to_svg({a, b}, {(a, b)}))
        self.assertEqual(len(root.findall('s:polyline', NS)), 1)
        self.assertEqual(len(root.findall('s:text', NS)), 4)
        for element in root.iter():
            for key in ('fill', 'stroke'):
                if key in element.attrib:
                    self.assertIn(element.attrib[key], ('black', 'white', 'none'))

    def test_cycle_and_isolated_are_valid(self):
        a, b, z = (Package(name, '1') for name in ('A', 'B', 'Z'))
        root = element_tree.fromstring(to_svg({a, b, z}, {(a, b), (b, a)}))
        self.assertEqual(len(root.findall('s:polyline', NS)), 2)
        self.assertEqual(len(root.findall('s:text', NS)), 6)

    def test_escape_and_deterministic(self):
        a = Package('A<&', '1')
        self.assertEqual(element_tree.fromstring(to_svg({a}, set())).find('s:text', NS).text, a.name)
        self.assertEqual(to_svg({a}, set()), to_svg({a}, set()))

    def test_curl_routes_are_orthogonal_and_avoid_nodes(self):
        with tarfile.open(ROOT / 'stage5/examples/APKINDEX.tar.gz') as archive:
            repo = parse_index(archive.extractfile('APKINDEX').read().decode())
        package = repo.names['curl'][0]
        graph = build_graph(repo, package, Config('curl', '', False, package.version, 20, ''))
        svg = element_tree.fromstring(to_svg(*graph))
        boxes = [tuple(float(rect.attrib[k]) for k in ('x', 'y', 'width', 'height'))
                 for rect in svg.findall('s:rect', NS) if 'x' in rect.attrib]
        lines = svg.findall('s:polyline', NS)
        self.assertEqual(len(lines), len(graph[1]))
        for line in lines:
            points = [tuple(map(float, point.split(','))) for point in line.attrib['points'].split()]
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                self.assertTrue(x1 == x2 or y1 == y2)
                for x, y, w, h in boxes:
                    if y1 == y2:
                        crosses = y < y1 < y+h and max(min(x1,x2),x) < min(max(x1,x2),x+w)
                    else:
                        crosses = x < x1 < x+w and max(min(y1,y2),y) < min(max(y1,y2),y+h)
                    self.assertFalse(crosses, (line.attrib['points'], (x,y,w,h)))
