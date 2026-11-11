import importlib.util
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'stage5'))
from depgraph import Package
from svg_renderer import to_svg

NS = {'s': 'http://www.w3.org/2000/svg'}

class SvgTests(unittest.TestCase):
    def test_nodes_edges_and_monochrome(self):
        a, b = Package('A', '1'), Package('B', '1')
        root = ET.fromstring(to_svg({a, b}, {(a, b)}))
        self.assertEqual(len(root.findall('s:polyline', NS)), 1)
        self.assertEqual(len(root.findall('s:text', NS)), 4)
        for element in root.iter():
            for key in ('fill', 'stroke'):
                if key in element.attrib:
                    self.assertIn(element.attrib[key], ('black', 'white', 'none'))

    def test_cycle_and_isolated_are_valid(self):
        a, b, z = (Package(name, '1') for name in ('A', 'B', 'Z'))
        root = ET.fromstring(to_svg({a, b, z}, {(a, b), (b, a)}))
        self.assertEqual(len(root.findall('s:polyline', NS)), 2)
        self.assertEqual(len(root.findall('s:text', NS)), 6)

    def test_escape_and_deterministic(self):
        a = Package('A<&', '1')
        self.assertEqual(ET.fromstring(to_svg({a}, set())).find('s:text', NS).text, a.name)
        self.assertEqual(to_svg({a}, set()), to_svg({a}, set()))
