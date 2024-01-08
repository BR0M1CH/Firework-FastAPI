FastAPI

Вторая состовляющая приложения - микросервис, связывающий БД с "фронтендом" и обрабатывающий некоторые запросы
(можно было разбить на еще более мелкие микросервисы - обработчик и доступ к БД, но тут удобнее было сделать так)
Логика: где-то развернут микросервис Firework Flask, независимо от него FastAPI, и где-то еще существует контейнер/виртуалка/хостинг с MongoDB (в идеале еще FTP-сервер для фото и видео).
Проекты не зависят друг от друга программно, могут находится на разных машинах, хранятся в разных репозиториях, что позволяет назвать их микросервисами (возможно минисервисы, их стоило бы еще сильнее подробить)

В качестве БД будут использоваться bson файлы, в качестве СУБД будет использоваться MongoDB, в качестве ORM выступит библиотека Motor, которая ползволяет реализовать асинхронные обращения к БД.

Микросервис состоит из двух файлов - *filters.py* и *main.py*, начнем с описания меньшего

# filters.py

В этом файле описаны классы, которые нужны для составления запросов отфильтрованных товаров к БД

__Идея1__: 
    Если на веб-интерфейсе в качестве какого-либо фильтра не выбрано ничего - значит он не участвует в выборке

__Идея2__: 
    Необходимо дифференцировать фильтры по области охвата: некоторые из них представляют выбор точных значений, например калибр салюта, другие же представляют диапазон значений, например время салюта.

Для реализации двух идей был создан мастер класс *ParentHandler*:
```python
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
```

Функция  param_handler нужна для обработки фильтров, подразумевающих диапазон значений, причем диапазон не однозначен,
он может представлять собой 
* *меньше чем Х*, 
* *больше чем Х*, 
* *больше чем Х, меньше чем У*

На вход поступает список значений - выбор клиента, наименование параметра, по которому нужно отфильтровать выдачу 
и коллекция - словарь, которые сопоставит пришедшее значение и то, что ожидается от БД.
Например на веб-интерфейсе пользовать выбрал время "работы" салюта 20-40 секунд, из формы пришло значение
 2, это значение другой микросервис отправит в запросе сюда, здесь функция обратится к словарю,
который для примера выглядит так:
```python
dict = {
"1": [20],
"2": [20,40],
"3": [40]
}
```
После обращения к словарю - функция посмотрим на длину значения по ключу
 и увидит, что длина больше 1, значит это диапазон и запрос необходимо
 соединить в скобку с *gte* и *lte* операторами, в противном случае 
функция посмотрит, ключ аттрибута 1? Если да, то это диапазон *меньше*, если же ключ не "1"
 и заранее известно, что его длина не 2, то это диапазон больше. 
Сама функция идет циклом по всем переданным значениям, и каждую итерацию кидает результат в список, 
затем производится анализ: сколько данных поступило
* если длина входящего списка 1: конечным выражением станет раскрытие массива (или массив[0])
* если длина входящего списка > 1: конечным выражением станет *"or": список*
* если же длина равна нулю - фильтр будет {}, что соответствует его отсутвию.

*Пометка: зря я наверное так много расписал*

Так же в этот класс входит get_price_filter - потому что цена - единственный фильтр, присущий каждой категории

*Пометка: декоратор @classmethod возможно будет ошибкой и стоило применить @staticmethod*

В дальнейшем создаются новые классы фильтров для каждой категории,
эти классы наследуются от описанного Мастер-класса, пример:
```python
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
```
В этом классе объявляется тот самый словарь, к которому будет обращаться функция составления запроса с диапазоном,
помимо этой функции здесь находится функция, которая просто составляет список значений, которые должны совпадать.
 В данном случае это высота салюта, на веб-интерфейсе: 2м, 3м, 4м. 

# main.py

В начале файла происходит инициализация самого приложения, уставновление соединения с БД и обращение (или создание) к коллекциям

Затем идет первая секция  - объявление функций, которые потом будут использоваться в маршрутах, это:
* Создать объект
* Получить список всех объектов коллекции
* Получить объект по параметру
* Обновить данные объекта
* Удалить объект
* Получить список самых продаваемых товаров:
    * фонтаны
    * бенгальские свечи
    * петарды
    
    Это нужно для дополнительной секции товара - *не забудьте купить*
* Получить максимальный параметр

Все вышеописанные функции (кроме топ товаров) на вход получают объект коллекции
и данные, по которым должна функция работать

Вторая секция - маршруты, делится на две категории - товары и пользователь

## Товары

Начнем с описания маршрутов товаров. Для каждой категории маршруты и их логика предельно схожи, так что
будут описаны маршруты одной категории - Салюты

* @app.post("/salutes/")
    ```python
    async def create_salute(salut: dict):
        salut['calibers'] = list(map(float, salut['calibers'].split(', ')))
        salut['text']=f"Выстрелов: {salut['shoots']}<br>Калибр: {'″, '.join(map(str,salut['calibers']))}″<br>Высота: до {salut['height']} метров<br>Длительность: {salut['duration']} сек"
        result = await create(salut, collection_salut)
        if result:
            print(result)
            return result
        else:
            return {"message": "0"}
    ```
  

Этот маршрут отвечает за добавление нового салюта, на вход поступает словарь (если по научному - десериализованный объект json)
В словаре по ключу 'calibers' лежит строка - список (человеческий, не программистский)
Функция его засплитит и перепопределить в список float-объектов
    

Важно отметить, что для рендеринга всех категорий служат всего 2 шаблона html - 
для всех объектов (каталог) и для одного (страница товара), соответственно нужно как-то
универсализировать текст, который будет выводится на веб-интерфейс, чтобы не писать
для каждой категории его отдельно. Это делает вторая строка - создает поле 'text', в котором хранится
описание товара, которое увидит пользователь. Затем просто отпрарвляется запрос к БД и подгоняется результат


* @app.get("/salutes/")
```python
async def get_salutes():
    salutes = await get_all(collection_salut)
    return salutes
```
Здесь простое получения всех товаров данной категории

* @app.post("/salutes/filtered/")
```python
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
```
Здесь в четыре переменные кладутся выражения, описывающие условия фильтрации выборка салютов,
объединяются с помощью оператора *$and*
Создаётся курсор, в котором применено выражение и затем асинхронно курсор забирает данные и превращает их в список


* @app.get("/salutes/{id}")
```python
async def get_salute_by_id(id: int):
    document = await get_by_param(param_name='id', param=int(id), collection=collection_salut)
    pprint(document)
    fountains = await get_top_fountains(count=2)
    bengals = await get_top_bengals(count=2)
    return [document, fountains, bengals]
```
Поиск салюта по id, так же забор данных о топовых фонтанах и бенгальских свечах
(ранее описывалось зачем нужны топовые товары)

* Базовые методы для редактирования и удаления:
```python
@app.put("/salutes/{id}")
async def update_salute(id: int, updated_salute: dict):
    document = await update(search_param_name='id', search_param=id, updated_item=updated_salute, collection=collection_salut)
    return document

@app.delete("/salutes/{id}")
async def delete_document(id: int):
    res = await delete(search_param_name='id', search_param=id, collection=collection_salut)
    return res
```

* @app.get('/salutes/param/')
```python
async def get_salute_max_param(param: str):
    a = await get_param(collection_salut, param_name=param)
    return a
```
Здесь подразумевается что сам параметр будет передан в качестве аргумента запроса - 
в основном применяется для получения максимальной цены салюта, для отображения в фильтре

## Пользователи

```python
#Нужно для создания нового пользователя
@app.post('/reg')
async def register(data: dict):
    data['royalty_level']=0
    data['permission']=0
    user = await create(data, collection_user, param_name='id')
    print(user)
    return user

#Нужно для проверки логина при регистрации (дальше id, логин и номер телефона - одно и то же)
@app.get('/reg/{id}')
async def check_reg(id: int):
    user = await get_by_param('id', id, collection_user)
    if user:
        return 1
    else:
        return None

#На вход поступает хэш пароля и сверяется с записью в БД, нужно для проверки совпадения логина и пароля
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
```

# Итог

Этот микросервис обратывает данные, пришедшие от пользователя (микросервис на Flask тоже обрабатывает данные, но там обработка заключается
в подгоне данных под формат обмена данными, а здесь данные обретают смысл) и составляет запросы к БД

Контейнер прилагается
