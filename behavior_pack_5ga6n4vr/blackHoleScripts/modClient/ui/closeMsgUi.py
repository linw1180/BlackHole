# -*- coding: utf-8 -*-

# 从客户端API中拿到我们需要的ViewBinder / ViewRequest / ScreenNode
import mod.client.extraClientApi as clientApi

from blackHoleScripts.modCommon import modConfig

ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
# 获取组件工厂，用来创建组件
compFactory = clientApi.GetEngineCompFactory()


# 所有的UI类需要继承自引擎的ScreenNode类
class CloseMsgUiScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        # 当前客户端的玩家Id
        self.mPlayerId = clientApi.GetLocalPlayerId()

        self.mMsg = '/closeMsgPanel/msg'
        self.mCloseButton = '/closeMsgPanel/closeButton'

    # Create函数是继承自ScreenNode，会在UI创建完成后被调用
    def Create(self):
        print ("=============Create============")
        self.AddTouchEventHandler(self.mCloseButton, self.OnCloseButtonTouch, {"isSwallow": True})

    def Init(self):
        print ("=================Init test====================")
        pass

    def OnCloseButtonTouch(self, args):
        print '88888888888888888888888 args =', args

        # 获取客户端System（以便下边可以通过客户端系统调用系统中相关方法和变量）
        blackHoleClientSystem = clientApi.GetSystem(modConfig.ModName, modConfig.ModClientSystemName)

        # ----------------- 信息提示完，玩家点击关闭按钮，可将此提示页面关闭 --------------------
        blackHoleClientSystem.mCloseMsgUiNode.SetRemove()
        print '55555555555 ----'
