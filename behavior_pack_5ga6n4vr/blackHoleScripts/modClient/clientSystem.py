# -*- coding: utf-8 -*-
import math

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
        # 存储序列帧特效实体ID
        self.frameEntityId = 0

    def ListenEvent(self):
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.SetSfxScaleEvent, self, self.OnSetSfxScale)

    def UnListenEvent(self):
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.SetSfxScaleEvent, self, self.OnSetSfxScale)

    def OnSetSfxScale(self, args):
        """
        设置序列帧特效大小
        """
        if self.frameEntityId != 0 and args['scale']:
            comp = clientApi.GetEngineCompFactory().CreateFrameAniTrans(self.frameEntityId)
            # 设置序列帧特效大小
            comp.SetScale((args['scale'], args['scale'], args['scale']))

    def OnCreateEffect(self, args):

        # 获取服务端传过来的玩家ID
        playerId = args["playerId"]
        # 调用客户端组件Api，获取玩家右手物品信息
        comp = clientApi.GetEngineCompFactory().CreateItem(playerId)
        carriedData = comp.GetCarriedItem()
        itemName = carriedData["itemName"]
        # 此处进行判断，若玩家使用的手持物品为黑洞制造器，则调用方法进行指定位置的黑洞特效创建
        if itemName == "black_hole:black_hole_create":
            self.createSfx(args)
        else:
            logger.info("=== only use black_hole_create can give you the sight ===")

    # 在指定点击位置创建粒子特效
    def createSfx(self, args):
        """
        在指定点击位置创建序列帧特效
        :param args: 玩家ID，方块命名空间和方块位置信息
        :return:
        """
        # 固定位置播放======================================================================

        # 获取传过来的dict中点击方块的位置信息
        x = args['x']
        y = args['y']
        z = args['z']

        # 获取位置pos（实体坐标） tuple(float, float, float)
        # 获取角度rot（俯仰角度以及绕竖直方向的角度） tuple(float, float)
        pos = (x + 0.5, y + 0.5, z + 0.5)
        rot = (90, 0, 0)  # 这里用的自定义的
        # 创建序列帧特效
        frameEntityId = self.CreateEngineSfxFromEditor("effects/black_hole.json")
        frameAniTransComp = compFactory.CreateFrameAniTrans(frameEntityId)
        frameAniTransComp.SetPos(pos)
        frameAniTransComp.SetRot(rot)
        frameAniTransComp.SetScale((3, 3, 3))
        frameAniControlComp = compFactory.CreateFrameAniControl(frameEntityId)
        # 播放特效
        frameAniControlComp.Play()

        # 将序列帧特效实体ID存储到全局变量中，供其他函数使用
        self.frameEntityId = frameEntityId

    # 删除序列帧特效实体方法
    def removeSfx(self, frameEntityId):
        self.DestroyEntity(frameEntityId)

    def Destroy(self):
        self.UnListenEvent()