# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi

from blackHoleScripts.modCommon import modConfig
from blackHoleScripts.modServer import logger

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
        self.ListenEvent()

    def ListenEvent(self):
        self.DefineEvent(modConfig.CreateEffectEvent)
        self.ListenForEvent(Namespace, SystemName, modConfig.ServerItemTryUseEvent, self, self.OnServerItemTryUse)

    def UnListenEvent(self):
        self.UnListenForEvent(Namespace, SystemName, modConfig.ServerItemTryUseEvent, self, self.OnServerItemTryUse)

    # ServerItemTryUseEvent：玩家点击右键尝试使用物品时服务端抛出的事件
    # 监听的事件ServerItemTryUseEvent的回调函数
    def OnServerItemTryUse(self, args):
        logger.info("000000000000000000000000000")
        # logger.info("======================> args: %s" % args)
        playerId = args["playerId"]
        # itemDict = args['itemDict']
        # cancel = args['cancel']
        # print("1111111111111 ", playerId, itemDict, cancel)

        # 获取使用的物品的物品信息字典
        itemDict = args["itemDict"]
        print "itemDict =", itemDict
        print "itemName =", itemDict["itemName"]
        # 进行逻辑判断
        if itemDict["itemName"] == "black_hole:black_hole_create":
            logger.info("=== using black_hole_create === 1111111111111111111111")
            # 创建事件数据
            info = self.CreateEventData()
            info["playerId"] = playerId
            # 广播CreateEffectEvent事件通知客户端创建特效
            self.BroadcastToAllClient(modConfig.CreateEffectEvent, info)

    def Destroy(self):
        self.UnListenEvent()
