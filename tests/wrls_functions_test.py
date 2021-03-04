import bpy
import pytest
from mathutils import Vector

from wireless.wireless import get_list_and_position
from wireless.wireless import mirror_and_translate_head
context = bpy.context


@pytest.mark.xfail(reason='bad implementation, hard to setup')
def test_get_list_and_position():
    # GIVEN  a configuration data, a list name and a part type
    list_name = "head_categories"
    part_type = "head_types"
    # WHEN get_list and position is called
    result = get_list_and_position(context, list_name, part_type)
    # THEN it returns the expected list and position
    assert result == [
        ["Guitar Jack"],
        0,
    ]


def test_mirror_and_translate():
    # GIVEN an object
    obj = bpy.data.objects["Cube"]
    # WHEN mirror_and_translate_head is ran
    mirror_and_translate_head(obj)
    # THEN its vertices are in the expected position
    vert_1 = obj.data.vertices[0]
    assert vert_1.co == Vector((-1.0, -1.0, 1.0))
