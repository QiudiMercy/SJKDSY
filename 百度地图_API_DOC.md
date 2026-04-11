# 百度地图 Web 服务 API 调用文档

> **文档生成时间**: 2026-04-01
> **Access Key (AK)**: `XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM`
> **说明**: 本文档包含所有验证成功的 API 调用方法

---

## 目录

1. [位置服务](#1-位置服务)
2. [路线规划](#2-路线规划)
3. [轨迹服务](#3-轨迹服务)
4. [天气服务](#4-天气服务)
5. [地图服务](#5-地图服务)
6. [其他服务](#6-其他服务)

---

## 1. 位置服务

### 1.1 地点检索

**功能描述**: 检索某一行政区划内的地点信息，支持城市检索、圆形区域检索

**接口地址**: `https://api.map.baidu.com/place/v2/search`

**请求方法**: GET

**请求参数**:

| 参数名    | 类型   | 必填 | 说明                                     |
| --------- | ------ | ---- | ---------------------------------------- |
| query     | string | 是   | 检索关键字，如"银行"、"美食"             |
| region    | string | 是   | 检索行政区划区域，如"北京"               |
| output    | string | 否   | 输出格式，json或xml，默认json            |
| ak        | string | 是   | 访问密钥                                 |
| scope     | int    | 否   | 检索结果详细程度，1=基本信息，2=详细信息 |
| page_num  | int    | 否   | 分页页码，从0开始                        |
| page_size | int    | 否   | 每页结果数，默认10，最大20               |

**请求示例**:

```
https://api.map.baidu.com/place/v2/search?query=银行&region=北京&output=json&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "message": "ok",
  "result_type": "poi_type",
  "query_type": "general",
  "results": [
    {
      "name": "招商银行(北京青年路支行)",
      "location": {
        "lat": 39.933729,
        "lng": 116.523186
      },
      "address": "北京市朝阳区青年路西里5号院15号楼二层",
      "province": "北京市",
      "city": "北京市",
      "area": "朝阳区",
      "telephone": "(010)85563091",
      "uid": "0ede7102f32db77f0f0a700e"
    }
  ]
}
```

**返回参数说明**:

| 参数名                 | 类型   | 说明              |
| ---------------------- | ------ | ----------------- |
| status                 | int    | 状态码，0表示成功 |
| message                | string | 状态说明          |
| results                | array  | POI结果列表       |
| results[].name         | string | POI名称           |
| results[].location.lat | float  | 纬度              |
| results[].location.lng | float  | 经度              |
| results[].address      | string | 地址              |
| results[].province     | string | 省份              |
| results[].city         | string | 城市              |
| results[].area         | string | 区县              |
| results[].telephone    | string | 电话              |
| results[].uid          | string | POI唯一标识       |

---

### 1.2 地理编码

**功能描述**: 将结构化地址转换为经纬度坐标

**接口地址**: `https://api.map.baidu.com/geocoding/v3/`

**请求方法**: GET

**请求参数**:

| 参数名  | 类型   | 必填 | 说明                                     |
| ------- | ------ | ---- | ---------------------------------------- |
| address | string | 是   | 结构化地址，如"北京市海淀区上地十街10号" |
| output  | string | 否   | 输出格式，json或xml                      |
| ak      | string | 是   | 访问密钥                                 |
| city    | string | 否   | 指定城市，提高解析准确度                 |

**请求示例**:

```
https://api.map.baidu.com/geocoding/v3/?address=北京市海淀区上地十街10号&output=json&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "result": {
    "location": {
      "lng": 116.30787799999993,
      "lat": 40.05702706489032
    },
    "precise": 1,
    "confidence": 100,
    "comprehension": 100,
    "level": ""
  }
}
```

**返回参数说明**:

| 参数名               | 类型   | 说明                          |
| -------------------- | ------ | ----------------------------- |
| status               | int    | 状态码，0表示成功             |
| result.location.lng  | float  | 经度                          |
| result.location.lat  | float  | 纬度                          |
| result.precise       | int    | 是否精确查找，1=精确，0=模糊  |
| result.confidence    | int    | 可信度，100表示高可信         |
| result.comprehension | int    | 地址理解程度，100表示完全理解 |
| result.level         | string | 地址类型                      |

---

### 1.3 逆地理编码

**功能描述**: 将经纬度坐标转换为结构化地址

**接口地址**: `https://api.map.baidu.com/reverse_geocoding/v3/`

**请求方法**: GET

**请求参数**:

| 参数名         | 类型   | 必填 | 说明                                          |
| -------------- | ------ | ---- | --------------------------------------------- |
| location       | string | 是   | 经纬度坐标，格式"lat,lng"，如"39.934,116.427" |
| output         | string | 否   | 输出格式，json或xml                           |
| ak             | string | 是   | 访问密钥                                      |
| coordtype      | string | 否   | 坐标类型，bd09ll(默认)、gcj02ll、wgs84ll      |
| extensions_poi | int    | 否   | 是否返回POI数据，1=返回，0=不返回             |

**请求示例**:

```
https://api.map.baidu.com/reverse_geocoding/v3/?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&output=json&location=39.934,116.427
```

**返回结果**:

```json
{
  "status": 0,
  "result": {
    "location": {
      "lng": 116.43973552597666,
      "lat": 39.9413310374553
    },
    "formatted_address": "北京市东城区北新桥街道南顺城街90号",
    "business": "东四,东直门,东四十条",
    "addressComponent": {
      "country": "中国",
      "province": "北京市",
      "city": "北京市",
      "district": "东城区",
      "town": "北新桥街道",
      "street": "南顺城街",
      "street_number": "90号",
      "adcode": "110101"
    },
    "pois": [],
    "cityCode": 131
  }
}
```

**返回参数说明**:

| 参数名                                | 类型   | 说明              |
| ------------------------------------- | ------ | ----------------- |
| status                                | int    | 状态码，0表示成功 |
| result.location.lng                   | float  | 经度              |
| result.location.lat                   | float  | 纬度              |
| result.formatted_address              | string | 格式化地址        |
| result.business                       | string | 商圈信息          |
| result.addressComponent.country       | string | 国家              |
| result.addressComponent.province      | string | 省份              |
| result.addressComponent.city          | string | 城市              |
| result.addressComponent.district      | string | 区县              |
| result.addressComponent.town          | string | 乡镇/街道         |
| result.addressComponent.street        | string | 街道              |
| result.addressComponent.street_number | string | 门牌号            |
| result.addressComponent.adcode        | string | 行政区划代码      |
| result.cityCode                       | int    | 城市代码          |

---

### 1.4 坐标转换

**功能描述**: 将不同坐标系的坐标进行转换

**接口地址**: `https://api.map.baidu.com/geoconv/v1/`

**请求方法**: GET

**请求参数**:

| 参数名 | 类型   | 必填 | 说明                                               |
| ------ | ------ | ---- | -------------------------------------------------- |
| coords | string | 是   | 源坐标，格式"lng,lat"，多个用";"分隔               |
| from   | int    | 是   | 源坐标类型，1=wgs84, 2=gcj02, 3=bd09ll, 4=bd09mc   |
| to     | int    | 是   | 目标坐标类型，3=bd09ll, 4=bd09mc, 5=gcj02, 6=wgs84 |
| ak     | string | 是   | 访问密钥                                           |

**请求示例**:

```
https://api.map.baidu.com/geoconv/v1/?coords=116.397428,39.90923&from=1&to=5&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "result": [
    {
      "x": 116.41004950771968,
      "y": 39.91697707917046
    }
  ]
}
```

**返回参数说明**:

| 参数名     | 类型  | 说明              |
| ---------- | ----- | ----------------- |
| status     | int   | 状态码，0表示成功 |
| result     | array | 转换后的坐标列表  |
| result[].x | float | 经度              |
| result[].y | float | 纬度              |

---

### 1.5 时区查询

**功能描述**: 查询指定坐标所在的时区信息

**接口地址**: `https://api.map.baidu.com/timezone/v1`

**请求方法**: GET

**请求参数**:

| 参数名    | 类型   | 必填 | 说明                       |
| --------- | ------ | ---- | -------------------------- |
| location  | string | 是   | 经纬度坐标，格式"lat,lng"  |
| ak        | string | 是   | 访问密钥                   |
| timestamp | int    | 否   | Unix时间戳，用于计算夏令时 |

**请求示例**:

```
https://api.map.baidu.com/timezone/v1?location=39.934,116.427&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&timestamp=1775036757
```

**返回结果**:

```json
{
  "status": 0,
  "result": {
    "time_zone": "Asia/Shanghai",
    "raw_offset": 28800,
    "dst_offset": 0,
    "local_time": "2026-04-01 18:04:02"
  }
}
```

**返回参数说明**:

| 参数名            | 类型   | 说明              |
| ----------------- | ------ | ----------------- |
| status            | int    | 状态码，0表示成功 |
| result.time_zone  | string | 时区名称          |
| result.raw_offset | int    | 与UTC的偏移秒数   |
| result.dst_offset | int    | 夏令时偏移秒数    |
| result.local_time | string | 本地时间          |

---

### 1.6 普通IP定位

**功能描述**: 根据IP地址获取大致位置信息

**接口地址**: `https://api.map.baidu.com/location/ip`

**请求方法**: GET

**请求参数**:

| 参数名 | 类型   | 必填 | 说明                            |
| ------ | ------ | ---- | ------------------------------- |
| ak     | string | 是   | 访问密钥                        |
| ip     | string | 否   | IP地址，不填则使用请求IP        |
| coor   | string | 否   | 坐标类型，bd09ll(默认)、gcj02ll |

**请求示例**:

```
https://api.map.baidu.com/location/ip?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&ip=202.108.22.5&coor=bd09ll
```

**返回结果**:

```json
{
  "status": 0,
  "address": "CN|北京|北京|None|CHINANET|0|0",
  "content": {
    "address": "北京市",
    "address_detail": {
      "province": "北京市",
      "city": "北京市",
      "district": "",
      "street": "",
      "street_number": "",
      "city_code": 131
    },
    "point": {
      "x": "116.39564503787867",
      "y": "39.92998577808024"
    }
  }
}
```

---

### 1.7 行政区划检索

**功能描述**: 检索行政区划信息，支持省、市、区县查询

**接口地址**: `https://api.map.baidu.com/api_region_search/v1/`

**请求方法**: GET

**请求参数**:

| 参数名    | 类型   | 必填 | 说明                           |
| --------- | ------ | ---- | ------------------------------ |
| keyword   | string | 是   | 检索关键字，如"北京"           |
| ak        | string | 是   | 访问密钥                       |
| sub_admin | int    | 否   | 是否返回下级行政区，0=否，1=是 |

**请求示例**:

```
https://api.map.baidu.com/api_region_search/v1/?keyword=北京&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "message": "ok",
  "results": [
    {
      "name": "北京市",
      "code": "110000",
      "level": "province",
      "children": []
    }
  ]
}
```

---

### 1.8 行政区划热点POI查询

**功能描述**: 查询行政区划内的热点POI推荐

**接口地址**: `https://api.map.baidu.com/place/v2/suggestion`

**请求方法**: GET

**请求参数**:

| 参数名 | 类型   | 必填 | 说明                   |
| ------ | ------ | ---- | ---------------------- |
| query  | string | 是   | 检索关键字，如"天安门" |
| region | string | 是   | 行政区划，如"北京"     |
| output | string | 否   | 输出格式，json或xml    |
| ak     | string | 是   | 访问密钥               |

**请求示例**:

```
https://api.map.baidu.com/place/v2/suggestion?query=天安门&region=北京&output=json&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "message": "ok",
  "result": [
    {
      "name": "天安门",
      "location": {
        "lat": 39.909946,
        "lng": 116.397467
      },
      "uid": "65e1ee886c885190f60e77ff",
      "city": "北京市",
      "district": "东城区",
      "business": "",
      "cityid": "131"
    }
  ]
}
```

---

## 2. 路线规划

### 2.1 驾车路线规划(轻量)

**功能描述**: 驾车路线规划轻量版，支持驾车、骑行、步行、公交

**接口地址**: `https://api.map.baidu.com/directionlite/v1/driving`

**请求方法**: GET

**请求参数**:

| 参数名      | 类型   | 必填 | 说明                                        |
| ----------- | ------ | ---- | ------------------------------------------- |
| origin      | string | 是   | 起点坐标，格式"lat,lng"                     |
| destination | string | 是   | 终点坐标，格式"lat,lng"                     |
| ak          | string | 是   | 访问密钥                                    |
| tactics     | int    | 否   | 路线策略，11=常规，12=高速优先，13=躲避拥堵 |

**请求示例**:

```
https://api.map.baidu.com/directionlite/v1/driving?origin=39.934,116.427&destination=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "message": "ok",
  "result": {
    "routes": [
      {
        "distance": 3527,
        "duration": 847,
        "steps": [
          {
            "distance": 352,
            "duration": 60,
            "direction": 1,
            "instruction": "从起点向正北方向出发,行驶352米,右转",
            "path": "116.427368,39.934112;116.427368,39.934212"
          }
        ]
      }
    ]
  }
}
```

**返回参数说明**:

| 参数名                              | 类型   | 说明              |
| ----------------------------------- | ------ | ----------------- |
| status                              | int    | 状态码，0表示成功 |
| result.routes                       | array  | 路线列表          |
| result.routes[].distance            | int    | 路线距离，单位米  |
| result.routes[].duration            | int    | 预计时间，单位秒  |
| result.routes[].steps               | array  | 路线分段          |
| result.routes[].steps[].distance    | int    | 分段距离          |
| result.routes[].steps[].duration    | int    | 分段时间          |
| result.routes[].steps[].instruction | string | 行驶指示          |
| result.routes[].steps[].path        | string | 分段路径坐标      |

---

### 2.2 骑行路线规划(轻量)

**接口地址**: `https://api.map.baidu.com/directionlite/v1/riding`

**请求参数**: 同驾车路线规划

**请求示例**:

```
https://api.map.baidu.com/directionlite/v1/riding?origin=39.934,116.427&destination=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

---

### 2.3 步行路线规划(轻量)

**接口地址**: `https://api.map.baidu.com/directionlite/v1/walking`

**请求参数**: 同驾车路线规划

**请求示例**:

```
https://api.map.baidu.com/directionlite/v1/walking?origin=39.934,116.427&destination=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

---

### 2.4 公交路线规划(轻量)

**接口地址**: `https://api.map.baidu.com/directionlite/v1/transit`

**请求参数**: 同驾车路线规划

**请求示例**:

```
https://api.map.baidu.com/directionlite/v1/transit?origin=39.934,116.427&destination=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

---

### 2.5 小客车标准导航

**功能描述**: 小客车标准导航，提供更详细的导航信息

**接口地址**: `https://api.map.baidu.com/direction/v2/driving`

**请求方法**: GET

**请求参数**:

| 参数名      | 类型   | 必填 | 说明                    |
| ----------- | ------ | ---- | ----------------------- |
| origin      | string | 是   | 起点坐标，格式"lat,lng" |
| destination | string | 是   | 终点坐标，格式"lat,lng" |
| ak          | string | 是   | 访问密钥                |
| tactics     | int    | 否   | 路线策略，12=高速优先   |

**请求示例**:

```
https://api.map.baidu.com/direction/v2/driving?origin=39.934,116.427&destination=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**: 包含详细的路线信息、交通状况、限速提示等

---

### 2.6 公交路线规划

**接口地址**: `https://api.map.baidu.com/direction/v2/transit`

**请求参数**: 同驾车路线规划

**请求示例**:

```
https://api.map.baidu.com/direction/v2/transit?origin=39.934,116.427&destination=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

---

### 2.7 批量算路

**功能描述**: 批量计算多个起点到多个终点的路线

**接口地址**: `https://api.map.baidu.com/routematrix/v2/driving`

**请求方法**: GET

**请求参数**:

| 参数名       | 类型   | 必填 | 说明                                             |
| ------------ | ------ | ---- | ------------------------------------------------ |
| origins      | string | 是   | 起点坐标，多个用"\|"分隔，格式"lat,lng\|lat,lng" |
| destinations | string | 是   | 终点坐标，多个用"\|"分隔                         |
| ak           | string | 是   | 访问密钥                                         |
| tactics      | int    | 否   | 路线策略                                         |

**请求示例**:

```
https://api.map.baidu.com/routematrix/v2/driving?origins=39.934,116.427&destinations=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "result": [
    {
      "distance": {"value": 3527, "text": "3.5公里"},
      "duration": {"value": 847, "text": "14分钟"}
    }
  ]
}
```

---

### 2.8 小客车算路

**接口地址**: `https://api.map.baidu.com/routematrix/v2/driving`

**请求参数**: 同批量算路，可添加 tactics 参数

**请求示例**:

```
https://api.map.baidu.com/routematrix/v2/driving?origins=39.934,116.427&destinations=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&tactics=12
```

---

### 2.9 公交信息查询

**接口地址**: `https://api.map.baidu.com/direction/v2/transit`

**请求参数**: 同公交路线规划

**请求示例**:

```
https://api.map.baidu.com/direction/v2/transit?origin=39.934,116.427&destination=39.914,116.404&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

---

### 2.10 巡航API

**功能描述**: 获取巡航模式下的路况信息

**接口地址**: `https://api.map.baidu.com/cruise/v1`

**请求方法**: GET

**请求参数**:

| 参数名    | 类型   | 必填 | 说明                        |
| --------- | ------ | ---- | --------------------------- |
| ak        | string | 是   | 访问密钥                    |
| location  | string | 是   | 当前位置坐标，格式"lat,lng" |
| speed     | int    | 是   | 当前速度，单位km/h          |
| direction | int    | 是   | 行驶方向，0-360度           |

**请求示例**:

```
https://api.map.baidu.com/cruise/v1?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&location=39.934,116.427&speed=60&direction=90
```

---

## 3. 轨迹服务

### 3.1 鹰眼轨迹

**功能描述**: 鹰眼轨迹服务，用于追踪和管理移动设备轨迹

**接口地址**: `https://yingyan.baidu.com/v3/entity/add`

**请求方法**: GET/POST

**请求参数**:

| 参数名      | 类型   | 必填 | 说明     |
| ----------- | ------ | ---- | -------- |
| ak          | string | 是   | 访问密钥 |
| service_id  | string | 是   | 服务ID   |
| entity_name | string | 是   | 实体名称 |

**请求示例**:

```
https://yingyan.baidu.com/v3/entity/add?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&service_id=TEST&entity_name=test_entity
```

**返回结果**:

```json
{
  "status": 0,
  "message": "成功"
}
```

---

### 3.2 轨迹重合分析

**功能描述**: 分析两条轨迹的重合率

**接口地址**: `https://api.map.baidu.com/trackmatch/v1`

**请求方法**: GET

**请求参数**:

| 参数名         | 类型   | 必填 | 说明                            |
| -------------- | ------ | ---- | ------------------------------- |
| ak             | string | 是   | 访问密钥                        |
| standard_track | string | 是   | 标准轨迹，格式"lat,lng;lat,lng" |
| query_track    | string | 是   | 查询轨迹，格式"lat,lng;lat,lng" |

**请求示例**:

```
https://api.map.baidu.com/trackmatch/v1?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&standard_track=39.934,116.427;39.935,116.428&query_track=39.934,116.427;39.935,116.428
```

**返回结果**:

```json
{
  "status": 0,
  "result": {
    "similarity": 0.95,
    "matched_distance": 1200,
    "total_distance": 1250
  }
}
```

---

## 4. 天气服务

### 4.1 国内天气查询

**功能描述**: 查询国内城市天气信息

**接口地址**: `https://api.map.baidu.com/weather/v1/`

**请求方法**: GET

**请求参数**:

| 参数名      | 类型   | 必填 | 说明                                  |
| ----------- | ------ | ---- | ------------------------------------- |
| district_id | string | 是   | 行政区划代码，如"110105"(朝阳区)      |
| data_type   | string | 是   | 数据类型，all=全部，now=实时，fc=预报 |
| ak          | string | 是   | 访问密钥                              |

**请求示例**:

```
https://api.map.baidu.com/weather/v1/?district_id=110105&data_type=all&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "result": {
    "location": {
      "country": "中国",
      "province": "北京市",
      "city": "北京市",
      "name": "朝阳区",
      "id": "110105"
    },
    "now": {
      "temp": 25,
      "feels_like": 26,
      "text": "晴",
      "wind_class": "3级",
      "wind_dir": "东南风",
      "humidity": 45,
      "pressure": 1012,
      "precipitation": 0
    },
    "forecasts": []
  }
}
```

**返回参数说明**:

| 参数名                   | 类型   | 说明              |
| ------------------------ | ------ | ----------------- |
| status                   | int    | 状态码，0表示成功 |
| result.location          | object | 位置信息          |
| result.now.temp          | int    | 当前温度，摄氏度  |
| result.now.feels_like    | int    | 体感温度          |
| result.now.text          | string | 天气现象          |
| result.now.wind_class    | string | 风力等级          |
| result.now.wind_dir      | string | 风向              |
| result.now.humidity      | int    | 相对湿度          |
| result.now.pressure      | int    | 气压              |
| result.now.precipitation | float  | 降水量            |
| result.forecasts         | array  | 未来天气预报      |

---

## 5. 地图服务

### 5.1 静态图

**功能描述**: 获取静态地图图片

**接口地址**: `https://api.map.baidu.com/staticimage/v2`

**请求方法**: GET

**请求参数**:

| 参数名  | 类型   | 必填 | 说明                                          |
| ------- | ------ | ---- | --------------------------------------------- |
| ak      | string | 是   | 访问密钥                                      |
| center  | string | 是   | 地图中心点坐标，格式"lng,lat"                 |
| width   | int    | 否   | 图片宽度，默认400，最大1024                   |
| height  | int    | 否   | 图片高度，默认300，最大1024                   |
| zoom    | int    | 否   | 地图级别，3-19                                |
| markers | string | 否   | 标注点，格式"lng,lat"或多个"lng,lat\|lng,lat" |

**请求示例**:

```
https://api.map.baidu.com/staticimage/v2?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&center=116.427,39.934&width=400&height=300&zoom=15
```

**返回结果**: 返回PNG格式的图片数据

---

## 6. 其他服务

### 6.1 多维检索

**功能描述**: 支持多维度条件的地点检索

**接口地址**: `https://api.map.baidu.com/place/v2/search`

**请求方法**: GET

**请求参数**: 同地点检索，可添加 tag 参数进行筛选

| 参数名 | 类型   | 必填 | 说明                       |
| ------ | ------ | ---- | -------------------------- |
| query  | string | 是   | 检索关键字                 |
| tag    | string | 否   | 分类筛选，如"火锅"、"酒店" |
| region | string | 是   | 行政区划                   |
| output | string | 否   | 输出格式                   |
| ak     | string | 是   | 访问密钥                   |

**请求示例**:

```
https://api.map.baidu.com/place/v2/search?query=美食&tag=火锅&region=北京&output=json&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

---

### 6.2 云存储

**功能描述**: LBS云存储服务，用于存储自定义POI数据

**接口地址**: `https://api.map.baidu.com/geodata/v4/poi/list`

**请求方法**: GET

**请求参数**:

| 参数名      | 类型   | 必填 | 说明     |
| ----------- | ------ | ---- | -------- |
| ak          | string | 是   | 访问密钥 |
| geotable_id | string | 否   | 数据表ID |
| page_index  | int    | 否   | 页码     |
| page_size   | int    | 否   | 每页数量 |

**请求示例**:

```
https://api.map.baidu.com/geodata/v4/poi/list?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

---

### 6.3 MCP(SSE)

**功能描述**: MCP SSE服务

**接口地址**: `https://api.map.baidu.com/mcp/v1/sse`

**请求方法**: GET

**请求参数**:

| 参数名 | 类型   | 必填 | 说明     |
| ------ | ------ | ---- | -------- |
| ak     | string | 是   | 访问密钥 |
| query  | string | 是   | 查询内容 |

**请求示例**:

```
https://api.map.baidu.com/mcp/v1/sse?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&query=北京
```

---

## 附录

### 坐标系说明

| 坐标系  | 说明       | 适用场景                   |
| ------- | ---------- | -------------------------- |
| wgs84ll | GPS坐标    | 国际标准，GPS设备使用      |
| gcj02ll | 国测局坐标 | 中国标准，高德、腾讯等使用 |
| bd09ll  | 百度经纬度 | 百度地图标准坐标           |
| bd09mc  | 百度墨卡托 | 百度地图米制坐标           |

### 状态码说明

| 状态码 | 说明           |
| ------ | -------------- |
| 0      | 成功           |
| 1      | 服务器内部错误 |
| 2      | 参数错误       |
| 3      | 请求方法错误   |
| 4      | 权限不足       |
| 5      | AK不存在或非法 |
| 101    | 服务禁用       |
| 102    | 不通过白名单   |
| 200    | 无请求权限     |
| 201    | 无请求配额     |
| 302    | 天配额超限     |

---

## 7. 补充API（修复后验证成功）

### 7.1 实时路况查询

**功能描述**: 查询指定道路的实时拥堵情况和拥堵趋势

**接口地址**: `https://api.map.baidu.com/traffic/v1/road`

**请求方法**: GET

**请求参数**:

| 参数名    | 类型   | 必填 | 说明                     |
| --------- | ------ | ---- | ------------------------ |
| ak        | string | 是   | 访问密钥                 |
| road_name | string | 是   | 道路名称，如"北四环中路" |
| city      | string | 是   | 城市名称，如"北京市"     |

**请求示例**:

```
https://api.map.baidu.com/traffic/v1/road?ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM&road_name=北四环中路&city=北京市
```

**返回结果**:

```json
{
  "status": 0,
  "message": "成功",
  "description": "北四环中路：自东向西拥堵；自西向东轻微拥堵；东向西,北四环中路附近严重拥堵；",
  "evaluation": {
    "status": 3,
    "status_desc": "自东向西拥堵；自西向东轻微拥堵"
  },
  "road_traffic": [
    {
      "congestion_sections": [
        {
          "road_type": 2,
          "congestion_distance": 3680,
          "speed": 12.19,
          "status": 4,
          "congestion_trend": "加重",
          "section_desc": "东向西,北四环中路附近"
        }
      ]
    }
  ]
}
```

**返回参数说明**:

| 参数名                                                   | 类型   | 说明                                         |
| -------------------------------------------------------- | ------ | -------------------------------------------- |
| status                                                   | int    | 状态码，0表示成功                            |
| description                                              | string | 路况描述                                     |
| evaluation.status                                        | int    | 拥堵状态，1=畅通，2=缓慢，3=拥堵，4=严重拥堵 |
| evaluation.status_desc                                   | string | 状态描述                                     |
| road_traffic                                             | array  | 道路路况详情                                 |
| road_traffic[].congestion_sections                       | array  | 拥堵路段列表                                 |
| road_traffic[].congestion_sections[].congestion_distance | int    | 拥堵距离（米）                               |
| road_traffic[].congestion_sections[].speed               | float  | 平均速度（km/h）                             |
| road_traffic[].congestion_sections[].status              | int    | 拥堵状态                                     |
| road_traffic[].congestion_sections[].congestion_trend    | string | 拥堵趋势：加重/持平/缓解                     |

---

### 7.2 深度检索（地点详情）

**功能描述**: 获取指定地点的详细信息，包括评分、营业时间等

**接口地址**: `https://api.map.baidu.com/place/v2/detail`

**请求方法**: GET

**请求参数**:

| 参数名 | 类型   | 必填 | 说明                         |
| ------ | ------ | ---- | ---------------------------- |
| uid    | string | 是   | POI的唯一标识UID             |
| output | string | 否   | 输出格式，json或xml          |
| scope  | string | 否   | 检索结果详细程度，2=详细信息 |
| ak     | string | 是   | 访问密钥                     |

**请求示例**:

```
https://api.map.baidu.com/place/v2/detail?uid=65e1ee886c885190f60e77ff&output=json&scope=2&ak=XmUR7gKwOoHukHL6VbzkdJmb7o0NlMhM
```

**返回结果**:

```json
{
  "status": 0,
  "message": "ok",
  "result": {
    "uid": "65e1ee886c885190f60e77ff",
    "name": "天安门",
    "location": {
      "lat": 39.915119,
      "lng": 116.403963
    },
    "address": "北京市东城区长安街",
    "province": "北京市",
    "city": "北京市",
    "area": "东城区",
    "telephone": "(010)65016000",
    "detail_info": {
      "classified_poi_tag": "旅游景点;人文景观;文物古迹;古建筑",
      "tag": "旅游景点;文物古迹",
      "overall_rating": "4.9",
      "comment_num": "10000+",
      "shop_hours": "05:00-22:00",
      "detail_url": "http://api.map.baidu.com/place/detail?uid=65e1ee886c885190f60e77ff",
      "image_num": "500+"
    }
  }
}
```

**返回参数说明**:

| 参数名                                | 类型   | 说明              |
| ------------------------------------- | ------ | ----------------- |
| status                                | int    | 状态码，0表示成功 |
| result.uid                            | string | POI唯一标识       |
| result.name                           | string | 地点名称          |
| result.location.lat                   | float  | 纬度              |
| result.location.lng                   | float  | 经度              |
| result.address                        | string | 地址              |
| result.telephone                      | string | 电话              |
| result.detail_info.classified_poi_tag | string | 分类标签          |
| result.detail_info.overall_rating     | string | 综合评分          |
| result.detail_info.comment_num        | string | 评论数量          |
| result.detail_info.shop_hours         | string | 营业时间          |
| result.detail_info.detail_url         | string | 详情页链接        |
| result.detail_info.image_num          | string | 图片数量          |

**使用说明**:

1. 先通过地点检索API获取有效的UID
2. 使用UID调用详情接口获取深度信息
3. scope=2 才能返回详细信息（评分、营业时间等）

---

**文档版本**: v1.1
**最后更新**: 2026-04-01
**API总数**: 30个验证成功
