"""
AQI 单元测试 - 不需要数据库连接
"""

import pytest
from downloader.aqi_downloader import (
    calculate_iaqi,
    get_aqi_description,
    get_aqi_level,
    get_health_advice,
    parse_aqi_data,
)


@pytest.mark.unit
class TestAQILevel:
    """AQI等级测试"""

    def test_excellent(self):
        """测试优等级"""
        assert get_aqi_level(25) == "优"
        assert get_aqi_level(50) == "优"

    def test_good(self):
        """测试良等级"""
        assert get_aqi_level(51) == "良"
        assert get_aqi_level(100) == "良"

    def test_mild_pollution(self):
        """测试轻度污染"""
        assert get_aqi_level(101) == "轻度污染"
        assert get_aqi_level(150) == "轻度污染"

    def test_moderate_pollution(self):
        """测试中度污染"""
        assert get_aqi_level(151) == "中度污染"
        assert get_aqi_level(200) == "中度污染"

    def test_heavy_pollution(self):
        """测试重度污染"""
        assert get_aqi_level(201) == "重度污染"
        assert get_aqi_level(300) == "重度污染"

    def test_severe_pollution(self):
        """测试严重污染"""
        assert get_aqi_level(301) == "严重污染"
        assert get_aqi_level(500) == "严重污染"

    def test_none_value(self):
        """测试None值"""
        assert get_aqi_level(None) is None


@pytest.mark.unit
class TestAQIDescription:
    """AQI描述测试"""

    def test_excellent_description(self):
        """测试优描述"""
        desc = get_aqi_description("优")
        assert "基本无空气污染" in desc

    def test_good_description(self):
        """测试良描述"""
        desc = get_aqi_description("良")
        assert "可接受" in desc

    def test_unknown_level(self):
        """测试未知等级"""
        desc = get_aqi_description("未知等级")
        assert desc == ""


@pytest.mark.unit
class TestHealthAdvice:
    """健康建议测试"""

    def test_excellent_advice(self):
        """测试优健康建议"""
        advice = get_health_advice("优")
        assert advice["outdoor"] == "适宜"
        assert advice["mask"] == "不需要"

    def test_heavy_pollution_advice(self):
        """测试重度污染健康建议"""
        advice = get_health_advice("重度污染")
        assert advice["outdoor"] == "避免"
        assert advice["mask"] == "必须佩戴"

    def test_unknown_level_advice(self):
        """测试未知等级健康建议"""
        advice = get_health_advice("未知等级")
        assert advice == {}


@pytest.mark.unit
class TestParseAQIData:
    """解析AQI数据测试"""

    def test_parse_valid_data(self):
        """测试解析有效数据"""
        mock_item = {
            "place": {
                "place_id": "ec8399ca",
                "type": "city",
                "name": "北京",
                "city_name": "北京"
            },
            "latest": {
                "update_time": "2024-01-15 10:00:00",
                "readings": [
                    {"kind": "aqi", "value": "75"},
                    {"kind": "pm25", "value": "55"},
                    {"kind": "pm10", "value": "85"}
                ]
            }
        }

        result = parse_aqi_data(mock_item)
        assert result is not None
        assert result["place_id"] == "ec8399ca"
        assert result["place_name"] == "北京"
        assert result["aqi"] == 75.0
        assert result["pm25"] == 55.0

    def test_parse_empty_readings(self):
        """测试解析空数据"""
        mock_item = {
            "place": {"place_id": "test", "type": "city", "name": "test"},
            "latest": {"update_time": "2024-01-15 10:00:00", "readings": []}
        }

        result = parse_aqi_data(mock_item)
        assert result is None


@pytest.mark.unit
class TestCalculateIAQI:
    """计算IAQI测试"""

    def test_calculate_pm25_iaqi(self):
        """测试计算PM2.5 IAQI"""
        data = {"pm25": 55.0}
        result = calculate_iaqi(data)
        assert "pm25_iaqi" in result
        assert result["pm25_iaqi"] > 0

    def test_calculate_pm10_iaqi(self):
        """测试计算PM10 IAQI"""
        data = {"pm10": 85.0}
        result = calculate_iaqi(data)
        assert "pm10_iaqi" in result
        assert result["pm10_iaqi"] > 0

    def test_calculate_aqi(self):
        """测试计算AQI"""
        data = {"pm25": 55.0, "pm10": 85.0}
        result = calculate_iaqi(data)
        assert "aqi" in result
        assert result["aqi"] > 0

    def test_calculate_with_zero_value(self):
        """测试零值处理"""
        data = {"pm25": 0.0}
        result = calculate_iaqi(data)
        # 零值不计算IAQI
        assert "pm25_iaqi" not in result
