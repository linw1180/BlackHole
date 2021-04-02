# -*- coding: utf-8 -*-

def get_new_pos(pos, rot, offset):
    """
    通过旋转值和相对坐标确定新位置
    :param tuple pos:
    :param tuple rot:
    :param tuple offset:
    :rtype: tuple
    :return:
    """
    # 转轴公式
    import math
    rad = math.radians(rot[1])
    sin = math.sin(rad)
    cos = math.cos(rad)
    dz = offset[0] * sin + offset[2] * cos
    dx = offset[0] * cos - offset[2] * sin
    return pos[0] + dx, pos[1] + offset[1], pos[2] + dz