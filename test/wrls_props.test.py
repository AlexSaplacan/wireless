"""
Test cases for curve and cables property groups
"""
import bpy
import unittest
# import runTestCases


C = bpy.context
D = bpy.data


class TestWirelessPropertyGroup(unittest.TestCase):

    def setUp(self):
        # create a new curve
        bpy.ops.curve.primitive_bezier_curve_add()
        self.curve = bpy.context.scene.objects['BezierCurve']

    def tearDown(self):
        self.curve.wrls.enable = False
        D.objects.remove(self.curve, do_unlink=True)

    def test_curve_default_wrls_status_is_undefined(self):
        self.assertEqual(self.curve.wrls.wrls_status, 'UNDEFINED')

    def test_curve_default_enable_is_not_true(self):
        self.assertFalse(self.curve.wrls.enable)

    def test_curve_wrls_status_is_curve_after_enable(self):
        self.curve.wrls.enable = True
        self.assertEqual(self.curve.wrls.wrls_status, 'CURVE')

    def test_cable_wrls_enable_is_true_after_curve_enable_is_set_true(self):
        self.curve.wrls.enable = True
        self.cable = bpy.data.objects['WRLS_Flex_Metallic']
        self.assertTrue(self.cable.wrls.enable)

    # @unittest.skip
    def test_cable_wrls_enable__to_false_also_sets_wrls_enable_false_on_curve(self):
        self.curve.wrls.enable = True
        self.cable = bpy.data.objects['WRLS_Flex_Metallic']
        C.scene.objects.active = self.cable
        self.cable.wrls.enable = False
        self.assertFalse(self.curve.wrls.enable)

    def test_cable_wrls_status_is_cable_after_curve_enable_is_set_true(self):
        self.curve.wrls.enable = True
        self.cable = bpy.data.objects['WRLS_Flex_Metallic']
        self.assertEqual(self.cable.wrls.wrls_status, 'CABLE')

    def test_curve_cable_is_default_none(self):
        self.assertEqual(self.curve.wrls.cable, '')

    def test_curve_cable_is_cable_name_after_enable(self):
        self.curve.wrls.enable = True
        self.assertEqual(self.curve.wrls.cable, 'WRLS_Flex_Metallic')

    def test_curve_use_head_and_use_tail_is_default_false(self):
        self.assertFalse(self.curve.wrls.use_head)
        self.assertFalse(self.curve.wrls.use_tail)

    def test_curve_loads_head_after_use_head_enabled(self):
        self.curve.wrls.enable = True
        self.curve.wrls.use_head = True
        self.head = bpy.data.objects['WRLS_USB_F']
        self.assertIsNotNone(self.head)

    def test_cable_use_head_and_use_tail_is_default_false(self):
        self.curve.wrls.enable = True
        self.cable = bpy.data.objects['WRLS_Flex_Metallic']
        self.assertFalse(self.cable.wrls.use_head)
        self.assertFalse(self.cable.wrls.use_tail)

    def test_cable_use_head_and_tail_is_true_after_head_enabled(self):
        self.curve.wrls.enable = True
        self.curve.wrls.use_head = True
        self.cable = bpy.data.objects['WRLS_Flex_Metallic']
        self.assertTrue(self.curve.wrls.use_head)
        self.assertFalse(self.curve.wrls.use_tail)


def runTestCases(testCases):
    for testCase in testCases:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)

    unittest.TextTestRunner().run(suite)


runTestCases([TestWirelessPropertyGroup])