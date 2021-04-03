# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi

from blackHoleScripts.modCommon import modConfig
from blackHoleScripts.modServer import logger
from blackHoleScripts.modServer.api import block_api

ServerSystem = serverApi.GetServerSystemCls()
SystemName = serverApi.GetEngineSystemName()
Namespace = serverApi.GetEngineNamespace()

# 服务端系统
class BlackHoleServerSystem(ServerSystem):

    # 初始化
    def __init__(self, namespace, system_name):
        logger.info("========================== Init BlackHoleServerSystem ==================================")
        super(BlackHoleServerSystem, self).__init__(namespace, system_name)
        # ServerSystem.__init__(self, namespace, system_name)
        # TODO: 服务端系统功能
        # 监听原版方块点击
        self.PLACE_REALITY_WARY_MACHINE_BLOCK = [
            'minecraft:grass', 'minecraft:sand', 'minecraft:dirt', 'minecraft:bed:*'
        ]
        self.ListenEvent()

    def ListenEvent(self):
        self.DefineEvent(modConfig.CreateEffectEvent)
        self.ListenForEvent(Namespace, SystemName, modConfig.ServerBlockUseEvent, self, self.OnServerBlockUseEvent)

        # 增加对原版方块点击事件的监听
        for blockName in self.PLACE_REALITY_WARY_MACHINE_BLOCK:
            block_api.add_block_item_listen_for_use_event(blockName)

    def UnListenEvent(self):
        self.UnListenForEvent(Namespace, SystemName, modConfig.ServerBlockUseEvent, self, self.OnServerBlockUseEvent)

    def OnServerBlockUseEvent(self, args):
        """
        ServerBlockUseEvent 的回调函数
        触发时机：玩家右键点击新版自定义方块（或者通过接口AddBlockItemListenForUseEvent增加监听的MC原生游戏方块）时服务端抛出该事件（该事件tick执行，需要注意效率问题）。
        :param args: 玩家和方块相关信息
        :return: 无
        """
        logger.info("000000000000000000000000000")
        logger.info("======================> args: %s" % args)
        # 创建事件数据
        evenData = self.CreateEventData()
        evenData["playerId"] = args["playerId"]
        evenData['x'] = args["x"]
        evenData['y'] = args["y"]
        evenData['z'] = args["z"]
        # 广播CreateEffectEvent事件通知客户端创建特效
        self.BroadcastToAllClient(modConfig.CreateEffectEvent, evenData)

    def Destroy(self):
        self.UnListenEvent()
