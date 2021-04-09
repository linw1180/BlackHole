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
        logger.info("000000000000000000000000000")
        logger.info("======================> args: %s" % args)
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

        # 测试（实现持续点击地面，所有生物朝点击的位置为中心，持续小位移至此）
        # entityDicts = serverApi.GetEngineActor()
        # for id in entityDicts:
        #     # 获取实体位置坐标
        #     comp = serverApi.GetEngineCompFactory().CreatePos(id)
        #     entityPos = comp.GetPos()
        #     entityPosX = entityPos[0]
        #     entityPosY = entityPos[1]
        #     entityPosZ = entityPos[2]
        #     set_motion(id, (float(args["x"] - entityPosX)/10, float(args["y"] - entityPosY)/10, float(args["z"] - entityPosZ)/10))

        # print '===============', get_motion(args['playerId'])

        # # 测试（遇到获取范围内entity列表失败的问题，暂未解决，换张哥给的Api试试）
        # print 'begin-----------------------------'
        # levelId = serverApi.GetLevelId()
        # comp = serverApi.GetEngineCompFactory().CreateGame(levelId)
        # entityIdList = comp.GetEntitiesAroundByType(args["playerId"], 100, 12)
        # print '------------------ levelId = ', levelId
        # print '------------------ args["playerId"] = ', args["playerId"]
        # print '------------------ entityIdList = ', entityIdList
        #
        # for entityId in entityIdList:
        #     print '--------------------- entityId = ', entityId
        #     # 获取实体位置坐标
        #     comp = serverApi.GetEngineCompFactory().CreatePos(entityId)
        #     entityPos = comp.GetPos()
        #     entityPosX = entityPos[0]
        #     entityPosY = entityPos[1]
        #     entityPosZ = entityPos[2]
        #     set_motion(id, (float(args["x"] - entityPosX)/10, float(args["y"] - entityPosY)/10, float(args["z"] - entityPosZ)/10))
        #     print '--------------------- (nx, ny, nz) = ', (float(args["x"] - entityPosX)/10, float(args["y"] - entityPosY)/10, float(args["z"] - entityPosZ)/10)
        #
        # print 'over-----------------------------'

        # 测试（比较理想的：实现持续点击方块，触发事件，将指定范围内生物以持续位移方式拉过来）
        # entity_ids = get_entity_api.get_pet_enemies_around(args["playerId"], 3)
        # print '------------------------------ entity_ids = ', entity_ids
        # for id in entity_ids:
        #     print '================= id = ', id
        #     # 获取实体位置坐标
        #     comp = serverApi.GetEngineCompFactory().CreatePos(id)
        #     entityPos = comp.GetPos()
        #     entityPosX = entityPos[0]
        #     entityPosY = entityPos[1]
        #     entityPosZ = entityPos[2]
        #     set_motion(id, (
        #     float(args["x"] - entityPosX) / 10, float(args["y"] - entityPosY) / 10, float(args["z"] - entityPosZ) / 10))

        # 控制是否调用============================================================= 2021年4月8日21:13:53 待修改
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
            if self.flag:
                self.biologyAttract(self.dict.get('playerId'), self.dict.get('x'), self.dict.get('y'), self.dict.get('z'))
                # print '-------------------------------------------------- biologyAttract'

    # 初步实现以玩家为中心，一定范围内的吸引功能
    def biologyAttract(self, player_id, x, y, z):
        entity_ids = get_entity_api.get_pet_enemies_around(player_id, 10)
        # print '------------------------------ entity_ids = ', entity_ids
        print '-----------------------------> attract_count : ', len(entity_ids)
        for id in entity_ids:
            # print '================= id = ', id
            # 获取实体位置坐标
            print("1111111111111111111")
            print(id)
            comp = serverApi.GetEngineCompFactory().CreatePos(id)
            entityPos = comp.GetPos()
            print(entityPos)
            entityPosX = entityPos[0]
            entityPosY = entityPos[1]
            entityPosZ = entityPos[2]
            set_motion(id, (float(x - entityPosX) / 50, float(y - entityPosY) / 50, float(z - entityPosZ) / 50))

        # 获取以玩家为中心，一定半径范围的所有生物ID（生物的具体杀死条件在下面通过生物离黑洞距离进行控制）
        entity_ids2 = get_entity_api.get_pet_enemies_around(player_id, 1000)
        # 下面代码实现功能：杀死进入黑洞范围内的生物
        for entityId in entity_ids2:
            # 获取实体位置坐标
            comp = serverApi.GetEngineCompFactory().CreatePos(entityId)
            entityPos = comp.GetPos()
            entity_pos_x = entityPos[0]
            entity_pos_y = entityPos[1]
            entity_pos_z = entityPos[2]
            # 获取黑洞半径范围内生物到黑洞中心的距离
            num = (x - entity_pos_x)**2 + (y - entity_pos_y)**2 + (z - entity_pos_z)**2
            distance = math.sqrt(num)
            # 杀死进入黑洞范围内的生物 2021年4月9日15:02:45======================== 下面计数有些问题，先存一版，后边试试羽哥推荐的以方块范围获取实体ID
            if distance <= 3:
                self.number += 1
                print '-------------------------------------------------> number = ', self.number
                levelId = serverApi.GetLevelId()
                comp = serverApi.GetEngineCompFactory().CreateGame(levelId)
                comp.KillEntity(entityId)
            if self.number == 20:
                print '=================================> attract 20, begin change     ', self.number
                self.number = 0
                print '---------------------------------> after change number    ', self.number

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
