import json
import unittest

import bpy

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
            "Custom Cube":{
                "name:"WRLS_Custom_Cube",
                "blend": "Custom_parts.blend",
                "cable" : false
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
            ],
        "Custom Parts": [
            "Custom Cube"
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
