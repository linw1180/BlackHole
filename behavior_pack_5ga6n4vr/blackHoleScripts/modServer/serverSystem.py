# -*- coding: utf-8 -*-
import math

import mod.server.extraServerApi as serverApi

from blackHoleScripts.modCommon import modConfig
from blackHoleScripts.modServer import logger
from blackHoleScripts.modServer.api import block_api, set_motion, get_motion, get_entity_api

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
        # 监听原版方块点击（后续可继续添加）
        self.PLACE_REALITY_WARY_MACHINE_BLOCK = [
            'minecraft:grass', 'minecraft:sand', 'minecraft:dirt', 'minecraft:bed:*'
        ]
        self.ListenEvent()
        self.dict = {}
        self.count = 0
        self.flag = False
        self.number = 0

    def ListenEvent(self):
        self.DefineEvent(modConfig.CreateEffectEvent)
        self.ListenForEvent(Namespace, SystemName, modConfig.ServerBlockUseEvent, self, self.OnServerBlockUseEvent)
        self.ListenForEvent(Namespace, SystemName, modConfig.OnScriptTickServer, self, self.OnScriptTickServer)

        # 增加对原版方块点击事件的监听
        for blockName in self.PLACE_REALITY_WARY_MACHINE_BLOCK:
            block_api.add_block_item_listen_for_use_event(blockName)

    def UnListenEvent(self):
        self.UnListenForEvent(Namespace, SystemName, modConfig.ServerBlockUseEvent, self, self.OnServerBlockUseEvent)
        self.UnListenForEvent(Namespace, SystemName, modConfig.OnScriptTickServer, self, self.OnScriptTickServer)

    def OnServerBlockUseEvent(self, args):
        """
        ServerBlockUseEvent 的回调函数
        触发时机：玩家右键点击新版自定义方块（或者通过接口AddBlockItemListenForUseEvent增加监听的MC原生游戏方块）时服务端抛出该事件（该事件tick执行，需要注意效率问题）。
        :param args: 玩家和方块相关信息（可获取玩家ID，方块命名空间和方块坐标等信息）
        :return: 无
        """
        # 创建事件数据
        evenData = self.CreateEventData()
        evenData["playerId"] = args["playerId"]
        evenData['x'] = args["x"]
        evenData['y'] = args["y"]
        evenData['z'] = args["z"]
        evenData['blockName'] = args['blockName']
        # 广播CreateEffectEvent事件通知客户端创建特效
        self.BroadcastToAllClient(modConfig.CreateEffectEvent, evenData)

        # 测试
        # self.blockStart(evenData)

        # 控制是否调用=============================================================
        self.flag = True
        self.dict['playerId'] = args["playerId"]
        self.dict['x'] = args["x"]
        self.dict['y'] = args["y"]
        self.dict['z'] = args["z"]

    # 服务器tick时触发,1秒有30个tick
    def OnScriptTickServer(self):
        self.count += 1
        # 每1/15秒触发一次
        if self.count % 2 == 0:
            # print '-------------------------------------------------- tick', self.count
            # 黑洞初始特效创建完成后，调用自定义函数，初步实现以玩家为范围中心，以点击方块为吸引位置中心，使用向量进行的生物牵引功能
            if self.flag and self.dict['playerId'] and self.dict['x'] and self.dict['y'] and self.dict['z']:
                self.biologyAttract(self.dict.get('playerId', -1), self.dict.get('x', -1), self.dict.get('y', -1), self.dict.get('z', -1))
                # print '-------------------------------------------------- biologyAttract'

    # 实现以点击方块处黑洞为中心，一定黑洞初始半径范围内的吸引功能
    def biologyAttract(self, player_id, x, y, z):

        # 使用服务端组件GetEntitiesInSquareArea获取指定范围内实体ID
        levelId = serverApi.GetLevelId()
        comp = serverApi.GetEngineCompFactory().CreateGame(levelId)
        # 吸收半径
        r = 1000
        # 正方形范围起始位置
        startPos = ((x - r/2), (y - r/2), (z - (math.sqrt(2) * r)/2))
        # 正方形范围结束位置
        endPos = ((x + r/2), (y + r/2), (z + (math.sqrt(2) * r)/2))
        # 获取到的指定正方形范围内所有entityId
        entity_ids = comp.GetEntitiesInSquareArea(None, startPos, endPos, 0)
        # ---------------去除玩家ID，去除黑洞对玩家的效果-----------------
        if player_id in entity_ids:
            entity_ids.remove(player_id)
        # 下面代码实现功能：将黑洞吸收半径范围内的实体吸引过来
        print '-----------------------------> attract_count : ', len(entity_ids)

        for id in entity_ids:
            # print '================= id = ', id
            # 获取实体位置坐标
            comp = serverApi.GetEngineCompFactory().CreatePos(id)
            entityPos = comp.GetPos()
            entityPosX = entityPos[0]
            entityPosY = entityPos[1]
            entityPosZ = entityPos[2]
            set_motion(id, (float(x - entityPosX) / 50, float(y - entityPosY) / 50, float(z - entityPosZ) / 50))

        # 下面代码实现功能：杀死进入黑洞半径大小范围内的生物
        for entityId in entity_ids:
            # 获取实体位置坐标
            comp = serverApi.GetEngineCompFactory().CreatePos(entityId)
            entityPos = comp.GetPos()
            entity_pos_x = entityPos[0]
            entity_pos_y = entityPos[1]
            entity_pos_z = entityPos[2]
            # 获取黑洞吸收半径范围内所有生物到黑洞中心的距离
            num = (x - entity_pos_x)**2 + (y - entity_pos_y)**2 + (z - entity_pos_z)**2
            # 开平方，获取生物到黑洞中心的距离
            distance = math.sqrt(num)
            # 杀死进入黑洞范围内的生物
            if distance <= 3:
                levelId = serverApi.GetLevelId()
                comp = serverApi.GetEngineCompFactory().CreateGame(levelId)
                ret = comp.KillEntity(entityId)
                if ret:
                    self.number += 1
                    print '-------------------------------------------------> kill numbers = ', self.number
            # if self.number == 20:
            #     print '=================================> attract 20, begin change     ', self.number
            #     self.number = 0
            #     print '---------------------------------> after change number    ', self.number

    # 方块物品先搁置，先实现生物这块
    def blockStart(self, args):
        """
        先将指定方块销毁，然后在原地设置掉落物为原方块
        """
        playerId = args['playerId']
        blockPos = (args['x'], args['y'], args['z'])
        levelId = serverApi.GetLevelId()
        blockName = args['blockName']
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)  # 此处playerId为block的设置者

        # === 将原方块销毁，并且将掉落物设置为原方块 ===
        blockDict = {
            'name': blockName
        }
        comp.SetBlockNew(blockPos, blockDict, 1)

    def Destroy(self):
        self.UnListenEvent()
