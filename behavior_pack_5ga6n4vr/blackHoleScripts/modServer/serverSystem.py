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
            'minecraft:grass', 'minecraft:sand', 'minecraft:dirt', 'minecraft:bed:*', 'minecraft:stone',
            'minecraft:water', 'minecraft:flowing_water', 'minecraft:gravel', 'minecraft:oak_leaves',
            'minecraft:spruce_leaves', 'minecraft:birch_leaves', 'minecraft:jungle_leaves', 'minecraft:acacia_leaves'
        ]
        self.ListenEvent()
        self.dict = {}
        self.count = 0
        self.flag = False
        self.tick_number = 0
        self.tick_count = 0
        # 黑洞默认初始半径 = 3
        self.radius = 3
        # 黑洞初始吸收速度参数（此并非速度，而是控制速度的相关参数；通过控制移动向量大小以达到控制吸收速度的效果）
        self.speed_param = 200
        # 吸收半径（注意: 最开始需要在此默认数值基础上再进行操作）
        # self.attract_radius = 18
        self.attract_radius = self.radius * 3

        # 打标记用，控制设置吸收半径的开关（在tick中，设置一次就需要关闭）
        self.set_attract_radius_switch = True


    def ListenEvent(self):
        # self.DefineEvent(modConfig.CreateEffectEvent)  此定义事件已过期，此处写不写都无作用
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
        # print '----------------------------------------------1234567  (x, y, z) = ', (args['x'], args['y'], args['z'])

        # 获取玩家物品，支持获取背包，盔甲栏，副手以及主手物品------------------------------------------------------
        comp = serverApi.GetEngineCompFactory().CreateItem(args['playerId'])
        item_dict = comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        # 如果玩家手持物品为黑洞制造器，则进行相关操作
        if item_dict['itemName'] == 'black_hole:black_hole_create':

            # 打标记，作为控制开关，决定是否tick调用=============================================================
            self.flag = True

            self.dict['playerId'] = args["playerId"]
            self.dict['x'] = args["x"]
            self.dict['y'] = args["y"]
            self.dict['z'] = args["z"]
            self.dict['blockName'] = args['blockName']

            # 对指定半径范围内方块进行相关处理
            # 获取指定中心，指定范围内全部空间坐标（暂时获取的坐标范围为一个方形的）
            # 初始默认吸收半径（不用改）
            r = 9
            r = 9
            for nx in range(args["x"] - r, args["x"] + r + 1):
                for ny in range(args["y"] - r, args["y"] + r + 1):
                    for nz in range(args["z"] - r, args["z"] + r + 1):
                        # 将指定位置方块替换为空气，在其位置创建/掉落原实体方块
                        self.clear_and_create_block(args["playerId"], nx, ny, nz)

    # 先搁置
    def set_new_block_range(self, x, y, z, playerId):
        # 获取指定中心，指定范围内全部空间坐标（暂时获取的坐标范围为一个方形的）
        # ========================================
        # 准吸收半径（注意: 需要在此默认数值基础上再进行操作）
        # r = self.radius * 3
        # 每吸收20个，吸收半径扩大三倍（用新半径将原半径覆盖）
        # if self.tick_count % 20 == 0:
        #     r = r * 3
        # 拟吸收半径（测试用）
        r = 6
        for nx in range(x - r, x + r + 1):
            for ny in range(y - r, y + r + 1):
                for nz in range(z - r, z + r + 1):
                    # 将指定位置方块替换为空气，在其位置创建/掉落原实体方块
                    self.clear_and_create_block(playerId, nx, ny, nz)

    def clear_and_create_block(self, playerId, nx, ny, nz):
        """
        将指定位置方块替换为空气，在其位置创建/掉落原实体方块
        :param playerId:
        :param nx:
        :param ny:
        :param nz:
        :return:
        """
        blockPos = (nx, ny, nz)
        levelId = serverApi.GetLevelId()

        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)  # 此处playerId为block的设置者
        # 获取操作前的指定位置的方块信息
        old_blockDict = comp.GetBlockNew(blockPos)
        drop_blockName = old_blockDict['name']
        # print '-----------------old_blockDict = ', old_blockDict

        if old_blockDict['name'] == 'minecraft:air':
            pass
        else:
            # === 将原方块直接替换为空气方块 ===
            blockDict = {
                'name': 'minecraft:air'
            }
            comp.SetBlockNew(blockPos, blockDict, 0)

            # 在被替换为空气位置处，创建物品实体（即掉落物），返回物品实体的entityId
            itemDict = {
                'itemName': drop_blockName,
                'count': 1
            }
            itemEntityId = self.CreateEngineItemEntity(itemDict, 0, blockPos)

            # 设置实体的重力因子，当生物重力因子为0时则应用世界的重力因子（暂时实验出来没出现什么效果）
            # comp = serverApi.GetEngineCompFactory().CreateGravity(itemEntityId)
            # comp.SetGravity(0.08)
            # print 'test1+++++++++++++++++++++++++++++++++++++++++++++++++++  itemEntityId = ', itemEntityId

            # 获取实体重力因子
            # comp = serverApi.GetEngineCompFactory().CreateGravity(itemEntityId)
            # item_gravity = comp.GetGravity()
            # print '============================11111 item_gravity =', item_gravity

    # 服务器tick时触发,1秒有30个tick
    def OnScriptTickServer(self):
        self.count += 1
        # 每1/15秒触发一次
        if self.count % 2 == 0:
            # print '-------------------------------------------------- tick', self.count
            pass

        # tick 调用
        # 黑洞初始特效创建完成后，调用自定义函数，初步实现以玩家为范围中心，以点击方块为吸引位置中心，使用向量进行的生物牵引功能
        if self.flag and self.dict['playerId'] and self.dict['x'] and self.dict['y'] and self.dict['z']:
            self.biologyAttract(self.dict.get('playerId', -1), self.dict.get('x', -1), self.dict.get('y', -1),
                                self.dict.get('z', -1))

        # if self.tick_count % 20 == 0:
        #     self.set_block_range(self.dict.get('x'), self.dict.get('y'), self.dict.get('z'), self.dict.get('playerId'))

    # 实现以点击方块处黑洞为中心，一定黑洞初始半径范围内的吸引功能
    def biologyAttract(self, player_id, x, y, z):

        # 使用服务端组件GetEntitiesInSquareArea获取指定范围内实体ID
        levelId = serverApi.GetLevelId()
        comp = serverApi.GetEngineCompFactory().CreateGame(levelId)

        # 每吸收20个，黑洞半径扩大一格，吸收半径和吸收速度均扩大为原来半径大小的三倍---------------------------------------------
        if self.tick_count != 0 and self.tick_count % 200000000 == 0 and self.set_attract_radius_switch:
            self.radius += 1  # 设置半径大小（每次扩增1格）
            self.attract_radius = self.radius * 3  # 设置吸收半径（为原半径大小的三倍；注意：原半径每次扩大一格）
            # self.speed_param /= 3  # 设置吸收速度（为原半径大小的三倍；注意：原半径每次扩大一格） ----（可能有点问题，和原半径大小建立不起联系，暂时用的原速度3倍，吸收速度增长太快）-------------------
            # print '=======================================================================================> self.tick_number = ', self.tick_number
            # 因为在tick执行，所以需要进行控制：每当满足条件，都只设置一次（符合条件，每次设置完一次后，就关闭开关，即使后边tick中实体杀死数量仍符合设置条件，但由于开关关闭，无法再次进行设置）
            self.set_attract_radius_switch = False
        print '=======================================================================================> self.tick_count = ', self.tick_count
        print '=======================================================================================> self.attract_radius = ', self.attract_radius

        # # 正方形范围起始位置
        # startPos = ((x - self.attract_radius), (y - self.attract_radius), (z - (math.sqrt(2) * self.attract_radius)))
        # # 正方形范围结束位置
        # endPos = ((x + self.attract_radius), (y + self.attract_radius), (z + (math.sqrt(2) * self.attract_radius)))

        # 测试用吸收半径
        r = 100
        startPos = ((x - r/2), (y - r/2), (z - (math.sqrt(2) * r/2)))
        endPos = ((x + r/2), (y + r/2), (z + (math.sqrt(2) * r/2)))

        # 获取到的指定正方形范围内所有entityId
        entity_ids = comp.GetEntitiesInSquareArea(None, startPos, endPos, 0)
        # ---------------去除玩家ID，去除黑洞对玩家的效果-----------------
        if player_id in entity_ids:
            entity_ids.remove(player_id)

        print '-----------------------------> attract_count : ', len(entity_ids)

        for entityId in entity_ids:
            # print '================= id = ', id
            # 获取实体位置坐标
            comp = serverApi.GetEngineCompFactory().CreatePos(entityId)
            entityPos = comp.GetPos()
            if entityPos:
                entityPosX = entityPos[0]
                entityPosY = entityPos[1]
                entityPosZ = entityPos[2]

                # 下面代码实现功能：将黑洞吸收半径范围内的实体吸引过来
                # set_motion(entityId, (float(x - entityPosX) / 30, float(y - entityPosY) / 30, float(z - entityPosZ) / 30))
                # set_motion(entityId, (float(x - entityPosX) / 50, float(y - entityPosY) / 50, float(z - entityPosZ) / 50))
                # set_motion(entityId, (float(x - entityPosX)/100, float(y - entityPosY)/100, float(z - entityPosZ)/100))

                # 给指定范围内目标实体向黑洞方向的位移: 使用set_motion（tick形式）
                # set_motion(entityId, (float(x - entityPosX) / self.speed_param, float(y - entityPosY) / self.speed_param,
                #                 float(z - entityPosZ) / self.speed_param))

                # 测试------------（使用SetPos接口设置实体位置，类似于传送，需要每次传送小距离以达到匀速效果）
                # print '2222222222 (x,y,z) =', (entityPosX, entityPosY, entityPosZ)
                # print '3333333333 data =', (float(x - entityPosX) / 200, float(y - entityPosY) / 200, float(z - entityPosZ) / 200)
                success = comp.SetPos(((float(x - entityPosX) / 200) + entityPosX,
                             (float(y - entityPosY) / 200) + entityPosY,
                             (float(z - entityPosZ) / 200) + entityPosZ))
                # print '66666666666 success =', success
                #            (float(x - entityPosX) / self.speed_param,
                #             float(y - entityPosY) / self.speed_param,
                #             float(z - entityPosZ) / self.speed_param))

                # set_motion(entityId, (float(x - entityPosX)/200, float(y - entityPosY)/200, float(z - entityPosZ)/200))
                # set_motion(entityId, (float(x - entityPosX)/500, float(y - entityPosY)/500, float(z - entityPosZ)/500))

                # 下面代码实现功能：杀死进入黑洞半径大小范围内的生物
                # 获取黑洞吸收半径范围内所有生物到黑洞中心的距离
                num = (x - entityPosX) ** 2 + (y - entityPosY) ** 2 + (z - entityPosZ) ** 2
                # 开平方，获取生物到黑洞中心的距离
                distance = math.sqrt(num)
                # 杀死进入黑洞半径范围内的生物
                if distance <= self.radius:
                    levelId = serverApi.GetLevelId()
                    comp = serverApi.GetEngineCompFactory().CreateGame(levelId)
                    ret = comp.KillEntity(entityId)
                    if ret:
                        self.tick_number += 1
                        # print 'ret =', ret
                        # print self.tick_number
                        # print '99999999999999999999'
                        if self.tick_number == 32:
                            # 此处 tick_count 代表黑洞杀死的实体数量
                            self.tick_count += 1
                            # 每杀死一个实体时，将吸收半径的开关，开启一次（---非常重要，上边tick执行中设置吸收半径就靠它了，花了接近一个点想出来！---）
                            self.set_attract_radius_switch = True
                            # 符合条件后，将最终的tick计数归零
                            self.tick_number = 0
                            print '-----------------------------------------------------------------------------------------> kill number = ', self.tick_count

    def Destroy(self):
        self.UnListenEvent()
