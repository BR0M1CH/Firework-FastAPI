
salutes_duration = {
    "1" : [20],
    "2": [20, 40],
    "3": [40, 60],
    "4": [60, 90],
    "5": [90]
}

salutes_shoots = {
    "1": [16],
    "2": [16, 25],
    "3": [25, 36],
    "4": [36, 50],
    "5": [50, 100],
    "6": [100, 200],
    "7": [200]
}

class Handler_Parent():
    def param_handler(param_list: list, param: str, collection: dict):
        list = []
        for attr in param_list:
            if len(collection[attr])>1:
                list.append( {param: {"$gte": collection[attr][0], "$lte": collection[attr][1]}})
            else:
                if attr=="1":
                    list.append({param: {"$lte": collection["1"][0]}})
                else:
                    list.append({param: {"$gte": collection[attr][0]}})
        if len(param_list)>1:
            value = {"$or": list}
        elif len(param_list)==1:
            value = list[0]
        else:
            value = {}
        return value

    @classmethod
    def get_price_filter(cls, min_price, max_price):
        return {"price": {"$gte": min_price, "$lte": max_price}}


class SaluteHandler(Handler_Parent):

    salutes_duration = {
        "1": [20],
        "2": [20, 40],
        "3": [40, 60],
        "4": [60, 90],
        "5": [90]
    }

    salutes_shoots = {
        "1": [16],
        "2": [16, 25],
        "3": [25, 36],
        "4": [36, 50],
        "5": [50, 100],
        "6": [100, 200],
        "7": [200]
    }

    @classmethod
    def get_shoots_filter(cls, param_list: list):
        return cls.param_handler(param_list, 'shoots', cls.salutes_shoots)

    @classmethod
    def get_duration_filter(cls, param_list: list):
        return cls.param_handler(param_list, 'duration', cls.salutes_duration)

    @classmethod
    def get_caliber_filter(cls, param_list: list):
        param_list = list(map(float, param_list))
        if len(param_list) > 0:
            return {'calibers': {"$in": param_list}}
        else:
            return {}


class PetardHandler(Handler_Parent):

    @classmethod
    def get_flight_filter(cls, param_list: list):
        param_list = list(map(bool, map(int, param_list)))
        if len(param_list) > 0:
            return({'flight': {"$in": param_list}})
        else:
            return {}

    @classmethod
    def get_complection_filter(cls, param_list: list):
        param_list = list(map(int, param_list))
        if len(param_list) > 0:
            if 20 in param_list:
                return( {"$or": [{"count": {"$in": param_list}}, {"count": {"$gte": 20}}]} )
            else:
                return( {'count': {"$in": param_list}})
        else:
            return {}

class FountaineHandler(Handler_Parent):

    duration_dict = {
        "1": [40],
        "2": [40, 60],
        "3": [60, 80],
        "4": [80]
    }
    @classmethod
    def get_height_filter(cls, param_list: list):
        param_list = list(map(int, param_list))
        if len(param_list) > 0:
            return({'height': {"$in": param_list}})
        else:
            return {}

    @classmethod
    def get_duration_filter(cls, param_list: list):
        return cls.param_handler(param_list, 'duration', cls.duration_dict)

class BengalHandler(Handler_Parent):

    @classmethod
    def get_length_filter(cls, param_list: list):
        param_list = list(map(int, param_list))
        if len(param_list) > 0:
            return({'length': {"$in": param_list}})
        else:
            return {}

    @classmethod
    def get_complection_filter(cls, param_list: list):
        param_list = list(map(int, param_list))
        if len(param_list) > 0:
            return({'count': {"$in": param_list}})
        else:
            return {}