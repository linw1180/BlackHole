# -*- coding: utf-8 -*-

import mod.server.extraServerApi as serverApi


def set_motion(entity_id, motion):
    """
    设置生物（不含玩家）的瞬时移动方向向量

    # rot 和 世界坐标系关系
    #			^ x -90°
    # 			|
    # 180°/-180  ----------> z 0°
    # 			| 90°

    1.18 新增 设置生物瞬时移动方向向量

    :param entity_id:
    :param motion: tuple(float,float,float) 世界坐标系下的向量，该方向为世界坐标系下的向量，以x,z,y三个轴的正方向为正值。
        可以通过当前生物的rot组件判断目前玩家面向的方向，可在开发模式下打开F3观察数值变化。
    :return: bool 设置是否成功
    """
    motion_comp = serverApi.GetEngineCompFactory().CreateActorMotion(entity_id)
    return motion_comp.SetMotion(motion)


def get_motion(entity_id):
    """
    获取生物（含玩家）的瞬时移动方向向量

    1.18 新增 获取生物的瞬时移动方向向量

    :param entity_id:
    :return: tuple(int,int,int) 瞬时移动方向向量，异常时返回None
    """
    motion_comp = serverApi.GetEngineCompFactory().CreateActorMotion(entity_id)
    return motion_comp.GetMotion()
