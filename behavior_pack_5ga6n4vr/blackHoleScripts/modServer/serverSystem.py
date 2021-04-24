# -*- coding: utf-8 -*-
import math

import mod.server.extraServerApi as serverApi
from mod.common.utils.mcmath import Vector3

from blackHoleScripts.modCommon import modConfig
from blackHoleScripts.modServer import logger
from blackHoleScripts.modServer.api import set_motion

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

		# 存储待删除的坐标的list（其实用pop_list命名更准确，但用的地方太多，现在改过来容易出错，暂时就这样命名了）
		# 此list不断在发生数据变化，list头部不断pop，尾部不断append
		self.coordinate_list = []
		self.pos_set = set()

		self.time_count = 0
		self.test = 10
		self.message_switch = False
		self.last_message_switch = False
		self.num_list = []
		self.temp_list = []

		# 初始扩增倍数（每扩增一次，加1）
		self.change_count = 1

		# 黑洞吸收范围内的所有实体ID（后边作为限制条件使用）
		# 初始化
		self.entity_ids = []

		# 初始化定时器对象
		self.func_timer = None
		self.msg_timer = None

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
		self.ListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.ShowDeleteSuccessMsgEvent,
							self, self.OnShowDeleteSuccessMsg)

	def UnListenEvent(self):
		self.UnListenForEvent(Namespace, SystemName, modConfig.ServerItemUseOnEvent, self, self.OnServerItemUseOnEvent)
		self.UnListenForEvent(Namespace, SystemName, modConfig.OnScriptTickServer, self, self.OnScriptTickServer)
		self.UnListenForEvent(Namespace, SystemName, modConfig.OnCarriedNewItemChangedServerEvent, self,
							  self.OnCarriedNewItemChangedServer)
		self.UnListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.RemoveAllAttractEvent,
							  self, self.OnRemoveAllAttract)
		self.UnListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.KillPlayerEvent,
							  self, self.OnShowDeleteSuccessMsg)
		self.UnListenForEvent(modConfig.ModName, modConfig.ModClientSystemName, modConfig.ShowDeleteSuccessMsgEvent,
							  self, self.OnKillPlayer)

	def OnShowDeleteSuccessMsg(self, args):
		"""
		OnShowDeleteSuccessMsgEvent事件的回调函数，响应删除按钮的请求，在左上角打印输出“黑洞已经全部清除”的消息
		"""
		comp = serverApi.GetEngineCompFactory().CreateMsg(self.dict['playerId'])
		comp.NotifyOneMessage(self.dict['playerId'], "黑洞已经全部清除！", "§4")

		# 取消两个定时器
		if self.msg_timer and self.func_timer:
			comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
			comp.CancelTimer(self.func_timer)
			comp.CancelTimer(self.msg_timer)
		self.message_switch = False
		self.last_message_switch = False

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
		# 清空坐标数组
		self.coordinate_list = []

	def OnCarriedNewItemChangedServer(self, args):
		"""
		玩家切换主手物品时触发该事件
		"""
		if args['newItemName'] == 'black_hole:black_hole_destroy':
			eventData = self.CreateEventData()
			eventData['newItemName'] = args['newItemName']
			# 广播事件到客户端，通知客户端展现删除按钮
			self.NotifyToClient(args['playerId'], modConfig.ShowDeleteButtonEvent, eventData)
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

			# 取消两个定时器
			if self.msg_timer and self.func_timer:
				comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
				comp.CancelTimer(self.func_timer)
				comp.CancelTimer(self.msg_timer)
			self.message_switch = False
			self.last_message_switch = False

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

			# 存储待删除的坐标的list
			self.coordinate_list = []

			self.time_count = 0
			# 初始化扩增倍数
			self.change_count = 1

			# ---------------------------------- 初始化数据 --------------------------------

			# 延时启动黑洞之前，通知客户端关闭吸引开关
			# 防止之前创建过一次黑洞，再次创建黑洞并延时启动时，玩家会被之前黑洞继续吸引并杀死
			# 广播事件，通知客户端关闭吸引开关
			data = self.CreateEventData()
			data['ar'] = self.attract_radius  # 随便传的事件数据
			self.BroadcastToAllClient(modConfig.CloseAttractSwitchEvent, data)

			# 创建黑洞特效
			# 广播CreateEffectEvent事件通知客户端创建特效
			self.BroadcastToAllClient(modConfig.CreateEffectEvent, evenData)

			# 打开在tick中执行的函数开关，在聊天框显示倒计时，倒计时刷新速度1s一次，10s后执行功能并关闭消息提示
			self.message_switch = True
			self.last_message_switch = True

			# 延时10秒启动黑洞的相关功能
			comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
			self.func_timer = comp.AddTimer(11.0, self.block_hole_ready, args)
			# comp.AddTimer(1.0, self.block_hole_ready, args)  # 测试用
			# 延时到倒计时10秒结束后，打印黑洞正在吸收物品的提示信息
			self.msg_timer = comp.AddTimer(12.0, self.last_message_func)

	def block_hole_ready(self, args):

		# 关闭消息打印开关
		self.message_switch = False

		# 每次使用黑洞制造器创建黑洞前
		# 重新关闭使用tick开关控制的函数，防止重新创建新黑洞后，旧黑洞开启的tick开关控制的函数还在执行
		self.flag = False
		# 清空待删除的坐标数组，处理脏数据，便于后边新黑洞初始吸收范围内方块的销毁与掉落物的创建
		self.coordinate_list = []
		# 清空杀死的实体计数
		self.kill_count = 0

		# 调用函数，向数组中添加初始吸收半径为9的球形范围内所有方块坐标
		self.set_new_block_range(self.attract_radius, args["x"], args["y"], args["z"])

		# 打标记，作为控制开关，决定是否tick调用
		self.flag = True

		self.new = 0

	def last_message_func(self):
		# 关闭最后一条消息打印开关
		self.message_switch = False

	def show_message(self, entity_id, time):
		"""
		左上角提示玩家黑洞启动倒计时信息
		"""
		if time:
			# 10s后执行功能，在聊天框显示倒计时，倒计时刷新速度1s一次
			comp = serverApi.GetEngineCompFactory().CreateMsg(entity_id)
			comp.NotifyOneMessage(entity_id, "注意，黑洞将在%ds后启动，请立即离开" % time, "§4")

	def show_last_message(self, entity_id):
		"""
		最后1秒倒计时后，展示 “黑洞正在吸收周围物品。。。” 信息
		"""
		comp = serverApi.GetEngineCompFactory().CreateMsg(entity_id)
		comp.NotifyOneMessage(entity_id, "黑洞正在吸收周围物品...", "§4")

	def set_new_block_range(self, ar, x, y, z):
		"""
		获取指定吸收半径范围内所有坐标，添加到list末尾（获取的是球形范围内坐标）
		"""
		pos_list = []
		for r in xrange(ar):
			for dx in xrange(-r, r + 1):
				for dy in xrange(-r, r + 1):
					for dz in xrange(-r, r + 1):
						if abs(dx) < r and abs(dy) != r and abs(dz) != r:
							continue
						if ar ** 2 < Vector3(dx, dy, dz).LengthSquared():
							continue
						# 将初始吸收半径范围坐标存入初始化坐标的list中
						pos_list.append((x + dx, y + dy, z + dz))

		self.pos_set = set(pos_list)

		# 将初始吸收半径范围内的坐标添加到待删除的list中
		self.coordinate_list.extend(pos_list)

		# 注意：此部分代码功能是更新给客户端最新的黑洞吸收半径（注意）
		# 广播事件，给客户端发送事件数据，使玩家也受黑洞效果影响
		self.BroadcastToAllClient(modConfig.PlayerAboutEvent, {'ar': ar, 'x': x, 'y': y, 'z': z})

	# 最新优化
	def set_new_block_range_add(self, ar, x, y, z):
		"""
		获取指定吸收半径范围内所有坐标，添加到list末尾（获取的是球形范围内坐标）
		"""
		# 存储扩增后新的吸收半径范围内所有坐标
		# new_pos_list = []
		add_list = self.count_block_pos(ar, x, y, z)

		# 将扩增后所有新增的坐标添加到待删list中
		self.coordinate_list.extend(add_list)
		self.pos_set.update(add_list)

		# 注意：此部分代码功能是更新给客户端最新的黑洞吸收半径（注意）
		# 广播事件，给客户端发送事件数据，使玩家也受黑洞效果影响
		self.BroadcastToAllClient(modConfig.PlayerAboutEvent, {'ar': ar, 'x': x, 'y': y, 'z': z})

	def count_block_pos(self, ar, x, y, z):
		add_list = []
		for r in xrange(int(self.attract_radius / math.sqrt(3)), ar):
			for dx in xrange(-r, r + 1):
				for dy in xrange(-r, r + 1):
					for dz in xrange(-r, r + 1):
						block_pos = (x + dx, y + dy, z + dz)
						if self.check_block_pos(block_pos, ar, r, dx, dy, dz):
							add_list.append(block_pos)
		return add_list

	def check_block_pos(self, block_pos, ar, r, dx, dy, dz):
		if self._check_pos_exists(block_pos):
			return False
		if self._check_lenght(r, dx, dy, dz):
			return False
		if self._check_squared_length(ar, dx, dy, dz):
			return False

		return True

	def _check_pos_exists(self, block_pos):
		"""
		关键优化点：（之前是因为坐标在list中筛选耗费时间太多，所以导致卡顿）
		1.将需要筛选的block_pos范围减小
		2.更换存储坐标容器的数据结构：将筛选目标由数组list换为链表set（数组查找快，链表插入和删除快）
		"""
		return block_pos in self.pos_set

	def _check_lenght(self, r, dx, dy, dz):
		if abs(dx) < r and abs(dy) != r and abs(dz) != r:
			return True

	def _check_squared_length(self, ar, dx, dy, dz):
		return ar ** 2 < Vector3(dx, dy, dz).LengthSquared()

	# 完美（求两个集合的补集，就是现在需要解决同一界面，每次扩增导致卡顿的问题）
	def set_new_block_range_last(self, ar, x, y, z):
		"""
		获取新增的环形球范围内所有坐标，添加到list末尾（圆心相同，大半径球比小半径球多出的那部分坐标）
		"""
		a_list = []
		for r in xrange(ar):
			for dx in xrange(-r, r + 1):
				for dy in xrange(-r, r + 1):
					for dz in xrange(-r, r + 1):
						if abs(dx) < r and abs(dy) != r and abs(dz) != r:
							continue
						if ar ** 2 < Vector3(dx, dy, dz).LengthSquared():
							continue
						# 每次往存储坐标的list末尾添加方块坐标，供后续销毁方块并创建掉落物使用
						a_list.append((x + dx, y + dy, z + dz))

		b_list = []
		for r in xrange(ar - 3):
			for dx in xrange(-r, r + 1):
				for dy in xrange(-r, r + 1):
					for dz in xrange(-r, r + 1):
						if abs(dx) < r and abs(dy) != r and abs(dz) != r:
							continue
						if (ar - 3) ** 2 < Vector3(dx, dy, dz).LengthSquared():
							continue
						# 每次往存储坐标的list末尾添加方块坐标，供后续销毁方块并创建掉落物使用
						b_list.append((x + dx, y + dy, z + dz))

		c_list = [i for i in a_list if i not in b_list]
		# for pos in c_list:
		#     self.coordinate_list.append(pos)
		self.coordinate_list.extend(c_list)

		# 注意：此部分代码功能是更新给客户端最新的黑洞吸收半径（注意）
		# 广播事件，给客户端发送事件数据，使玩家也受黑洞效果影响
		eventData = self.CreateEventData()
		eventData['ar'] = ar
		eventData['x'] = x
		eventData['y'] = y
		eventData['z'] = z
		self.BroadcastToAllClient(modConfig.PlayerAboutEvent, eventData)

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
			# 方式一：使用此方式可能会直接破坏掉一些方块，导致实际生成的掉落物比真正的少
			blockDict = {
				'name': 'minecraft:air'
			}
			comp.SetBlockNew(blockPos, blockDict, 1)

			# 方式二：使用此方式，则会将掉落物一个不少的全部创建出来
			# === 将原方块销毁并替换为空气方块 ===
			# blockDict = {
			#     'name': 'minecraft:air'
			# }
			# comp.SetBlockNew(blockPos, blockDict, 0)
			# # === 在原方块销毁位置生成原方块掉落物 ===
			# itemDict = {
			#     'itemName': old_blockDict['name'],
			#     'count': 1
			# }
			# self.CreateEngineItemEntity(itemDict, 0, blockPos)

	# 服务器tick时触发,1秒有30个tick
	def OnScriptTickServer(self):

		self.count += 1
		# 每1/15秒触发一次（提示信息倒计时10秒，每秒刷新一次）
		if self.message_switch and self.count % 30 == 0:
			self.show_message(self.dict['playerId'], self.test)
			self.test -= 1

		if self.last_message_switch and self.count == 330:
			self.show_last_message(self.dict['playerId'])

		# tick 调用
		# 黑洞初始特效创建完成后，调用自定义函数，实现以点击方块位置为范围中心，以点击方块为吸引中心，使用向量进行的所有实体牵引功能
		if self.flag and self.dict['playerId'] and self.dict['x'] and self.dict['y'] and self.dict['z']:
			self.biology_attract(self.dict.get('playerId', -1), self.dict.get('x', -1), self.dict.get('y', -1),
								 self.dict.get('z', -1))

		# tick中对数据分批处理：将指定位置方块替换为空气，在其位置创建/掉落原实体方块（每次tick执行一部分）
		if self.flag and self.coordinate_list and self.dict['playerId'] and self.count % 2:
			# 将黑洞吸收范围内的实体ID数量控制在200以内（防止画面内一次出现太多掉落物，导致卡顿！）
			if len(self.entity_ids) <= 150:
				for i in range(5):
					if self.coordinate_list and len(self.coordinate_list) >= 5:
						player_id = self.dict['playerId']
						# 每次从list中按从左往右弹，并进行方块的销毁和掉落物的创建
						blockPos = self.coordinate_list.pop(i)
						# blockPos = self.coordinate_list.pop()
						# 调用自定义函数，销毁方块并创建掉落物
						self.clear_and_create_block(player_id, blockPos)

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

		# 将吸收范围内的所有实体ID存入成员变量中
		self.entity_ids = entity_ids
		# print '------------------------------------------------------------------------ l = ', len(entity_ids)

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
					pos_z = (
						float(x - entityPosX) / 800 * 3, float(y - entityPosY) / 800 * 3,
						float(z - entityPosZ) / 800 * 3)
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
						# print '------------------------------------------------------------- kill =', self.kill_count
						# --------------- 此处写黑洞效果随吸收的实体数的变化逻辑 ---------------
						# if self.kill_count != 0 and self.kill_count % 200 == 0:
						# 计算出吸收半径的圆和黑洞杀死半径的圆之间的体积的一半，作为黑洞扩增的吸收物品件数条件
						# limit_count = (2 * math.pi * (self.attract_radius**3 - (self.radius - 3)**3)) / 3
						# print '-----------------------> limit_count =', limit_count

						if self.kill_count != 0 and self.kill_count % (
								((2 + self.change_count) * 100 * self.change_count)) == 0:
							# if self.kill_count != 0 and self.kill_count % 300 == 0:
							# 使扩增倍数加1（使后续扩增条件均是初始条件的一倍）
							self.change_count += 1
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
							self.set_new_block_range_add(self.attract_radius, self.dict['x'], self.dict['y'],
														 self.dict['z'])

	def Destroy(self):
		self.UnListenEvent()
