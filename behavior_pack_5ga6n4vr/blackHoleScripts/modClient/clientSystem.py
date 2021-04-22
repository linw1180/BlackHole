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
        self.ListenEvent()
        # 存储序列帧特效实体ID
        self.frameEntityId = 0
        # 保存ui界面节点
        self.mDeleteButtonUiNode = None
        self.mCloseMsgUiNode = None

        # tick计数
        self.tickCount = 0

        # 黑洞对玩家的效果功能开关
        self.attract_switch = False
        # 初始化来自服务端的黑洞数据
        # 初始化黑洞吸收半径
        self.ar = 0
        # 初始化黑洞位置坐标
        self.x = 0
        self.y = 0
        self.z = 0

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
                            modConfig.OnScriptTickClient, self, self.OnScriptTickClient)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.SetSfxScaleEvent, self, self.OnSetSfxScale)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.ShowDeleteButtonEvent, self, self.OnShowDeleteButton)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.RemoveButtonUiEvent, self, self.OnRemoveButtonUi)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.PlayerAboutEvent, self, self.OnPlayerAbout)
        self.ListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CloseAttractSwitchEvent, self, self.OnCloseAttractSwitch)

    def UnListenEvent(self):
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                              modConfig.OnScriptTickClient, self, self.OnScriptTickClient)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CreateEffectEvent, self, self.OnCreateEffect)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.SetSfxScaleEvent, self, self.OnSetSfxScale)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.ShowDeleteButtonEvent, self, self.OnShowDeleteButton)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.RemoveButtonUiEvent, self, self.OnRemoveButtonUi)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.PlayerAboutEvent, self, self.OnPlayerAbout)
        self.UnListenForEvent(modConfig.ModName, modConfig.ModServerSystemName, modConfig.CloseAttractSwitchEvent, self, self.OnCloseAttractSwitch)

    def OnCloseAttractSwitch(self, args):
        """
        OnCloseAttractSwitch事件的回调函数，响应服务端，关闭黑洞对玩家的吸引开关
        """
        self.attract_switch = False

    def OnPlayerAbout(self, args):
        """
        接受来自服务端的数据：黑洞吸收半径 ar 和黑洞位置坐标 x, y, z, 并存入成员变量中（黑洞创建后才产生数据）
        """
        # 黑洞对玩家的效果功能开关
        self.attract_switch = True
        if args['ar']:
            self.ar = args['ar']
        if args['x']:
            self.x = args['x']
        if args['y']:
            self.y = args['y']
        if args['z']:
            self.z = args['z']

    def OnScriptTickClient(self):
        """
        服务器tick时触发,1秒有30个tick
        """
        self.tickCount += 1
        if self.attract_switch and self.tickCount % 2 == 0:
            self.AttractPlayer()

    def AttractPlayer(self):
        """
        黑洞对玩家的牵引和杀死功能实现
        """
        # 限制：只有在黑洞被创建并启动后，才对玩家有效果
        if self.ar and self.x and self.y and self.z:

            print '--------------------------- self.ar =', self.ar

            # -------------- 控制玩家进入黑洞吸收范围后，可被黑洞吸引，向黑洞中心位移 ------------
            # 玩家ID
            localPlayerId = clientApi.GetLocalPlayerId()
            # 玩家位置
            comp = clientApi.GetEngineCompFactory().CreatePos(localPlayerId)
            playerPos = comp.GetPos()
            playerPosX = playerPos[0]
            playerPosY = playerPos[1]
            playerPosZ = playerPos[2]

            # 获取黑洞吸收半径范围内玩家到黑洞中心的距离
            num = (self.x - playerPosX) ** 2 + (self.y - playerPosY) ** 2 + (self.z - playerPosZ) ** 2
            # 开平方，获取玩家到黑洞中心的距离
            distance = math.sqrt(num)

            # ---------------------- 黑洞吸收范围内，牵引玩家功能的实现 ------------------------------
            # 设置给玩家的移动向量大小
            pos_p = (float(self.x - playerPosX) / 200, float(self.y - playerPosY) / 200, float(self.z - playerPosZ) / 200)
            # 玩家进入黑洞吸收范围，则被黑洞吸引，被黑洞牵引
            if distance <= self.ar:
                motionComp = clientApi.GetEngineCompFactory().CreateActorMotion(localPlayerId)
                motionComp.SetMotion(pos_p)

            # ---------------------- 玩家进入黑洞半径，被黑洞杀死功能的实现 ------------------------------
            if distance <= self.ar / 3:
                data = self.CreateEventData()
                data['playerId'] = localPlayerId
                self.NotifyToServer(modConfig.KillPlayerEvent, data)

    def OnRemoveButtonUi(self, args):
        """
        当前若不是手持黑洞终止器，就不展现(删除)删除黑洞按钮UI界面和删除成功提示UI页面
        """
        if self.mDeleteButtonUiNode:
            self.mDeleteButtonUiNode.SetRemove()
        if self.mCloseMsgUiNode:
            self.mCloseMsgUiNode.SetRemove()

    def OnShowDeleteButton(self, args):
        """
        手持黑洞终止器时，显示删除按钮UI界面
        """
        # 注册删除按钮UI 详细解释参照《UI API》
        clientApi.RegisterUI(modConfig.ModName, modConfig.DeleteButtonUiName, modConfig.DeleteButtonUiPyClsPath,
                                    modConfig.DeleteButtonUiScreenDef)
        # 创建UI
        self.mDeleteButtonUiNode = clientApi.CreateUI(modConfig.ModName, modConfig.DeleteButtonUiName, {"isHud": 1})

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