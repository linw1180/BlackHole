# -*- coding: utf-8 -*-


# Mod Info
ModName = 'BlackHole'
ModVersion = '1.0.0'

# Server System
ModServerSystemName = 'BlackHoleServerSystem'
ModServerSystemPath = 'blackHoleScripts.modServer.serverSystem.BlackHoleServerSystem'

# Client System
ModClientSystemName = 'BlackHoleClientSystem'
ModClientSystemPath = 'blackHoleScripts.modClient.clientSystem.BlackHoleClientSystem'

# Client Event
# engine
UiInitFinishedEvent = "UiInitFinished"
OnScriptTickClient = 'OnScriptTickClient'
# custom
RemoveAllAttractEvent = 'RemoveAllAttractEvent'
KillPlayerEvent = 'KillPlayerEvent'
ShowDeleteSuccessMsgEvent = 'ShowDeleteSuccessMsgEvent'

# Server Event
# engine
OnScriptTickServer = 'OnScriptTickServer'
ServerItemUseOnEvent = 'ServerItemUseOnEvent'
OnCarriedNewItemChangedServerEvent = 'OnCarriedNewItemChangedServerEvent'
# custom
CreateEffectEvent = 'CreateEffectEvent'
SetSfxScaleEvent = 'SetSfxScaleEvent'
ShowDeleteButtonEvent = 'ShowDeleteButtonEvent'
RemoveButtonUiEvent = 'RemoveButtonUiEvent'
PlayerAboutEvent = 'PlayerAboutEvent'
CloseAttractSwitchEvent = 'CloseAttractSwitchEvent'

# UI
DeleteButtonUiName = "deleteButtonUi"
DeleteButtonUiPyClsPath = "blackHoleScripts.modClient.ui.deleteButtonUi.DeleteButtonUiScreen"
DeleteButtonUiScreenDef = "deleteButtonUi.main"

CloseMsgUiName = "closeMsgUi"
CloseMsgUiPyClsPath = "blackHoleScripts.modClient.ui.closeMsgUi.CloseMsgUiScreen"
CloseMsgUiScreenDef = "closeMsgUi.main"