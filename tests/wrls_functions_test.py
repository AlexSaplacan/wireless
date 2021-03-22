import bpy
import pytest
from mathutils import Vector

from wireless.configs import data as data
from wireless.wireless import get_list_and_position
from wireless.wireless import get_model_image_path
from wireless.wireless import get_part_category
from wireless.wireless import hide_model
from wireless.wireless import link_obj_to_collection
from wireless.wireless import mirror_and_translate_head
from wireless.wireless import new_models_have_missing_images
from wireless.wireless import new_models_in_models_list
from wireless.wireless import set_wrls_collection

C = bpy.context


@pytest.fixture
def temp_coll():
    coll = bpy.data.collections.new('temp_coll')
    master_coll = C.scene.collection
    master_coll.children.link(coll)
    C.view_layer.update()


@pytest.fixture
def part_types():
    data["cable_categories"].append("Good Cables")
    data["head_categories"].append("Good Heads")
    data["tail_categories"].append("Good Tails")

    win_wrls = C.window_manager.wrls
    win_wrls.cable_categories = "Good Cables"
    win_wrls.head_categories = "Good Heads"
    win_wrls.tail_categories = "Good Tails"
    yield
    win_wrls.cable_categories = "All Cables"
    win_wrls.head_categories = "All Heads and Tails"
    win_wrls.tail_categories = "All Heads and Tails"


@pytest.fixture
def c_data():
    c = {
  "Models": {
    "Some Cable": {
      "blend": "Cables.blend",
      "cable": False,
      "name": "WRLS_SomeCable",
    },
    "ATX 4pin": {
      "blend": "Cables.blend",
      "cable": False,
      "name": "WRLS_ATX_4pin",
    },
},

"Thumbs": [
    {
      "id": "Some Cable",
      "img": "WRLS_SomeCable.jpg",
    },
    {
      "id": "USB F",
      "img": "WRLS_USB_F.jpg",
    },
],
  "model_types": {
    "Custom Parts": [
      "Some Cable",
      "Burp Cable",
    ],
  },
}
    return c

@pytest.mark.xfail()
def test_get_part_cagegory(part_types):
    # GIVEN  a configuration data, a list name and a part type
    list_name = "head_categories"
    # WHEN get_list and position is called
    result = get_part_category(list_name)
    # THEN it returns the expected list and position
    assert result == "Good Heads"


def test_mirror_and_translate():
    # GIVEN an object
    obj = bpy.data.objects["Cube"]
    # WHEN mirror_and_translate_head is ran
    mirror_and_translate_head(obj)
    # THEN its vertices are in the expected position
    vert_1 = obj.data.vertices[0]
    assert vert_1.co == Vector((-1.0, -1.0, 1.0))


def test_hide_model():
    # GIVEN an object in the scene
    obj = bpy.data.objects["Cube"]
    # WHEN hide_object is ran
    hide_model(obj)

    # THEN the model is hidden in viewport and render
    assert obj.hide_viewport is True
    assert obj.hide_render is True


def test_link_obj_to_collection(temp_coll):
    # GIVEN an object in the scene
    obj = bpy.data.objects["Cube"]
    # WHEN link_obj_to_collection() is called
    link_obj_to_collection(obj, col="temp_coll")
    # THEN the object can be found in the collection.
    assert C.scene.collection.children["temp_coll"].objects.get("Cube")


@pytest.mark.parametrize(
    ("custom_models", "models_list", "expected"),
    (
        (["maat", "max"], ["foo", "bar"], False),
        (["foo", "max"], ["foo", "bar"], True),
    ),


)
def test_new_models_in_models_list(
    custom_models,
    models_list,
    expected,
):
    # GIVEN two lists of models
    # WHEN new_models_in_models_list is ran
    result = new_models_in_models_list(
        custom_models,
        models_list,
    )
    # THEN it returns the expected result
    assert result == expected


def test_get_model_image_path(tmpdir, c_data):
    # GIVEN a directory with img_path
    img = tmpdir.mkdir('thumbs').join('WRLS_SomeCable.jpg')
    # WHEN get_model_image_path is called
    result = get_model_image_path(tmpdir, "Some Cable", c_data)
    # THEN it returns the expected result
    assert result == str(img)


@pytest.mark.parametrize(
    ("model_list", "expected"),
    (
        (['Some Cable'], False),
        (['Poo Cable'], 'Could not find thumbnail for Poo Cable. Aborting'),
        (['Some Cable', 'Poo Cable'], 'Could not find thumbnail for Poo Cable. Aborting'),
    ),
)
def test_new_models_have_missing_images(
    tmpdir,
    model_list,
    c_data,
    expected,
):
    # GIVEN a directory with img_path and a cables config
    img = tmpdir.mkdir('thumbs').join('WRLS_SomeCable.jpg')
    with open(img, 'w')as f:
        f.write("oops")
    # WHEN new_models_have_missing_images is called
    result = new_models_have_missing_images(tmpdir, model_list, c_data)
    # THEN result is like expected
    assert result == expected
