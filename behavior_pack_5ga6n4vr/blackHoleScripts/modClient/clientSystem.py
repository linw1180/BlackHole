# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi

from blackHoleScripts.modClient import logger
from blackHoleScripts.modClient.utils import apiUtil
from blackHoleScripts.modCommon import modConfig

ClientSystem = clientApi.GetClientSystemCls()
SystemName = clientApi.GetEngineSystemName()
Namespace = clientApi.GetEngineNamespace()
# 组件工厂，用来创建组件
compFactory = clientApi.GetEngineCompFactory()

# 客户端系统
class BlackHoleClientSystem(ClientSystem):

    # 初始化
    def __init__(self, namespace, system_name):
        logger.info("========================== Init BlackHoleClientSystem ==================================")
        super(BlackHoleClientSystem, self).__init__(namespace, system_name)  # 现用初始化父类方式
        # ClientSystem.__init__(self, namespace, system_name)  这种方式也可以初始化父类
        # TODO: 客户端系统功能
        self.ListenEvent()

    def ListenEvent(self):
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)

    def UnListenEvent(self):
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)

    def OnCreateEffect(self, args):
        logger.info("22222222222222222222 %s" % args)

        # 获取服务端传过来的玩家ID
        playerId = args["playerId"]
        # 调用客户端组件Api，获取玩家右手物品信息
        comp = clientApi.GetEngineCompFactory().CreateItem(playerId)
        carriedData = comp.GetCarriedItem()
        itemName = carriedData["itemName"]
        # 此处进行判断，若玩家使用的手持物品为黑洞制造器，则进行指定位置的黑洞特效创建
        if itemName == "black_hole:black_hole_create":
            self.createParticle(args)
        else:
            logger.info("=== only use black_hole_create can give you the sight ===")

    # 创建粒子特效
    def createParticle(self, args):
        logger.info("333333333333333333333333333 %s" % args)

        # 固定位置播放======================================================================
        # 获取传过来的dict中玩家ID和点击方块的位置信息
        entityId = args["playerId"]
        logger.info('-------------------------------------------- entityId = %s' % entityId)
        x = args['x']
        y = args['y']
        z = args['z']
        logger.info('-------------------------------------------- x = %d' % x)
        logger.info('-------------------------------------------- y = %d' % y)
        logger.info('-------------------------------------------- z = %d' % z)

        # 获取实体位置pos（实体坐标） tuple(float, float, float)
        pos_comp = clientApi.GetEngineCompFactory().CreatePos(entityId)
        pos = pos_comp.GetPos()
        # 获取实体角度rot（俯仰角度以及绕竖直方向的角度） tuple(float, float)
        rot_comp = clientApi.GetEngineCompFactory().CreateRot(entityId)
        rot = rot_comp.GetRot()

        # 先用转轴公式算出新位置坐标，再从配置文件读取特效
        # offset = (0, -0.5, 4)  # 这里用的自定义的
        # pos = apiUtil.get_new_pos(pos, rot, offset)
        pos = (x + 0.5, y + 0.5, z + 0.5)
        rot = (90, 0, 0)  # 这里用的自定义的
        particleEntityId = self.CreateEngineParticle("effects/black_hole.json", pos)
        particle_comp = clientApi.GetEngineCompFactory().CreateParticleTrans(particleEntityId)
        particle_comp.SetRot(rot)


        # 可绑定entity（但此处不适用）
        # entityId = args["playerId"]
        # comp = clientApi.GetEngineCompFactory().CreateParticleEntityBind(particleEntityId)
        # comp.Bind(entityId, (0, 1, 0), (0, 0, 0))

        # 播放特效
        logger.info("------------------------------> particleEntityId = %s" % particleEntityId)
        particleControlComp = clientApi.GetEngineCompFactory().CreateParticleControl(particleEntityId)
        logger.info("------------------------------> particleControlComp = %s" % particleControlComp)
        particleControlComp.Play()
        logger.info("44444444444444444444444444444")

    # 删除特效实体方法
    def removeParticle(self, particleEntityId):
        self.DestroyEntity(particleEntityId)

    def Destroy(self):
        self.UnListenEvent()