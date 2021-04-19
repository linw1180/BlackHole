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
        # 保存ui界面节点
        self.mDeleteButtonUiNode = None
        self.mCloseMsgUiNode = None

        # 初始化时进行设备检查，自动切换鼠标和触控
        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        # ret ==> 0：Window；1：IOS；2：Android；-1：其他
        ret = clientApi.GetPlatform()
        if ret == 0:
            # 参数：True:进入鼠标模式，False:退出鼠标模式
            # PC设备（使用鼠标）
            comp.SimulateTouchWithMouse(True)
        else:
            # 其他设备（使用触控）
            comp.SimulateTouchWithMouse(False)


    def ListenEvent(self):
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            modConfig.UiInitFinishedEvent, self, self.OnUIInitFinished)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.SetSfxScaleEvent, self, self.OnSetSfxScale)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.ShowDeleteButtonEvent, self, self.OnShowDeleteButton)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.RemoveButtonUiEvent, self, self.OnRemoveButtonUi)

    def UnListenEvent(self):
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                              modConfig.UiInitFinishedEvent, self, self.OnUIInitFinished)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.SetSfxScaleEvent, self, self.OnSetSfxScale)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.ShowDeleteButtonEvent, self, self.OnShowDeleteButton)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.RemoveButtonUiEvent, self, self.OnRemoveButtonUi)

    def ShowDeleteMsg(self):
        """
        删除所有黑洞后，给玩家信息提示，展示删除成功的页面
        """
        # 注册信息提示和关闭按钮的UI
        clientApi.RegisterUI(modConfig.ModName, modConfig.CloseMsgUiName, modConfig.CloseMsgUiPyClsPath,
                                    modConfig.CloseMsgUiScreenDef)
        # 创建UI
        self.mCloseMsgUiNode = clientApi.CreateUI(modConfig.ModName, modConfig.CloseMsgUiName, {"isHud": 1})

    def OnRemoveButtonUi(self, args):
        """
        当前若不是手持黑洞终止器，就不展现(删除)删除黑洞按钮UI界面
        """
        print'------------------------------------------------------------'
        if self.mDeleteButtonUiNode:
            self.mDeleteButtonUiNode.SetRemove()

    def OnShowDeleteButton(self, args):
        """
        手持黑洞终止器时，显示删除按钮UI界面
        """
        # 注册删除按钮UI 详细解释参照《UI API》
        flag = clientApi.RegisterUI(modConfig.ModName, modConfig.DeleteButtonUiName, modConfig.DeleteButtonUiPyClsPath,
                                    modConfig.DeleteButtonUiScreenDef)
        print ("=================flag==================", flag)
        # 创建UI
        self.mDeleteButtonUiNode = clientApi.CreateUI(modConfig.ModName, modConfig.DeleteButtonUiName, {"isHud": 1})
        print ("self.mDeleteButtonUiNode", self.mDeleteButtonUiNode)
        if self.mDeleteButtonUiNode:
            print ("=============if===========")

    # 初始化创建UI（在此处不需要，其他地方可套用里边注册UI方式）
    def OnUIInitFinished(self, args):
        print '-------------------------------------------------------------------------------- args =', args
        # # 注册UI 详细解释参照《UI API》
        # flag = clientApi.RegisterUI(modConfig.ModName, modConfig.BlackHoleUiName, modConfig.BlackHoleUiPyClsPath,
        #                      modConfig.BlackHoleUiScreenDef)
        # print ("=================flag==================", flag)
        # # 创建UI
        # self.mBlackHoleUiNode = clientApi.CreateUI(modConfig.ModName, modConfig.BlackHoleUiName, {"isHud": 1})
        # print ("self.mBlackHoleUiNode", self.mBlackHoleUiNode)
        # if self.mBlackHoleUiNode:
        #     print ("=============if===========")
            # self.mBlackHoleUiNode.Init()

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

        # 如果之前创建过黑洞，则先把之前的销毁，再进行新的创建
        if self.frameEntityId:
            self.removeSfx(self.frameEntityId)

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