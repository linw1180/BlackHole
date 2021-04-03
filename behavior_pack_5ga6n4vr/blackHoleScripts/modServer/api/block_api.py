# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi

level_id = serverApi.GetLevelId()

def add_block_item_listen_for_use_event(block_name):
    """
    增加blockName方块对ServerBlockUseEvent事件的脚本层监听

    1.19 调整 去掉增加原版方块监听ServerBlockUseEvent事件时同步到客户端的功能

    :param block_name: str 方块名称，格式：namespace:name:AuxValue，其中namespace:name:*匹配所有的方块数据值AuxValue
    :return: bool 是否增加成功
    """
    block_use_event_white_list_comp = serverApi.GetEngineCompFactory().CreateBlockUseEventWhiteList(level_id)
    return block_use_event_white_list_comp.AddBlockItemListenForUseEvent(block_name)