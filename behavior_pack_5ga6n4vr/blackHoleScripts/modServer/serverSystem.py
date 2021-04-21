# -*- coding: utf-8 -*-
import math

import mod.server.extraServerApi as serverApi
from mod.common.utils.mcmath import Vector3

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
        self.ListenEvent()
        self.dict = {}
        self.count = 0
        self.flag = False
        # 用来计数销毁的实体
        self.kill_count = 0
        self.tick_count = 0
        # 黑洞默认初始半径 = 3
        self.radius = 3
        # 黑洞初始吸收速度参数（此并非速度，而是控制速度的相关参数；通过控制移动向量大小以达到控制吸收速度的效果）
        self.speed_param = 200
        # 吸收半径（注意: 最开始需要在此默认数值基础上再进行操作）
        # self.attract_radius = 18
        self.attract_radius = self.radius * 3

        # 存储坐标的list
        self.coordinate_list = []

        self.time_count = 0
        self.test = 10
        self.message_switch = False
        self.num_list = []
        self.temp_list = []

    def ListenEvent(self):
        # self.DefineEvent(modConfig.CreateEffectEvent)  此定义事件已过期，此处写不写都无作用
        self.ListenForEvent(Namespace, SystemName, modConfig.ServerItemUseOnEvent, self, self.OnServerItemUseOnEvent)
        self.ListenForEvent(Namespace, SystemName, modConfig.OnScriptTickServer, self, self.OnScriptTickServer)
        self.ListenForEvent(Namespace, SystemName, modConfig.OnCarriedNewItemChangedServerEvent, self,
                            self.OnCarriedNewItemChangedServer)
        self.ListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.RemoveAllAttractEvent,
                            self, self.OnRemoveAllAttract)
        self.ListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.KillPlayerEvent,
                            self, self.OnKillPlayer)

    def UnListenEvent(self):
        self.UnListenForEvent(Namespace, SystemName, modConfig.ServerItemUseOnEvent, self, self.OnServerItemUseOnEvent)
        self.UnListenForEvent(Namespace, SystemName, modConfig.OnScriptTickServer, self, self.OnScriptTickServer)
        self.UnListenForEvent(Namespace, SystemName, modConfig.OnCarriedNewItemChangedServerEvent, self,
                              self.OnCarriedNewItemChangedServer)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.RemoveAllAttractEvent,
                            self, self.OnRemoveAllAttract)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.KillPlayerEvent,
                              self, self.OnKillPlayer)

    def OnKillPlayer(self, args):
        """
        OnKillPlayerEvent的回调函数，回应客户端的请求，杀死进入黑洞半径的玩家
        """
        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        comp.KillEntity(args['playerId'])

    def OnRemoveAllAttract(self, args):
        """
        取消所有黑洞吸引效果
        """
        # 关闭使用tick开关控制的函数（主要是向量牵引实体和销毁方块并创建掉落物这两个函数）
        self.flag = False

    def OnCarriedNewItemChangedServer(self, args):
        """
        玩家切换主手物品时触发该事件
        """
        if args['newItemName'] == 'black_hole:black_hole_destroy':
            eventData = self.CreateEventData()
            eventData['newItemName'] = args['newItemName']
            # 广播事件到客户端，通知客户端展现删除按钮
            self.BroadcastToAllClient(modConfig.ShowDeleteButtonEvent, eventData)
        else:
            eventData = self.CreateEventData()
            eventData['newItemName'] = args['newItemName']
            # 广播事件到客户端，通知客户端删除UI（不是使用黑洞终止器的话不需要展现删除按钮界面）
            self.BroadcastToAllClient(modConfig.RemoveButtonUiEvent, eventData)

    def OnServerItemUseOnEvent(self, args):
        """
        ServerItemUseOnEvent 的回调函数
        玩家在对方块使用物品之前服务端抛出的事件。注：如果需要取消物品的使用需要同时在ClientItemUseOnEvent和ServerItemUseOnEvent中将ret设置为True才能正确取消。
        """
        # 获取玩家物品，支持获取背包，盔甲栏，副手以及主手物品
        comp = serverApi.GetEngineCompFactory().CreateItem(args['entityId'])
        item_dict = comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        # 如果玩家手持物品为黑洞制造器，则进行相关操作
        if item_dict['itemName'] == 'black_hole:black_hole_create':

            # 创建事件数据
            evenData = self.CreateEventData()
            evenData["playerId"] = args["entityId"]
            evenData['x'] = args["x"]
            evenData['y'] = args["y"]
            evenData['z'] = args["z"]
            evenData['blockName'] = args['blockName']
            # 将数据存入全局变量，供其他函数调用
            self.dict['playerId'] = args["entityId"]
            self.dict['x'] = args["x"]
            self.dict['y'] = args["y"]
            self.dict['z'] = args["z"]
            self.dict['blockName'] = args['blockName']

            # ---------------------------------- 初始化数据 --------------------------------
            # 恢复倒数时初始数据为10（避免二次创建黑洞，倒计时读数错误）
            self.test = 10
            # 重新关闭tick执行的函数
            self.flag = False
            # 将黑洞相关数据初始化
            self.count = 0
            # 用来计数销毁的实体
            self.kill_count = 0
            self.tick_count = 0
            # 黑洞默认初始半径 = 3
            self.radius = 3
            # 黑洞初始吸收速度参数（此并非速度，而是控制速度的相关参数；通过控制移动向量大小以达到控制吸收速度的效果）
            self.speed_param = 200
            # 吸收半径（注意: 最开始需要在此默认数值基础上再进行操作）
            # self.attract_radius = 18
            self.attract_radius = self.radius * 3

            # 存储坐标的list
            self.coordinate_list = []

            self.time_count = 0
            # ---------------------------------- 初始化数据 --------------------------------

            # 创建黑洞特效
            # 广播CreateEffectEvent事件通知客户端创建特效
            self.BroadcastToAllClient(modConfig.CreateEffectEvent, evenData)

            # 打开在tick中执行的函数开关，在聊天框显示倒计时，倒计时刷新速度1s一次，10s后执行功能并关闭消息提示
            self.message_switch = True

            # 延时10秒启动黑洞的相关功能
            comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
            comp.AddTimer(11.0, self.block_hole_ready, args)
            # comp.AddTimer(1.0, self.block_hole_ready, args)  # 测试用

    def block_hole_ready(self, args):

        # 关闭消息打印开关
        self.message_switch = False

        # 每次使用黑洞制造器创建黑洞前
        # 重新关闭使用tick开关控制的函数，防止重新创建新黑洞后，旧黑洞开启的tick开关控制的函数还在执行
        self.flag = False
        # 清空坐标数组，处理脏数据，便于后边新黑洞初始吸收范围内方块的销毁与掉落物的创建
        self.coordinate_list = []
        # 清空杀死的实体计数
        self.kill_count = 0

        # 调用函数，向数组中添加初始吸收半径为9的球形范围内所有方块坐标
        self.set_new_block_range(self.attract_radius, args["x"], args["y"], args["z"])

        # 打标记，作为控制开关，决定是否tick调用
        self.flag = True

    def show_message(self, entity_id, time):
        """
        左上角提示玩家黑洞启动倒计时信息
        """
        # 10s后执行功能，在聊天框显示倒计时，倒计时刷新速度1s一次
        comp = serverApi.GetEngineCompFactory().CreateMsg(entity_id)
        comp.NotifyOneMessage(entity_id, "注意，黑洞将在%ds后启动，请立即离开" % time, "§4")

    def set_new_block_range(self, ar, x, y, z):
        """
        获取指定吸收半径范围内所有坐标，添加到list末尾（获取的是球形范围内坐标）
        """
        for r in xrange(ar):
            for dx in xrange(-r, r + 1):
                for dy in xrange(-r, r + 1):
                    for dz in xrange(-r, r + 1):
                        if abs(dx) < r and abs(dy) != r and abs(dz) != r:
                            continue
                        if ar ** 2 < Vector3(dx, dy, dz).LengthSquared():
                            continue
                        # 每次往存储坐标的list末尾添加方块坐标，供后续销毁方块并创建掉落物使用
                        self.coordinate_list.append((x + dx, y + dy, z + dz))

        # 注意：此部分代码功能是更新给客户端最新的黑洞吸收半径（注意）
        # 广播事件，给客户端发送事件数据，使玩家也受黑洞效果影响
        eventData = self.CreateEventData()
        eventData['ar'] = ar
        eventData['x'] = x
        eventData['y'] = y
        eventData['z'] = z
        self.BroadcastToAllClient(modConfig.PlayerAboutEvent, eventData)

    # 效果不好
    def set_new_block_range_test(self, ar, x, y, z):

        # 获取正方形范围内，球形范围外的坐标，添加到坐标数组中
        ar = ar - 3  # 删除原先半径球和方形之间多余的坐标
        for nx in range(x - ar, x + ar):
            for ny in range(y - ar, y + ar):
                for nz in range(z - ar, z + ar):
                    if ((nx - x) ** 2 + (ny - y) ** 2 + (nz - z) ** 2) > ar ** 2:
                        # 获取坐标信息，存入全局list中
                        num = nx ** 2 + ny ** 2 + nz ** 2
                        self.num_list.append(num)
                        blockPos = (nx, ny, nz)
                        self.temp_list.append(blockPos)
                        # 每次往list末尾添加元素
                        # self.coordinate_list.append(blockPos)
        self.num_list.sort()
        for n in self.num_list:
            for m in self.temp_list:
                if m[0]**2 + m[1]**2 + m[2]**2 == n:
                    # print 'n ===========================', n
                    # print 'm --------------------------------------', m
                    self.coordinate_list.append(m)

        # 获取扩增后新加的球上的坐标，添加到坐标数组中
        ar = ar + 3  # 删除扩增半径的球坐标
        for r in xrange(ar - 3, ar):
            for dx in xrange(-r, r + 1):
                for dy in xrange(-r, r + 1):
                    for dz in xrange(-r, r + 1):
                        if abs(dx) < r and abs(dy) != r and abs(dz) != r:
                            continue
                        if ar ** 2 < Vector3(dx, dy, dz).LengthSquared():
                            continue
                        # 每次往存储坐标的list末尾添加方块坐标，供后续销毁方块并创建掉落物使用
                        self.coordinate_list.append((x + dx, y + dy, z + dz))
    # 效果不好
    def set_new_block_range_after(self, ar, x, y, z):
        """
        只获取扩增后范围内新增的方块坐标，并添加到坐标数组末尾（使用集合之间的补集来实现）
        """
        list_a = []
        list_b = []
        for r in xrange(ar):
            for dx in xrange(-r, r + 1):
                for dy in xrange(-r, r + 1):
                    for dz in xrange(-r, r + 1):
                        if abs(dx) < r and abs(dy) != r and abs(dz) != r:
                            continue
                        if ar ** 2 < Vector3(dx, dy, dz).LengthSquared():
                            continue
                        # 将扩增后范围内所有坐标存入list_a中
                        list_a.append((x + dx, y + dy, z + dz))

        for r in xrange(ar - 3):
            for dx in xrange(-r, r + 1):
                for dy in xrange(-r, r + 1):
                    for dz in xrange(-r, r + 1):
                        if abs(dx) < r and abs(dy) != r and abs(dz) != r:
                            continue
                        if (ar - 3) ** 2 < Vector3(dx, dy, dz).LengthSquared():
                            continue
                        # 将扩增后范围内所有坐标存入list_b中
                        list_b.append((x + dx, y + dy, z + dz))

        # 取补集，获取扩增后新增的坐标，加入到坐标数组末尾
        set_a = set(list_a)
        set_b = set(list_b)
        set_c = set_a.difference(set_b)
        list_c = list(set_c)
        for i in list_c:
            self.coordinate_list.append(i)

    # def set_new_block_range_after(self, r, x, y, z):
    #     """
    #     获取指定范围内所有坐标，存入list中，从正方形范围内筛选出球形范围坐标
    #     """
    #     # 注意：此半径r为吸收半径
    #     for nx in range(x - r, x + r + 1):
    #         for ny in range(y - r, y + r + 1):
    #             for nz in range(z - r, z + r + 1):
    #                 if ((nx - x) ** 2 + (ny - y) ** 2 + (nz - z) ** 2) <= r ** 2 and (
    #                         (nx - x) ** 2 + (ny - y) ** 2 + (nz - z) ** 2) >= (r - 3) ** 2:
    #                     # 获取坐标信息，存入全局list中
    #                     blockPos = (nx, ny, nz)
    #                     # 每次往list末尾添加元素
    #                     self.coordinate_list.append(blockPos)
    #
    #                     self.test += 1

    def clear_and_create_block(self, playerId, blockPos):
        """
        将指定位置方块替换为空气，在其位置创建/掉落原实体方块
        """
        # 此处playerId为block的设置者
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)
        # 获取操作前的指定位置的所有方块信息
        old_blockDict = comp.GetBlockNew(blockPos)
        # 不对空气方块进行操作
        if old_blockDict['name'] != 'minecraft:air':
            # === 将原方块销毁并替换为空气方块，掉落物为原方块 ===
            blockDict = {
                'name': 'minecraft:air'
            }
            comp.SetBlockNew(blockPos, blockDict, 1)

    # 服务器tick时触发,1秒有30个tick
    def OnScriptTickServer(self):

        self.count += 1
        # 每1/15秒触发一次（提示信息倒计时10秒，每秒刷新一次）
        if self.message_switch and self.count % 30 == 0:
            self.show_message(self.dict['playerId'], self.test)
            self.test -= 1

        # tick 调用
        # 黑洞初始特效创建完成后，调用自定义函数，实现以点击方块位置为范围中心，以点击方块为吸引中心，使用向量进行的所有实体牵引功能
        if self.flag and self.dict['playerId'] and self.dict['x'] and self.dict['y'] and self.dict['z']:
            self.biology_attract(self.dict.get('playerId', -1), self.dict.get('x', -1), self.dict.get('y', -1),
                                self.dict.get('z', -1))

        # tick中对数据分批处理：将指定位置方块替换为空气，在其位置创建/掉落原实体方块（每次tick执行一部分）
        if self.flag and self.coordinate_list and self.dict['playerId']:
            for i in range(5):
                if self.coordinate_list:
                    player_id = self.dict['playerId']
                    # 每次从list中按从左往右弹，并进行方块的销毁和掉落物的创建
                    blockPos = self.coordinate_list.pop(i)
                    # blockPos = self.coordinate_list.pop()
                    # 调用自定义函数，销毁方块并创建掉落物
                    self.clear_and_create_block(player_id, blockPos)

        print '----------------------------------------->> list ', len(self.coordinate_list)

    # 在tick函数中被调用，满足条件后tick执行，进行对范围内实体的向量牵引
    # 实现以点击方块处黑洞为中心，一定初始吸收半径范围内的吸引功能
    def biology_attract(self, player_id, x, y, z):

        # 使用服务端组件GetEntitiesInSquareArea获取指定范围内实体ID
        levelId = serverApi.GetLevelId()
        comp = serverApi.GetEngineCompFactory().CreateGame(levelId)

        # 正方形范围起始位置（正式用）
        startPos = ((x - self.attract_radius), (y - self.attract_radius), (z - (math.sqrt(2) * self.attract_radius)))
        # 正方形范围结束位置（正式用）
        endPos = ((x + self.attract_radius), (y + self.attract_radius), (z + (math.sqrt(2) * self.attract_radius)))

        # print '========= attract_radius =', self.attract_radius

        # 测试用吸收半径
        # r = 18
        # startPos = ((x - r / 2), (y - r / 2), (z - (math.sqrt(2) * r / 2)))
        # endPos = ((x + r / 2), (y + r / 2), (z + (math.sqrt(2) * r / 2)))

        # 获取到的指定正方形范围内所有entityId
        entity_ids = comp.GetEntitiesInSquareArea(None, startPos, endPos, 0)

        # print '-----------------------------> attract =', len(entity_ids)

        for entityId in entity_ids:

            # 对范围内实体进行区分，将生物实体和掉落物实体a区分开，分别进行向量位移计算
            type_comp = serverApi.GetEngineCompFactory().CreateEngineType(entityId)
            # 获取实体类型
            entityType = type_comp.GetEngineType()

            # 过滤
            if not entityType:
                continue

            # 获取实体位置坐标
            comp = serverApi.GetEngineCompFactory().CreatePos(entityId)
            entityPos = comp.GetPos()
            if entityPos:
                entityPosX = entityPos[0]
                entityPosY = entityPos[1]
                entityPosZ = entityPos[2]

                # 下面代码实现功能：将黑洞吸收半径范围内的实体吸引过来
                if entityType and entityType == 64:
                    # 掉落物实体的向量移动逻辑（最后需要写成可变化的）
                    # SetPos接口------------------------
                    comp.SetPos(((float(x - entityPosX) / 800 * 3) + entityPosX,
                                 (float(y - 3 - entityPosY) / 50 * 3) + entityPosY,
                                 (float(z - entityPosZ) / 800 * 3) + entityPosZ))
                    pos_z = (float(x - entityPosX) / 800 * 3, float(y - entityPosY) / 800 * 3, float(z - entityPosZ) / 800 * 3)
                    # set_motion接口------------------------
                    set_motion(entityId, pos_z)

                    # comp.SetPos(((float(x - entityPosX) / 200) + entityPosX,
                    #              (float(y - 2 - entityPosY) / 50) + entityPosY,
                    #              (float(z - entityPosZ) / 200) + entityPosZ))
                    # pos_z = (float(x - entityPosX) / 200, float(y - entityPosY) / 200, float(z - entityPosZ) / 200)
                    # set_motion(entityId, pos_z)
                else:
                    # 非掉落物实体的向量移动逻辑（最后需要写成可变化的）
                    # SetPos接口------------------------
                    # comp.SetPos(((float(x - entityPosX) / 200) + entityPosX,
                    #              (float(y - entityPosY) / 200) + entityPosY,
                    #              (float(z - entityPosZ) / 200) + entityPosZ))

                    # comp.SetPos(((float(x - entityPosX) / 500) + entityPosX,
                    #              (float(y - entityPosY) / 500) + entityPosY,
                    #              (float(z - entityPosZ) / 500) + entityPosZ))

                    # set_motion接口------------------------
                    # pos_z = (float(x - entityPosX) / 200, float(y - entityPosY) / 200, float(z - entityPosZ) / 200)
                    # set_motion(entityId, pos_z)
                    pos_z = (float(x - entityPosX) / 300, float(y - entityPosY) / 300, float(z - entityPosZ) / 300)
                    set_motion(entityId, pos_z)

                # 下面代码实现功能：杀死进入黑洞半径大小范围内的实体
                # 获取黑洞吸收半径范围内所有生物到黑洞中心的距离
                num = (x - entityPosX) ** 2 + (y - entityPosY) ** 2 + (z - entityPosZ) ** 2
                # 开平方，获取生物到黑洞中心的距离
                distance = math.sqrt(num)
                # 杀死进入黑洞半径范围内的实体
                if distance <= self.radius:
                    levelId = serverApi.GetLevelId()
                    comp = serverApi.GetEngineCompFactory().CreateGame(levelId)
                    # ret = comp.KillEntity(entityId)
                    ret = self.DestroyEntity(entityId)
                    if ret:
                        self.kill_count += 1
                        # print '---------------------------------------------------------------- kill =', self.kill_count
                        # --------------- 此处写黑洞效果随吸收的实体数的变化逻辑 ---------------
                        # if self.kill_count != 0 and self.kill_count % 200 == 0:
                        # 计算出吸收半径的圆和黑洞杀死半径的圆之间的体积的一半，作为黑洞扩增的吸收物品件数条件
                        # limit_count = (2 * math.pi * (self.attract_radius**3 - (self.radius - 3)**3)) / 3
                        # print '-----------------------> limit_count =', limit_count

                        if self.kill_count != 0 and self.kill_count % 300 == 0:
                            # 设置半径变化（每次扩增1格）
                            self.radius += 1
                            # --------begin----------  创建事件数据，广播自定义事件，通知客户端修改黑洞序列帧特效大小
                            eventData = self.CreateEventData()
                            eventData['scale'] = self.radius
                            self.BroadcastToAllClient(modConfig.SetSfxScaleEvent, eventData)
                            # --------over----------
                            # 设置吸收半径（每次扩大为原半径大小的三倍；注意：原半径每次扩增1格）
                            self.attract_radius = self.radius * 3
                            # 调用函数往存储位置坐标的list中添加新坐标，以便在tick中继续销毁方块创建掉落物
                            self.set_new_block_range(self.attract_radius, self.dict['x'], self.dict['y'],
                                                           self.dict['z'])
                            # 待加：此处还需设置吸收速度随半径大小的变化规则（“当前大小的三倍？”）

    def Destroy(self):
        self.UnListenEvent()
