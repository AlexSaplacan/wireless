import os

import bpy
import pytest

from wireless.wireless import set_wrls_collection


C = bpy.context
D = bpy.data


@pytest.fixture
def bezier_curve():
    bpy.ops.curve.primitive_bezier_curve_add()
    curve = bpy.context.scene.objects['BezierCurve']
    yield curve
    curve.wrls.enable = False
    D.objects.remove(curve, do_unlink=True)


def test_wm_wrls_property_exists() -> None:
    assert bpy.context.window_manager.wrls is not None


def test_curve_default_wrls_status_is_undefined(bezier_curve) -> None:
    assert bezier_curve.wrls.wrls_status == "UNDEFINED"


def test_curve_default_enable_is_not_true(bezier_curve):
    assert bezier_curve.wrls.enable is False


def test_curve_wrls_status_is_curve_after_enable(bezier_curve) -> None:
    bezier_curve.wrls.enable = True
    assert bezier_curve.wrls.wrls_status == 'CURVE'


def test_cable_wrls_enable_is_true_after_curve_enable_is_set_true(
    bezier_curve,
) -> None:
    bezier_curve.wrls.enable = True
    cable = bpy.data.objects['WRLS_Flex_Metallic']
    assert cable.wrls.enable is True


@pytest.mark.xfail(reason='bad implemented')
def test_cable_wrls_enable_false_also_sets_wrls_enable_false_on_curve(
    bezier_curve,
) -> None:
    bezier_curve.wrls.enable = True
    cable = bpy.data.objects['WRLS_Flex_Metallic']
    C.view_layer.objects.active = cable
    cable.wrls.enable = False
    assert bezier_curve.wrls.enable is True


def test_set_wrls_collection():
    # WHEN set_wrls_collection is ran
    set_wrls_collection()
    # THEN WrlS collection exists
    assert bpy.data.collections['WrlS'] is not None
