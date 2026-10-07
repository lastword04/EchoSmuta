# Mining Service API Documentation

Сервис для управления добычей ресурсов, крафтом предметов и торговлей в городах.

**Base URL:** `http://localhost:8086` (порт может отличаться)

**Требуется аутентификация:** Все эндпоинты требуют JWT токен в заголовке `Authorization: Bearer <token>`

---

## Resources API

Управление ресурсами персонажа и добыча.

### GET /api/resources/

Получить доступные ресурсы на текущей локации персонажа и статистику персонажа.

**Требования:**
- Персонаж должен быть авторизован

**Response:** `LocationResourcesAndCharacterStats`
```json
{
  "location_resources": [
    {
      "id": "uuid",
      "location_slug": "string",
      "resource_slug": "string",
      "chance": 0.5,
      "current_amount": 100,
      "max_amount": 1000,
      "experience_on_resource": 50
    }
  ],
  "character_stats": {
    "id": "uuid",
    "character_id": "uuid",
    "location_slug": "string",
    "experience": 1000,
    "level": 5,
    "add_chance": 0.1
  }
}
```

---

### GET /api/resources/my

Получить все ресурсы персонажа.

**Требования:**
- Персонаж должен быть авторизован

**Response:** `list[ResourseCharacterResponse]`
```json
[
  {
    "id": "uuid",
    "character_id": "uuid",
    "resource_slug": "string",
    "amount": 50,
    "resource": {
      "name": "Iron Ore",
      "slug": "iron-ore",
      "weight": 10,
      "price": 100,
      "serial_number": 1
    }
  }
]
```

---

### GET /api/resources/{resource_slug}

Получить информацию о конкретном ресурсе по slug.

**Path Parameters:**
- `resource_slug` (string, required) - Slug ресурса

**Response:** `ResourceReadSchema`
```json
{
  "id": "uuid",
  "name": "Iron Ore",
  "slug": "iron-ore",
  "weight": 10,
  "price": 100,
  "serial_number": 1
}
```

---

### POST /api/resources/mining/actions

Начать добычу ресурсов (требуется капча).

**Требования:**
- Персонаж должен быть авторизован
- Персонаж должен быть онлайн
- Персонаж не должен быть в процессе другой добычи

**Request Body:** `CaptchaVerificationRequest`
```json
{
  "captcha_token": "string"
}
```

**Response:** `MiningActionReadSchema` (201 Created)
```json
{
  "id": "uuid",
  "character_id": "uuid",
  "location_slug": "string",
  "start_time": "2026-03-02T10:00:00Z",
  "finish_time": "2026-03-02T10:05:00Z",
  "status": "IN_PROGRESS",
  "message": "Mining in progress...",
  "celery_task_id": "task-uuid",
  "result_status": null,
  "recived_resourse_slug": null,
  "count_recived_resource": null
}
```

---

### GET /api/resources/mining/actions/{action_id}

Получить информацию о конкретной добыче по ID.

**Path Parameters:**
- `action_id` (uuid, required) - ID действия добычи

**Response:** `MiningActionReadSchema`
```json
{
  "id": "uuid",
  "character_id": "uuid",
  "location_slug": "string",
  "start_time": "2026-03-02T10:00:00Z",
  "finish_time": "2026-03-02T10:05:00Z",
  "status": "COMPLETED",
  "message": "Mining completed successfully",
  "celery_task_id": "task-uuid",
  "result_status": "SUCCESS",
  "recived_resourse_slug": "iron-ore",
  "count_recived_resource": 5
}
```

---

### GET /api/resources/mining/status

Получить текущий статус добычи персонажа.

**Требования:**
- Персонаж должен быть авторизован

**Response:** `MiningActionResponseSchema`
```json
{
  "mining_action": {
    "id": "uuid",
    "character_id": "uuid",
    "location_slug": "string",
    "start_time": "2026-03-02T10:00:00Z",
    "finish_time": "2026-03-02T10:05:00Z",
    "status": "IN_PROGRESS",
    "message": "Mining in progress...",
    "celery_task_id": "task-uuid",
    "result_status": null,
    "recived_resourse_slug": null,
    "count_recived_resource": null
  }
}
```

---

## Items API

Управление предметами, рецептами, магазинами и торговлей.

### Recipes (Рецепты)

#### GET /api/items/recipes

Получить все доступные рецепты для покупки на текущей локации персонажа.

**Query Parameters:**
- `quantity` (integer, required) - Количество предметов в рецепте (1-100)

**Response:** `list[ResourceItemReadSchema]`
```json
[
  {
    "id": "uuid",
    "name": "Iron Sword",
    "slug": "iron-sword",
    "item_type": "WEAPON",
    "location_slug": "city-forge",
    "price": 500.0,
    "quantity": 1
  }
]
```

---

#### POST /api/items/recipes

Купить рецепт (списываются дукаты с персонажа).

**Request Body:** `CharacterRecipeCreateSchema`
```json
{
  "item_slug": "iron-sword",
  "quantity": 1
}
```

**Response:** `CharacterRecipeReadSchema` (201 Created)
```json
{
  "id": "uuid",
  "character_id": "uuid",
  "item_slug": "iron-sword",
  "quantity": 1,
  "created_at": "2026-03-02T10:00:00Z",
  "updated_at": "2026-03-02T10:00:00Z"
}
```

---

#### GET /api/items/recipes/me

Получить все рецепты персонажа с детальной информацией (только для текущей локации).

**Response:** `list[CharacterRecipeWithDetailsSchema]`
```json
[
  {
    "recipe_id": "uuid",
    "quantity": 1,
    "item_details": {
      "item": {
        "id": "uuid",
        "name": "Iron Sword",
        "slug": "iron-sword",
        "item_type": "WEAPON",
        "location_slug": "city-forge",
        "price": 500.0
      },
      "components": [
        {
          "id": "uuid",
          "item_slug": "iron-sword",
          "resource_slug": "iron-ore",
          "quantity": 5,
          "resource_name": "Iron Ore"
        }
      ]
    }
  }
]
```

---

#### GET /api/items/recipes/me/stock

Получить все рецепты персонажа с информацией о наличии ресурсов (только для текущей локации).

**Response:** `list[CharacterRecipeWithStockSchema]`
```json
[
  {
    "recipe_id": "uuid",
    "quantity": 1,
    "item_details": {
      "item": {
        "id": "uuid",
        "name": "Iron Sword",
        "slug": "iron-sword",
        "item_type": "WEAPON",
        "location_slug": "city-forge",
        "price": 500.0
      },
      "components": [
        {
          "id": "uuid",
          "item_slug": "iron-sword",
          "resource_slug": "iron-ore",
          "quantity": 5,
          "resource_name": "Iron Ore",
          "is_in_stock": true
        }
      ]
    }
  }
]
```

**Примечание:** `is_in_stock` показывает, есть ли у персонажа достаточное количество ресурса для крафта.

---

### Character Items (Инвентарь)

#### GET /api/items/me

Получить все предметы в инвентаре персонажа.

**Response:** `list[InventoryItemReadSchema]`
```json
[
  {
    "id": "uuid",
    "character_id": "uuid",
    "item_slug": "iron-sword",
    "quantity": 3,
    "in_shop": false,
    "on_sale": false,
    "sale_price": null,
    "item": {
      "id": "uuid",
      "name": "Iron Sword",
      "slug": "iron-sword",
      "item_type": "WEAPON",
      "location_slug": "city-forge",
      "price": 500.0
    }
  }
]
```

---

#### GET /api/items/from-location

Получить все предметы персонажа, сгруппированные по категориям (инвентарь, магазин, на продаже).

**Response:** `LocationItemsGroupedSchema`
```json
{
  "inventory_items": [...],
  "shop_items": [...],
  "sale_items": [...]
}
```

---

### Item Details

#### GET /api/items/item/{item_slug}

Получить информацию о предмете по slug.

**Path Parameters:**
- `item_slug` (string, required) - Slug предмета

**Response:** `ItemReadSchema`
```json
{
  "id": "uuid",
  "name": "Iron Sword",
  "slug": "iron-sword",
  "item_type": "WEAPON",
  "location_slug": "city-forge",
  "price": 500.0
}
```

---

#### GET /api/items/{item_id}/details

Получить детальную информацию о предмете с компонентами.

**Path Parameters:**
- `item_id` (uuid, required) - ID предмета

**Response:** `ItemDetailsSchema`
```json
{
  "item": {
    "id": "uuid",
    "name": "Iron Sword",
    "slug": "iron-sword",
    "item_type": "WEAPON",
    "location_slug": "city-forge",
    "price": 500.0
  },
  "components": [
    {
      "id": "uuid",
      "item_slug": "iron-sword",
      "resource_slug": "iron-ore",
      "quantity": 5,
      "resource_name": "Iron Ore"
    }
  ]
}
```

---

### Shop Management (Управление магазином)

#### GET /api/items/city-shop

Получить магазин персонажа на текущей локации.

**Response:** `CityTradingShopResponseSchema`
```json
{
  "shop": {
    "id": "uuid",
    "character_id": "uuid",
    "location_slug": "city-market",
    "number": 1,
    "name": "My Shop",
    "description": "Best items in town",
    "level": 1,
    "capacity": 10,
    "license_duration": "2026-04-02T10:00:00Z",
    "photo_id": "uuid"
  },
  "items": [...]
}
```

---

#### POST /api/items/city-shop/

Создать магазин на текущей локации персонажа.

**Требования:**
- У персонажа должно быть достаточно дукатов
- Персонаж должен соответствовать минимальному уровню

**Response:** `CityTradingShopResponseSchema` (201 Created)

---

#### GET /api/items/city-shop/settings

Получить настройки покупки магазина для текущей локации.

**Response:** `CityTradingShopBuySettingsReadSchema`
```json
{
  "id": "uuid",
  "location_slug": "city-market",
  "min_level": 5,
  "price": 10000.0
}
```

---

#### GET /api/items/city-shop/{id}

Получить магазин по ID.

**Path Parameters:**
- `id` (uuid, required) - ID магазина

**Response:** `CityTradingShopResponseSchema`

---

#### GET /api/items/city-shop/number/{number}

Получить магазин по номеру на текущей локации.

**Path Parameters:**
- `number` (integer, required) - Номер магазина

**Response:** `CityTradingShopResponseSchema`

---

#### GET /api/items/city-shop/paginate

Получить список магазинов с предметами на продаже (пагинация).

**Query Parameters:**
- `page` (integer, default: 1) - Номер страницы
- `page_size` (integer, default: 5, max: 100) - Количество на странице
- `location_slug` (string, optional, max: 128) - Слаг локации персонажа. Если передан, сервер использует его напрямую, избегая дополнительного HTTP-запроса к сервису персонажей.

**Response:** `PaginatedShopsWithSaleItemsSchema`
```json
{
  "items": [
    {
      "shop": {...},
      "sale_items": [...]
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 5,
  "total_pages": 10
}
```

---

#### PATCH /api/items/city-shop/{id}/info

Обновить информацию о магазине (название, описание).

**Path Parameters:**
- `id` (uuid, required) - ID магазина

**Request Body:** `CityTradingShopUpdateInfoSchema`
```json
{
  "name": "New Shop Name",
  "description": "New description"
}
```

**Response:** `CityTradingShopReadSchema`

---

#### PATCH /api/items/city-shop/{id}/photo

Обновить фото магазина.

**Path Parameters:**
- `id` (uuid, required) - ID магазина

**Request Body:** `CityTradingShopUpdatePhotoSchema`
```json
{
  "photo_id": "uuid"
}
```

**Response:** `CityTradingShopReadSchema`

---

#### POST /api/items/city-shop/{id}/renewal

Продлить лицензию магазина.

**Path Parameters:**
- `id` (uuid, required) - ID магазина

**Требования:**
- У персонажа должно быть достаточно дукатов

**Response:** `CityTradingShopReadSchema`

---

### Shop Inventory (Управление товарами в магазине)

#### POST /api/items/shops/inventory/{item_id}/list

Выставить предмет из инвентаря в магазин.

**Path Parameters:**
- `item_id` (uuid, required) - ID предмета в инвентаре

**Требования:**
- Предмет должен принадлежать персонажу
- В магазине должно быть свободное место
- Предмет не должен быть уже в магазине или на продаже

**Response:** `LocationItemsGroupedSchema`

---

#### POST /api/items/shops/inventory/{item_id}/withdraw

Забрать предмет из магазина в инвентарь.

**Path Parameters:**
- `item_id` (uuid, required) - ID предмета в инвентаре

**Требования:**
- Предмет должен быть в магазине
- Предмет не должен быть на продаже

**Response:** `LocationItemsGroupedSchema`

---

### Sale Management (Управление продажами)

#### POST /api/items/sale/inventory/{inventory_item_id}

Выставить предмет на продажу.

**Path Parameters:**
- `inventory_item_id` (uuid, required) - ID предмета в инвентаре

**Request Body:** `SaleInventoryItemCreateSchema`
```json
{
  "price": 1000.0
}
```

**Требования:**
- Предмет должен быть в магазине
- Предмет не должен быть уже на продаже

**Response:** `LocationItemsGroupedSchema` (201 Created)

---

#### DELETE /api/items/sale/inventory/{inventory_item_id}

Снять предмет с продажи.

**Path Parameters:**
- `inventory_item_id` (uuid, required) - ID предмета в инвентаре

**Требования:**
- Предмет должен быть на продаже

**Response:** `LocationItemsGroupedSchema`

---

### Purchase (Покупка)

#### POST /api/items/purchase/inventory/{inventory_item_id}

Купить предмет у другого игрока.

**Path Parameters:**
- `inventory_item_id` (uuid, required) - ID предмета в инвентаре продавца

**Требования:**
- Предмет должен быть на продаже
- У покупателя должно быть достаточно дукатов
- Покупатель не может купить свой собственный предмет

**Response:** `StatusOkSchema`

---

### Stats (Статистика)

#### GET /api/items/stats

Получить статистику торговли персонажа на текущей локации.

**Query Parameters:**
- `location_slug` (string, optional, max: 128) - Слаг локации персонажа. Если передан, сервер использует его напрямую, избегая дополнительного HTTP-запроса к сервису персонажей.

**Response:** `CharacterCityTradeStatsReadSchema`
```json
{
  "id": "uuid",
  "character_id": "uuid",
  "location_slug": "city-market",
  "experience": 1500,
  "level": 3,
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-02T10:00:00Z"
}
```

**Примечание:** Если статистика не существует, она будет создана автоматически с начальными значениями (experience: 0, level: 1).

---

## Типы предметов (ItemType)

- `WEAPON` - Оружие
- `ARMOR` - Броня
- `CONSUMABLE` - Расходуемое
- `MATERIAL` - Материал
- `QUEST` - Квестовый предмет

---

## Статусы добычи (MiningStatus)

- `IN_PROGRESS` - В процессе
- `COMPLETED` - Завершено
- `FAILED` - Провалено
- `CANCELLED` - Отменено

---

## Статусы результата (ResultStatus)

- `SUCCESS` - Успех
- `FAILURE` - Неудача
- `CRITICAL_SUCCESS` - Критический успех
- `CRITICAL_FAILURE` - Критическая неудача

---

## Коды ошибок

### 400 Bad Request
- Неверные параметры запроса
- Недостаточно ресурсов/дукатов
- Предмет уже на продаже/в магазине

### 401 Unauthorized
- Отсутствует или невалидный токен авторизации

### 403 Forbidden
- Персонаж не авторизован
- Недостаточно прав для выполнения действия
- Персонаж не онлайн

### 404 Not Found
- Ресурс/предмет/магазин не найден

### 409 Conflict
- Персонаж уже в процессе добычи
- Магазин уже существует

### 422 Unprocessable Entity
- Ошибка валидации данных

---

## Примеры использования

### Начать добычу ресурсов

```bash
curl -X POST http://localhost:8086/api/resources/mining/actions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"captcha_token": "captcha-token-here"}'
```

### Купить рецепт

```bash
curl -X POST http://localhost:8086/api/items/recipes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"item_slug": "iron-sword", "quantity": 1}'
```

### Создать магазин

```bash
curl -X POST http://localhost:8086/api/items/city-shop/ \
  -H "Authorization: Bearer <token>"
```

### Выставить предмет на продажу

```bash
curl -X POST http://localhost:8086/api/items/sale/inventory/{item_id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"price": 1000.0}'
```
