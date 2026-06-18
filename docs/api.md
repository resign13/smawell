# Gingtto Storefront API

## 基础信息

- 本地商城后端: `http://127.0.0.1:5301`
- 数据库: PostgreSQL 16 `smawell_admin`
- 商城账号来源: `store_users`
- 受保护接口统一使用: `Authorization: Bearer <token>`

## 通用状态码

- `200` 请求成功
- `201` 创建成功
- `400` 参数错误或业务校验失败
- `401` 未登录或登录失效
- `404` 资源不存在
- `500` 服务异常

## 1. 健康检查

### `GET /api/health`

返回服务和数据库连通状态。

## 2. 首页数据

### `GET /api/home`

查询参数:
- `lang`: `zh | en`

返回字段:
- `banners[]`
- `featured[]`
- `categories[]`
- `stats[]`

## 3. 商城账号登录

### `POST /api/auth/store/login`

请求体:
```json
{
  "email": "buyer@company.com",
  "password": "secret123"
}
```

响应示例:
```json
{
  "token": "string",
  "user": {
    "id": 1,
    "name": "Buyer",
    "companyName": "Gingtto Partner",
    "email": "buyer@company.com",
    "status": "active",
    "createdAt": "2026-04-24T08:00:00+00:00"
  }
}
```

## 4. 当前登录信息

### `GET /api/auth/me`

## 5. 退出登录

### `POST /api/auth/logout`

## 6. 商品列表

### `GET /api/products`

查询参数:
- `lang`: `zh | en`
- `category`: 分类 key
- `keyword`: 商品名称模糊搜索关键字

返回字段:
- `items[].id`
- `items[].slug`
- `items[].sku`
- `items[].productCode`
- `items[].colorGroup`
- `items[].colorName`
- `items[].colorHex`
- `items[].categoryKey`
- `items[].categoryLabel`
- `items[].price`
- `items[].formattedPrice`
- `items[].stock`
- `items[].featured`
- `items[].origin`
- `items[].sizes[]`
- `items[].sizePrices[]`
- `items[].sizePrices[].sizeCode`
- `items[].sizePrices[].price`
- `items[].sizePrices[].stock`
- `items[].image`
- `items[].gallery[]`
- `items[].name`
- `items[].summary`
- `items[].description`
- `items[].searchText`
- `total`

## 7. 商品详情

### `GET /api/products/:slug`

查询参数:
- `lang`: `zh | en`

响应示例:
```json
{
  "product": {
    "id": 1,
    "slug": "mercerized-cotton-t-shirt-white",
    "sku": "GT-TS-001",
    "productCode": "zm393-wht",
    "colorGroup": "zm393",
    "colorName": "White",
    "colorHex": "#F5F1E8",
    "price": 36.99,
    ],
    "sizes": ["S", "M"],
    "sizePrices": [
      { "sizeCode": "S", "price": 36.99, "stock": 50 },
      { "sizeCode": "M", "price": 38.99, "stock": 42 }
    ],
    "colorOptions": [
      {
        "id": 1,
        "slug": "mercerized-cotton-t-shirt-white",
        "productCode": "zm393-wht",
        "colorName": "White",
        "colorHex": "#F5F1E8",
        "image": "https://example.com/white.jpg",
        "stock": 92
      }
    ],
    "stock": 92
  },
  "related": []
}
```

说明:
- `colorOptions` 用于同款不同颜色切换，前端应跳转到对应 `slug`
- 每个颜色款式是独立商品，`stock` 是该颜色所有尺码库存总和
- `sizePrices[].stock` 是该颜色下具体尺码的库存，下单传 `sizeCode` 时会优先扣减对应尺码库存

## 8. 提交订单

### `POST /api/orders`

业务规则:
- 校验当前登录商城账号是否有效
- 一次提交整个购物车，写入一张 `orders` 和多条 `order_items`
- 扣减 `products.stock`
- 如果传入 `sizeCode`，同时扣减 `product_size_prices.stock`
- 库存不足时返回 `400`

请求体:
```json
{
  "contact": {
    "value": "buyer@company.com",
    "marketingOptIn": true
  },
  "delivery": {
    "country": "United States",
    "firstName": "Lina",
    "lastName": "Buyer",
    "address": "1250 Market Street",
    "apartment": "Suite 600",
    "city": "San Francisco",
    "state": "California",
    "zip": "94103",
    "phone": "+1 415 000 0000"
  },
  "items": [
    {
      "productId": 1,
      "sizeCode": "M",
      "quantity": 2
    },
    {
      "productId": 2,
      "sizeCode": "L",
      "quantity": 5
    }
  ],
  "note": "",
  "labelImageUrls": []
}
```

返回字段:
- `order.id`
- `order.orderNo`
- `order.status`
- `order.totalAmount`
- `order.trackingNo`
- `order.items[]`

必填校验:
- `contact.value`
- `delivery.country`
- `delivery.lastName`
- `delivery.address`
- `delivery.city`
- `delivery.state`
- `delivery.zip`
- `delivery.phone`
- `items[]`

## 8.1 上传订单附件

### `POST /api/order-attachments`

说明:
- 需要登录
- 支持上传备注附件，最多 5 个（PDF/图片）
- 文件大小限制 10MB

响应示例:
```json
{
  "items": [
    {"url": "https://example.com/uploads/abc.jpg", "filename": "label.jpg"}
  ],
  "urls": ["https://example.com/uploads/abc.jpg"]
}
```

## 9. 我的订单

### `GET /api/store/orders`

查询参数:
- `q` 可选，按订单号、商品名称、SKU、联系信息搜索

说明:
- 仅返回当前登录商城账号自己的订单
- 返回字段包含订单级信息与明细数组
- 新下单时 `trackingNo` 为空，前台展示为待上传
- 后台改成 `shipped` 后会回传物流单号
- 只有未发货状态订单允许前台取消；`shipped / completed / cancelled` 不允许取消

响应字段:
- `items[].id`
- `items[].orderNo`
- `items[].status`
- `items[].createdAt`
- `items[].totalAmount`
- `items[].itemCount`
- `items[].contactName`
- `items[].contactValue`
- `items[].phone`
- `items[].country`
- `items[].address`
- `items[].apartment`
- `items[].city`
- `items[].state`
- `items[].zip`
- `items[].shippingAddress`
- `items[].marketingOptIn`
- `items[].trackingNo`
- `items[].note`
- `items[].labelImageUrls`
- `items[].paymentLink`
- `items[].shippedAt`
- `items[].completedAt`
- `items[].canCancel`
- `items[].items[]`
- `items[].items[].productId`
- `items[].items[].productName`
- `items[].items[].sku`
- `items[].items[].sizeCode`
- `items[].items[].quantity`
- `items[].items[].unitPrice`
- `items[].items[].totalPrice`
- `items[].items[].image`

## 10. 取消订单

### `POST /api/store/orders/:orderId/cancel`

说明:
- 仅允许当前商城账号取消自己的订单
- 仅 `pending_payment` 和 `paid` 状态允许取消
- 取消后会自动回补 `products.stock`
- 如果订单包含尺码库存，也会回补 `product_size_prices.stock`

成功响应:
```json
{
  "message": "Order cancelled successfully",
  "order": {
    "id": 12,
    "orderNo": "LM-000012",
    "status": "cancelled"
  }
}
```
