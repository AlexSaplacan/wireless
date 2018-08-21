import bpy
import unittest
import json
from wireless import wireless

class TestAddData(unittest.TestCase):

    def setUp(self):

        configs = """
        {
        "Models": {
            "Flex Metallic" : {
                "name" : "WRLS_Flex_Metallic",
                "blend" : "Cables.blend",
                "cable":true
                },
            "USB F":{
                "name":"WRLS_USB_F",
                "blend" : "Cables.blend",
                "cable":false
                },
            "USB Type C":{
                "name":"WRLS_USB_Type_C",
                "blend" : "Cables.blend",
                "cable":false
                }
            },
        "model_types": {
            "All Cables":[
                "Flex Metallic"
            ],
            "Electric Cables":[
                "Round Simple",
                "Data Flat"
            ],
        "head_types":[
                "USB F",
                "USB Type C"
            ],
        "All Heads and Tails":[
                "USB F",
                "USB Type C"
            ],
        "Electric Plugs":
        [
            "Industrial 220V M"
        ],
        "Data Parts":[
                "USB F",
                "USB Type C"
            ]
        },
        "cable_categories":[
            "All Cables",
            "Electric Cables"
            ],
        "head_categories":[
            "All Heads and Tails",
            "Electric Plugs"
            ],
        "tail_categories":[
            "All Heads and Tails",
            "Electric Plugs"
            ],
        "Thumbs": [
            {
                "id":"Flex Metallic",
                "img":"WRLS_FlexMetallic.jpg"
            },
            {
                "id":"USB F",
                "img":"WRLS_USB_F.jpg"
            },
            {
                "id":"USB Type C",
                "img":"WRLS_USB_Type_C.jpg"
            }
        ]
        }
        """

        self.data = json.loads(configs)
        self.object = bpy.data.objects['Custom Cube']

    def test_add_new_model_adds_model_name_in_models(self):

        # GIVEN a configs file and an object
        # WHEN the object is added as part
        wireless.add_new_model(self.object, self.data)
        # THEN the new object is in the models
        self.assertTrue('Custom Cube' in self.data['Models'])

    def test_add_new_model_saves_name_with_WRLS_prefix(self):

        # GIVEN a configs file and an object
        # WHEN the object is added as part
        wireless.add_new_model(self.object, self.data)
        # THEN the new object is in the models
        self.assertEqual(self.data['Models']['Custom Cube']['name'], 'WRLS_Custom_Cube')

    def test_add_new_model_has_custom_blend_prefix(self):

        # GIVEN a configs file and an object
        # WHEN the object is added as part
        wireless.add_new_model(self.object, self.data)
        # THEN the new object is in the models
        self.assertEqual(self.data['Models']['Custom Cube']['blend'], 'Custom_parts.blend')

    def test_add_new_model_has_cable_true_if_wm_wrls_is_cable(self):

        # GIVEN a configs file and an object, and wm_wrls.type_of_part is "Cable"
        bpy.context.window_manager.wrls.type_of_part = 'Cable'
        # WHEN the object is added as part
        wireless.add_new_model(self.object, self.data)
        # THEN the new object is in the models and cable key is true
        self.assertTrue(self.data['Models']['Custom Cube']['cable'])

    def test_add_new_model_has_cable_false_if_wm_wrls_is_headtail(self):

        # GIVEN a configs file and an object, and wm_wrls.type_of_part is "Head / tail"
        bpy.context.window_manager.wrls.type_of_part = 'Head / Tail'
        # WHEN the object is added as part
        wireless.add_new_model(self.object, self.data)
        # THEN the new object is in the models and cable key is False
        self.assertFalse(self.data['Models']['Custom Cube']['cable'])

    def test_add_to_category_all_cables_if_wm_wrls_is_cable(self):

        # GIVEN a configs file and a new object with wm_wrls.type_of_part is cable
        bpy.context.window_manager.wrls.type_of_part = 'Cable'
        # WHEN the object is added as part
        wireless.add_to_category(self.object, self.data)
        self.assertIn('Custom Cube', self.data['model_types']['All Cables'])

    def test_add_to_category_all_cables_if_wm_wrls_is_cable_and_category_is_not_all_cables(self):

        # GIVEN new object with wm_wrls.type_of_part is cable
        bpy.context.window_manager.wrls.type_of_part = 'Cable'
        bpy.context.window_manager.wrls.cable_categories = 'Electric Cables'
        # WHEN the object is added as part
        wireless.add_to_category(self.object, self.data)
        self.assertIn('Custom Cube', self.data['model_types']['All Cables'])

    def test_add_to_category_if_wm_wrls_is_cable_and_category_is_not_all_cables(self):

        # GIVEN new object with wm_wrls.type_of_part is cable
        bpy.context.window_manager.wrls.type_of_part = 'Cable'
        bpy.context.window_manager.wrls.cable_categories = 'Electric Cables'
        # WHEN the object is added as part
        wireless.add_to_category(self.object, self.data)
        self.assertIn('Custom Cube', self.data['model_types']['Electric Cables'])

    def test_add_to_category_all_heads_if_wm_wrls_is_not_cable(self):

        # GIVEN a configs file and a new object with wm_wrls.type_of_part is cable
        bpy.context.window_manager.wrls.type_of_part = 'Head / Tail'
        # WHEN the object is added as part
        wireless.add_to_category(self.object, self.data)
        self.assertIn('Custom Cube', self.data['model_types']['All Heads and Tails'])

    def test_add_to_category_all_heads_if_wm_wrls_not_cable_and_category_not_all_heads(self):

        # GIVEN new object with wm_wrls.type_of_part is cable
        bpy.context.window_manager.wrls.type_of_part = 'Head / Tail'
        bpy.context.window_manager.wrls.head_categories = 'Electric Plugs'
        # WHEN the object is added as part
        wireless.add_to_category(self.object, self.data)
        self.assertIn('Custom Cube', self.data['model_types']['Electric Plugs'])

    def test_add_to_category_if_wm_wrls_is_head_and_category_is_not_all_heads(self):

        # GIVEN new object with wm_wrls.type_of_part is cable
        bpy.context.window_manager.wrls.type_of_part = 'Head / Tail'
        bpy.context.window_manager.wrls.head_categories = 'Electric Plugs'
        # WHEN the object is added as part
        wireless.add_to_category(self.object, self.data)
        self.assertIn('Custom Cube', self.data['model_types']['Electric Plugs'])

    def test_add_thumb_adds_in_list_element_with_id_as_object_name(self):
        # GIVEN a new object
        # WHEN ad_thumb is ran
        wireless.add_thumb(self.object, self.data)
        # THEN a new element with id:name of the object is added
        self.assertEqual(self.data['Thumbs'][-1]['id'], 'Custom Cube')


    def test_add_thumb_adds_in_list_element_with_img_as_converted_object_name(self):
        # GIVEN a new object
        # WHEN ad_thumb is ran
        wireless.add_thumb(self.object, self.data)
        # THEN a new element with img:name of the converted object is added
        self.assertEqual(self.data['Thumbs'][-1]['img'], 'WRLS_Custom_Cube.jpg')

def runTestCases(testCases):
    for testCase in testCases:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)

    unittest.TextTestRunner().run(suite)


runTestCases([TestAddData])