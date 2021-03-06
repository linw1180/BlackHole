# -*- coding: utf-8 -*-

# 从客户端API中拿到我们需要的ViewBinder / ViewRequest / ScreenNode
import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi
from mod.common.minecraftEnum import TouchEvent

from blackHoleScripts.modClient.clientSystem import BlackHoleClientSystem
from blackHoleScripts.modCommon import modConfig

ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
# 获取组件工厂，用来创建组件
compFactory = clientApi.GetEngineCompFactory()

# 所有的UI类需要继承自引擎的ScreenNode类
class DeleteButtonUiScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        # 当前客户端的玩家Id
        self.mPlayerId = clientApi.GetLocalPlayerId()

        self.mDeleteButton = "/deleteButton"
        # self.mMsg = '/successMsgPanel/msg'
        # self.mCloseButton = '/successMsgPanel/closeButton'

    # Create函数是继承自ScreenNode，会在UI创建完成后被调用
    def Create(self):
        self.AddTouchEventHandler(self.mDeleteButton, self.OnDeleteButtonTouch, {"isSwallow": True})

    def Init(self):
        pass

    def OnDeleteButtonTouch(self, args):
        """
        点击删除按钮：实现删除黑洞特效、取消黑洞吸引效果，达到终止黑洞的效果
        """
        if args['TouchEvent'] == TouchEvent.TouchUp:

            # 获取客户端System（以便下边可以通过客户端系统调用系统中相关方法和变量）
            blackHoleClientSystem = clientApi.GetSystem(modConfig.ModName, modConfig.ModClientSystemName)

            # ----------------- 销毁黑洞特效 --------------------
            # 通过调用客户端系统方法，销毁黑洞序列帧特效
            blackHoleClientSystem.DestroyEntity(blackHoleClientSystem.frameEntityId)

            # ----------------- 取消黑洞吸引效果 --------------------
            # 给服务端广播事件，通知服务端去除黑洞吸引效果
            blackHoleClientSystem.NotifyToServer(modConfig.RemoveAllAttractEvent, args)

            # ----------------- 黑洞终止后，还需要将删除按钮UI去除 --------------------
            blackHoleClientSystem.mDeleteButtonUiNode.SetRemove()

            # 给服务端广播事件，通知服务端在左上角消息列表打印“黑洞已经全部清除”的消息
            blackHoleClientSystem.NotifyToServer(modConfig.ShowDeleteSuccessMsgEvent, args)

            # ----------------- 黑洞终止后，需要将黑洞数据初始化，消除黑洞对玩家的影响（初始化数据后，玩家就不符合牵引条件了） --------------------
            blackHoleClientSystem.ar = 0
            blackHoleClientSystem.x = 0
            blackHoleClientSystem.y = 0
            blackHoleClientSystem.z = 0