# AQI 数据下载与查询设置指南

## 概述

本指南介绍如何设置和使用 AQI（空气质量指数）数据下载和查询功能。系统使用"在意空气"（Air Matters）作为数据源，提供实时 AQI 数据。

## 1. 环境配置

### 1.1 获取 API 密钥

1. 访问 [在意空气官网](https://www.air-matters.com/)
2. 注册账号并申请 API 密钥
3. 获取 API Key（格式类似：`your_api_key_here`）

### 1.2 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# 在意空气 AQI 数据源
AIR_MATTERS_KEY=你的API密钥
```

## 2. 数据库设置

### 2.1 创建数据表

运行以下命令创建 AQI 相关数据表：

```bash
python -m downloader.main --init-db
```

这会创建以下表：
- `aqi_city`: 城市 AQI 数据表
- `aqi_station`: 监测站 AQI 数据表

### 2.2 验证数据表

连接数据库查看表结构：

```sql
DESCRIBE aqi_city;
DESCRIBE aqi_station;
```

## 3. 数据下载

### 3.1 查看支持的城市

```bash
python -m downloader.aqi_downloader --list
```

输出示例：
```
支持的城市列表:
==================================================
上海         | 1212a003   | 101020100
乌鲁木齐      | 7418bb74   | 101130101
兰州         | ed4d93e2   | 101160101
北京         | 29a34245   | 101010100
...
```

### 3.2 下载单个城市数据

```bash
python -m downloader.aqi_downloader --city 北京
```

### 3.3 下载所有城市数据

```bash
python -m downloader.aqi_downloader
```

## 4. 数据查询

### 4.1 使用 Python 代码查询

```python
from app.skills.aqi import query_aqi_data

# 查询北京 AQI
result = await query_aqi_data("北京")
print(result)
```

### 4.2 使用 MCP 工具查询

在 Claude Code 或 Cursor 中，可以直接使用 MCP 工具：

```
查询北京的 AQI 数据
```

系统会返回：
```json
{
  "success": true,
  "city": "北京",
  "update_time": "2024-01-15 10:00:00",
  "aqi": {
    "value": 75,
    "level": "良",
    "description": "空气质量可接受，某些污染物可能对少数人健康有轻微影响"
  },
  "pollutants": {
    "pm2.5": {"value": 55, "unit": "μg/m³", "iaqi": 75},
    "pm10": {"value": 85, "unit": "μg/m³", "iaqi": 67},
    ...
  },
  "health_advice": {
    "general": "可正常户外活动",
    "sensitive": "减少长时间、高强度的户外活动",
    "outdoor": "适宜",
    "mask": "不需要"
  }
}
```

## 5. 数据结构

### 5.1 城市 AQI 数据表 (aqi_city)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| city_id | VARCHAR(20) | 在意空气城市ID |
| city_name | VARCHAR(64) | 城市名称 |
| update_time | VARCHAR(32) | 数据更新时间 |
| aqi | INT | AQI指数 |
| pm25 | FLOAT | PM2.5浓度(μg/m³) |
| pm25_iaqi | INT | PM2.5分指数 |
| pm10 | FLOAT | PM10浓度(μg/m³) |
| pm10_iaqi | INT | PM10分指数 |
| so2 | FLOAT | SO2浓度(μg/m³) |
| so2_iaqi | INT | SO2分指数 |
| no2 | FLOAT | NO2浓度(μg/m³) |
| no2_iaqi | INT | NO2分指数 |
| o3 | FLOAT | O3浓度(μg/m³) |
| o3_iaqi | INT | O3分指数 |
| co | FLOAT | CO浓度(mg/m³) |
| co_iaqi | INT | CO分指数 |
| source | VARCHAR(32) | 数据源 |
| created_at | DATETIME | 创建时间 |

### 5.2 监测站 AQI 数据表 (aqi_station)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| station_code | VARCHAR(32) | 监测站编码 |
| station_name | VARCHAR(64) | 监测站名称 |
| city_id | VARCHAR(20) | 所属城市ID |
| city_name | VARCHAR(64) | 所属城市名称 |
| update_time | VARCHAR(32) | 数据更新时间 |
| aqi | INT | AQI指数 |
| ... | ... | 其他污染物字段同城市表 |

## 6. 城市映射

系统使用两种城市ID：
1. **在意空气ID**: 字母数字混合，如 `29a34245`
2. **系统ID**: 纯数字，如 `101010100`（北京局格式）

映射关系存储在 `downloader/aqi_downloader.py` 的 `CITY_MAPPING` 字典中。

## 7. AQI 等级标准

| AQI范围 | 等级 | 颜色 | 健康影响 |
|---------|------|------|----------|
| 0-50 | 优 | 绿色 | 空气质量令人满意，基本无空气污染 |
| 51-100 | 良 | 黄色 | 空气质量可接受，某些污染物可能对少数人健康有轻微影响 |
| 101-150 | 轻度污染 | 橙色 | 敏感人群症状有轻度加剧，健康人群出现刺激症状 |
| 151-200 | 中度污染 | 红色 | 进一步加剧敏感人群症状，可能对心脏和呼吸系统有影响 |
| 201-300 | 重度污染 | 紫色 | 健康人群运动耐受力降低，有明显强烈症状 |
| >300 | 严重污染 | 褐红色 | 健康人群运动耐受力降低，有明显强烈症状，提前采取措施 |

## 8. 健康建议

系统根据 AQI 等级提供健康建议：

- **一般人群**: 日常活动建议
- **敏感人群**: 老人、儿童、呼吸系统疾病患者等
- **户外活动**: 是否适宜户外运动
- **佩戴口罩**: 是否需要佩戴防护口罩

## 9. 定时更新

建议设置定时任务，每小时更新一次 AQI 数据：

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每小时整点执行）
0 * * * * cd /path/to/WeatherAgent && python -m downloader.aqi_downloader >> /var/log/aqi_download.log 2>&1
```

## 10. 故障排除

### 10.1 API 密钥错误

错误信息：`❌ 未配置 AIR_MATTERS_KEY`

**解决方案**：检查 `.env` 文件中的 `AIR_MATTERS_KEY` 配置。

### 10.2 数据库连接失败

错误信息：`❌ 连接数据库失败`

**解决方案**：
1. 检查 MySQL 服务是否运行
2. 检查数据库连接参数
3. 确认数据库用户权限

### 10.3 城市ID未找到

错误信息：`未知城市ID: xxxxxxxx`

**解决方案**：
1. 检查 `CITY_MAPPING` 中是否包含该城市
2. 如需添加新城市，在 `CITY_MAPPING` 中添加映射关系

## 11. 扩展开发

### 11.1 添加新城市

在 `downloader/aqi_downloader.py` 的 `CITY_MAPPING` 中添加：

```python
CITY_MAPPING = {
    # 现有映射...
    "new_city_id": ("新城市名", "系统城市ID"),
}
```

### 11.2 自定义健康建议

修改 `get_health_advice()` 函数，调整不同 AQI 等级的建议内容。

### 11.3 数据可视化

可以基于 `aqi_city` 表数据，使用 Matplotlib 或 Plotly 绘制 AQI 趋势图。

## 12. 测试

运行测试脚本验证功能：

```bash
# 测试城市映射
python tests/test_aqi_mapping.py

# 测试下载功能（模拟）
python tests/test_aqi_download.py
```

## 13. 相关文件

- `downloader/aqi_downloader.py`: AQI 下载器主程序
- `app/skills/aqi.py`: AQI 查询 Skill
- `app/mcp/server.py`: MCP 工具定义
- `downloader/models.py`: 数据库模型
- `tests/test_aqi_mapping.py`: 城市映射测试
- `tests/test_aqi_download.py`: 下载功能测试
