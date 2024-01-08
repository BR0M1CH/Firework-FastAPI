from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pprint import pprint
from filters import SaluteHandler, PetardHandler, FountaineHandler, BengalHandler


app = FastAPI()
# Добавляем middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к MongoDB
uri = "mongodb://admin:admin@mongodb:27017/"
client = AsyncIOMotorClient(uri)
db = client["Feierverk"]
collection_user = db["User"]
collection_salut = db["Salut"]
collection_bengal=db['Bengal']
collection_fountaine=db['Fountain']
collection_petard=db['Petard']

#######################################################################################################
##############                   Standart CRUD funcs                                 ##################
#######################################################################################################

async def create(item: dict, collection, param_name="name"):
    '''
    Creating new document by item params in choosen collection
    :param item: item, which must be added to collection
    :param collection: collection in Mongo, where item will be added
    :return: newly created document
    '''
    result = await collection.insert_one(item)
    obj = await collection.find_one({param_name: item[param_name]})
    return await get_all(collection)

async def get_all(collection, param_name=None, param=None) -> list:
    '''
    Getting all items in collection
    :param collection: collection in Mongo, which must be returned
    :return: list of collection items
    '''
    documents = []
    async for document in collection.find():
        document['_id'] = str(document['_id'])
        documents.append(document)
    return list(documents)

async def get_by_param(param_name, param, collection):
    '''
    Getting item by param from collection
    :param param_name: name of param
    :param param: value of param
    :param collection: collection in Mongo
    :return: item
    '''
    document = await collection.find_one({param_name: param})
    if document:
        print(document)
        document['_id'] = str(document['_id'])
        return document
    else:
        return None

async def update(search_param_name: str, search_param, updated_item: dict, collection):
    '''
    Updating item, choosen by param from collection
    :param search_param_name: name of param
    :param search_param: value of param
    :param updated_item: new version of item(can be some params, not all)
    :param collection: collection in Mongo
    :return: updated item
    '''
    await collection.update_one({search_param_name: search_param}, {"$set": updated_item})
    document = await collection.find_one({search_param_name: search_param})
    document['_id'] = str(document['_id'])
    return document

async def delete(search_param_name: str, search_param, collection):
    '''
    Delete item, choosen by param from collection
    :param search_param_name: name of param
    :param search_param: value of param
    :param collection: collection in Mongo
    :return: {'message': '1'}
    '''
    await collection.delete_one({search_param_name: search_param})
    return {"message": "1"}

async def get_top_fountains(count=1):
    top_fountains = await collection_fountaine.find({"available": {"$gt": 5}}, sort=[("sales", -1)]).limit(count).to_list(length=count)
    for i in range(len(top_fountains)):
        top_fountains[i]['_id'] = str(top_fountains[i]['_id'])
    return top_fountains

async def get_top_bengals(count=2):
    top_bengals = await collection_bengal.find({"available": {"$gt": 5}}, sort=[("sales", -1)]).limit(count).to_list(length=count)
    for i in range(len(top_bengals)):
        top_bengals[i]['_id'] = str(top_bengals[i]['_id'])
    return top_bengals

async def get_top_petards(count=2):
    top_petards = await collection_petard.find({"available": {"$gt": 5}}, sort=[("sales", -1)]).limit(count).to_list(length=count)
    for i in range(len(top_petards)):
        top_petards[i]['_id'] = str(top_petards[i]['_id'])
    return top_petards

async def get_param(collection, param_name: str):
    print('called')
    pipeline = [
        {"$group": {
            "_id": None,
            "max_param": {"$max": f"${param_name}"}
        }}
    ]
    result = await collection.aggregate(pipeline).to_list(1)
    if result:
        max_param = result[0]['max_param']
    else:
        max_param = 0
    return max_param


#######################################################################################################
##############                                ROUTES                                 ##################
#######################################################################################################

@app.post('/reg')
async def register(data: dict):
    data['royalty_level']=0
    data['permission']=0
    user = await create(data, collection_user, param_name='id')
    print(user)
    return user

@app.get('/reg/{id}')
async def check_reg(id: int):
    user = await get_by_param('id', id, collection_user)
    if user:
        return 1
    else:
        return None

@app.get('/auth')
async def auth(id: int, password: str):
    user = await get_by_param('id', id, collection_user)
    if user:
        if user['password'] == password:
            return 1
        else:
            return None

@app.get('/password')
async def password_hash(id: int):
    password = await get_by_param('id', id, collection_user)
    return password['password']

@app.get('/user')
async def get_all_users():
    users = await get_all(collection_user)
    return users

@app.get('/user/{id}')
async def get_user(id: int):
    user = await get_by_param('id', id, collection_user)
    if user:
        return user
    else:
        return None


@app.put("/user/{id}")
async def update_salute(id: int, updated_user: dict):
    document = await update(search_param_name='id', search_param=id, updated_item=updated_user, collection=collection_user)
    return document

@app.delete('/user/{royalty}')
async def delete_user(royalty: int):
    res = await delete(search_param_name='royalty_level', search_param=royalty, collection=collection_user)
    return res

#######################################################################################################
##############                                SALUTE                                 ##################
#######################################################################################################

@app.post("/salutes/")
async def create_salute(salut: dict):
    salut['calibers'] = list(map(float, salut['calibers'].split(', ')))
    salut['text']=f"Выстрелов: {salut['shoots']}<br>Калибр: {'″, '.join(map(str,salut['calibers']))}″<br>Высота: до {salut['height']} метров<br>Длительность: {salut['duration']} сек"
    result = await create(salut, collection_salut)
    if result:
        print(result)
        return result
    else:
        return {"message": "0"}

@app.get("/salutes/")
async def get_salutes():
    salutes = await get_all(collection_salut)
    return salutes

@app.post("/salutes/filtered/")
async def get_salutes_filtered(data: dict):
    print(data['calibers_filter'])
    shoots_expr = SaluteHandler().get_shoots_filter(data['shoots_filter'])
    duration_expr = SaluteHandler().get_duration_filter(data['duration_filter'])
    caliber_expr = SaluteHandler().get_caliber_filter(data['calibers_filter'])
    price_expr = SaluteHandler().get_price_filter(data['min_price_filter'], data['max_price_filter'])
    expr = {"$and": [price_expr, shoots_expr, caliber_expr, duration_expr]}
    print(expr)
    cursor = collection_salut.find(expr, sort=[("sales", -1)])
    result = await cursor.to_list(length=None)
    for i in range(len(result)):
        result[i]['_id']=str(result[i]['_id'])
    print(result)
    return result

@app.get("/salutes/{id}")
async def get_salute_by_id(id: int):
    document = await get_by_param(param_name='id', param=int(id), collection=collection_salut)
    pprint(document)
    fountains = await get_top_fountains(count=2)
    bengals = await get_top_bengals(count=2)
    return [document, fountains, bengals]

@app.put("/salutes/{id}")
async def update_salute(id: int, updated_salute: dict):
    document = await update(search_param_name='name', search_param=id, updated_item=updated_salute, collection=collection_salut)
    return document
@app.delete("/salutes/{id}")
async def delete_document(id: int):
    res = await delete(search_param_name='name', search_param=id, collection=collection_salut)
    return res

@app.get('/salutes/param/')
async def get_salute_max_param(param: str):
    a = await get_param(collection_salut, param_name=param)
    return a
#######################################################################################################
##############                                BENGALS                                ##################
#######################################################################################################
@app.get("/bengals/")
async def get_bengales():
    salutes = await get_all(collection_bengal)
    return salutes

@app.post("/bengals/filtered/")
async def get_bengals_filtered(data: dict):
    length_expr = BengalHandler().get_length_filter(data['length_filter'])
    complection_expr = BengalHandler().get_complection_filter(data['complection_filter'])
    price_expr = BengalHandler().get_price_filter(data['min_price_filter'], data['max_price_filter'])
    expr = {"$and": [price_expr, length_expr, complection_expr]}
    print(expr)
    cursor = collection_bengal.find(expr, sort=[("sales", -1)])
    result = await cursor.to_list(length=None)
    for i in range(len(result)):
        result[i]['_id']=str(result[i]['_id'])
    print(result)
    return result

@app.post("/bengals/")
async def create_salute(bengal: dict):
    bengal['text']=f"Длительность: {bengal['duration']} с<br>Цвета: {bengal['colors']} <br>В пачке: {bengal['count']} шт"
    result = await create(bengal, collection_bengal)
    if result:
        print(result)
        return result
    else:
        return {"message": "0"}

@app.get("/bengals/{id}")
async def get_bengal_by_id(id: int):
    document = await get_by_param(param_name='id', param=int(id), collection=collection_bengal)
    pprint(document)
    fountains = await get_top_fountains(count=2)
    petards = await get_top_petards(count=2)
    return [document, fountains, petards]

@app.put("/bengals/{id}")
async def update_bengal(id: int, updated_bengal: dict):
    document = await update(search_param_name='id', search_param=int(id), updated_item=updated_bengal, collection=collection_bengal)
    return document
@app.delete("/bengals/{id}")
async def delete_bengal(id: int):
    res = await delete(search_param_name='id', search_param=int(id), collection=collection_bengal)
    return res
@app.get('/bengals/param/')
async def get_bengal_max_id(param: str):
    a = await get_param(collection_bengal, param_name=param)
    return a
#######################################################################################################
##############                             FOUNTAINS                                 ##################
#######################################################################################################
@app.get("/fountaines/")
async def get_fountaines():
    fountaines = await get_all(collection_fountaine)
    return fountaines

@app.post("/fountaines/filtered/")
async def get_fountaines_filtered(data: dict):
    height_expr = FountaineHandler().get_height_filter(data['height_filter'])
    duration_expr = FountaineHandler().get_duration_filter(data['duration_filter'])
    price_expr = FountaineHandler().get_price_filter(data['min_price_filter'], data['max_price_filter'])
    expr = {"$and": [price_expr, height_expr, duration_expr]}
    print(expr)
    cursor = collection_fountaine.find(expr, sort=[("sales", -1)])
    result = await cursor.to_list(length=None)
    for i in range(len(result)):
        result[i]['_id']=str(result[i]['_id'])
    print(result)
    return result

@app.post("/fountaines/")
async def create_fountaine(fountain: dict):
    fountain['text']=f"Длительность: {fountain['duration']} с<br>Высота: до {fountain['height']} м"
    result = await create(fountain, collection_fountaine)
    if result:
        print(result)
        return result
    else:
        return {"message": "0"}

@app.get("/fountaines/{id}")
async def get_fountaine_by_id(id: int):
    print('*'*20)
    document = await get_by_param(param_name='id', param=int(id), collection=collection_fountaine)
    pprint(document)
    petards = await get_top_petards(count=2)
    bengals = await get_top_bengals(count=2)
    return [document, petards, bengals]

@app.put("/fountaines/{id}")
async def update_fountaine(id: str, updated_fountaine: dict):
    document = await update(search_param_name='id', search_param=int(id), updated_item=updated_fountaine, collection=collection_fountaine)
    return document
@app.delete("/fountaines/{id}")
async def delete_fountaine(id: str):
    res = await delete(search_param_name='id', search_param=int(id), collection=collection_fountaine)
    return res

@app.get('/fountaines/param/')
async def get_fountaine_max_param(param: str):
    a = await get_param(collection_fountaine, param_name=param)
    return a

#######################################################################################################
##############                             PETARDS                                   ##################
#######################################################################################################
@app.get("/petards/")
async def get_petards():
    petards = await get_all(collection_petard)
    return petards

@app.post("/petards/filtered/")
async def get_petards_filtered(data: dict):
    flight_expr = PetardHandler().get_flight_filter(data['flight_filter'])
    complection_expr = PetardHandler().get_complection_filter(data['complection_filter'])
    price_expr = PetardHandler().get_price_filter(data['min_price_filter'], data['max_price_filter'])
    expr = {"$and": [price_expr, flight_expr, complection_expr]}
    print(expr)
    cursor = collection_petard.find(expr, sort=[("sales", -1)])
    result = await cursor.to_list(length=None)
    for i in range(len(result)):
        result[i]['_id']=str(result[i]['_id'])
    print(result)
    return result

@app.post("/petards/")
async def create_petard(petard: dict):
    pprint(petard)
    if petard['flight']:
        if petard['packet']:
            petard['text']=f"Летающая петарда<br>Цена за пачку {petard['count']}шт!"
        else:
            petard['text']=f"Летающая петарда<br>Цена за шт!"
    else:
        if petard['packet']:
            petard['text']=f"Наземная петарда<br>Цена за пачку {petard['count']}шт!"
        else:
            petard['text']=f"Наземная петарда<br>Цена за шт!"
    result = await create(petard, collection_petard)
    if result:
        print(result)
        return result
    else:
        return {"message": "0"}

@app.get("/petards/{id}")
async def get_petard_by_id(id: str):
    document = await get_by_param(param_name='id', param=int(id), collection=collection_petard)
    pprint(document)
    fountains = await get_top_fountains(count=2)
    bengals = await get_top_bengals(count=2)
    return [document, fountains, bengals]

@app.put("/petards/{id}")
async def update_petard(id: str, updated_petard: dict):
    document = await update(search_param_name='id', search_param=int(id), updated_item=updated_petard, collection=collection_petard)
    return document
@app.delete("/petards/{id}")
async def delete_petard(id: str):
    res = await delete(search_param_name='id', search_param=int(id), collection=collection_petard)
    return res

@app.get('/petards/param/')
async def get_petard_max_param(param: str):
    a = await get_param(collection_petard, param_name=param)
    return a



