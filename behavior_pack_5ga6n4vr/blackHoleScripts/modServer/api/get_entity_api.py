# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi

def get_pet_enemies_around(eid, radius, except_entity=False):
    """
    获取区域内的敌方entity列表
    """
    comp = serverApi.GetEngineCompFactory().CreateGame(eid)
    filters = {"any_of": [
        {
            "subject": "other",
            "test": "is_family",
            "value": "enemy"
        },
        {
            "subject": "other",
            "test": "is_family",
            "value": "monster"
        },
        {
            "subject": "other",
            "test": "is_family",
            "value": "mob"
        },
    ]}
    entity_ids = comp.GetEntitiesAround(eid, radius, filters)
    if except_entity:
        if eid in entity_ids:
            entity_ids.remove(eid)
    return entity_ids