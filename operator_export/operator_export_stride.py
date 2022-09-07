"""
Module charged with the handling of Strides
"""
# coding=utf-8
from ..operator_utilities.file_definition_bwm import (
    StrideType,
    StrideSize,
    Vertex,
    Stride,
)


def create_vertex_stride(vertex: Vertex) -> Stride:
    """
    From a vertex create the corresponding Stride
    """
    stride = Stride()

    stride.idSizes.append((StrideType.POINT, StrideSize.POINT_3D))
    stride.stride = 12
    if vertex.normal:
        stride.idSizes.append((StrideType.NORMAL, StrideSize.POINT_3D))
        stride.stride += 12
    for uv in vertex.uvs:
        stride.idSizes.append((StrideType.UV_MAP, StrideSize.TUPLE))
        stride.stride += 8

    stride.count = len(stride.idSizes)
    stride.size = 0x88 - 4 - (8 * stride.count)
    stride.unknown = bytes([0 for i in range(stride.size)])

    return stride


def create_skin_strides() -> Stride:
    """
    Create the strides deffining a Bone/Weight table of a Skin
    """
    strides = [Stride() for i in range(8)]

    for stride in strides[:4]:
        stride.count = 1
        stride.idSizes.append((StrideType.BONE_INDEX, StrideSize.BYTE))
        stride.stride = 1
        stride.size = 0x7C
        stride.unknown = bytes([0 for i in range(stride.size)])

    for stride in strides[5:]:
        stride.count = 1
        stride.idSizes.append((StrideType.BONE_WEIGHT, StrideSize.FLOAT))
        stride.stride = 4
        stride.stride = 0x7C
        stride.unknown = bytes([0 for i in range(stride.size)])

    return strides
