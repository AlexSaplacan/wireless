import bpy
import pytest


C = bpy.context
D = bpy.data


@pytest.fixture
def bezier_curve():
    bpy.ops.curve.primitive_bezier_curve_add()
    curve = bpy.context.scene.objects['BezierCurve']
    yield curve
    curve.wrls.enable = False
    D.objects.remove(curve, do_unlink=True)


def test_wireless_button_off_when_curve_selected(
    bezier_curve,
) -> None:
    bezier_curve.wrls.enable = True
    bpy.context.object.wrls.enable = False
    assert bezier_curve.wrls.enable is False


@pytest.mark.xfail()
def test_wireless_button_off_when_cable_selected(
    bezier_curve,
) -> None:
    bezier_curve.wrls.enable = True
    cable = bpy.data.objects['WRLS_Flex_Metallic']
    C.view_layer.objects.active = cable
    bpy.context.object.wrls.enable = False
    assert cable.wrls.enable is False
    assert bezier_curve.wrls.enable is False
