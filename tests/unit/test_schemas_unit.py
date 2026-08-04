"""
数据模型验证单元测试
测试Pydantic Schema的验证逻辑
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    FeedbackRequest,
    WeatherData,
    HourlyData,
    ForecastData,
    FeelsLikeResult,
)


# ============ FeedbackRequest 测试 ============


@pytest.mark.unit
class TestFeedbackRequest:
    """反馈请求模型测试"""

    def test_valid_request(self):
        """测试有效请求"""
        req = FeedbackRequest(
            feedback_id="TEST001", content="北京温度不准", location="北京", time="2024-01-15"
        )
        assert req.feedback_id == "TEST001"
        assert req.content == "北京温度不准"
        assert req.location == "北京"
        assert req.time == "2024-01-15"

    def test_minimal_request(self):
        """测试最小请求（只有必填字段）"""
        req = FeedbackRequest(feedback_id="TEST002", content="温度不准")
        assert req.feedback_id == "TEST002"
        assert req.content == "温度不准"
        assert req.location is None
        assert req.time is None

    def test_missing_required_field(self):
        """测试缺少必填字段"""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(content="温度不准")
        assert "feedback_id" in str(exc_info.value)

    def test_missing_content(self):
        """测试缺少内容"""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(feedback_id="TEST003")
        assert "content" in str(exc_info.value)

    def test_optional_fields(self):
        """测试可选字段"""
        req = FeedbackRequest(
            feedback_id="TEST004", content="测试", user_id="USER001", source="APP"
        )
        assert req.user_id == "USER001"
        assert req.source == "APP"

    def test_field_types(self):
        """测试字段类型"""
        req = FeedbackRequest(
            feedback_id="TEST005",
            content="测试",
            time="2024-01-15 10:00:00",
            location="北京",
            user_id="USER001",
            source="WEB",
        )
        assert isinstance(req.feedback_id, str)
        assert isinstance(req.content, str)
        assert isinstance(req.time, str)
        assert isinstance(req.location, str)


# ============ WeatherData 测试 ============


@pytest.mark.unit
class TestWeatherData:
    """实况气象数据模型测试"""

    def test_valid_weather_data(self):
        """测试有效气象数据"""
        data = WeatherData(
            city_id="101010100",
            city_name="北京",
            temperature=25.0,
            humidity=60,
            wind_speed=3.5,
            weather_zh="晴",
        )
        assert data.city_id == "101010100"
        assert data.temperature == 25.0
        assert data.humidity == 60

    def test_optional_fields(self):
        """测试可选字段"""
        data = WeatherData()
        assert data.city_id is None
        assert data.temperature is None
        assert data.humidity is None

    def test_partial_data(self):
        """测试部分数据"""
        data = WeatherData(city_name="上海", temperature=28.5)
        assert data.city_name == "上海"
        assert data.temperature == 28.5
        assert data.humidity is None

    def test_field_validation(self):
        """测试字段验证"""
        # 温度可以是负数
        data = WeatherData(temperature=-10.5)
        assert data.temperature == -10.5

        # 湿度可以是0
        data = WeatherData(humidity=0)
        assert data.humidity == 0

        # 风速可以是0
        data = WeatherData(wind_speed=0)
        assert data.wind_speed == 0


# ============ HourlyData 测试 ============


@pytest.mark.unit
class TestHourlyData:
    """逐时预报数据模型测试"""

    def test_valid_hourly_data(self):
        """测试有效逐时数据"""
        data = HourlyData(
            city_id="101010100",
            predict_time="2024-01-15 10:00:00",
            temperature=22.0,
            humidity=55,
            wind_speed=4.0,
            weather_zh="多云",
        )
        assert data.city_id == "101010100"
        assert data.predict_time == "2024-01-15 10:00:00"
        assert data.temperature == 22.0

    def test_precipitation_fields(self):
        """测试降水相关字段"""
        data = HourlyData(pop=80.0, precipitation=5.2)
        assert data.pop == 80.0
        assert data.precipitation == 5.2

    def test_empty_data(self):
        """测试空数据"""
        data = HourlyData()
        assert data.city_id is None
        assert data.temperature is None


# ============ ForecastData 测试 ============


@pytest.mark.unit
class TestForecastData:
    """逐天预报数据模型测试"""

    def test_valid_forecast_data(self):
        """测试有效预报数据"""
        data = ForecastData(
            city_id="101010100",
            predict_date="2024-01-15",
            temp_high=5.0,
            temp_low=-3.0,
            weather_day="晴",
            weather_night="多云",
        )
        assert data.city_id == "101010100"
        assert data.predict_date == "2024-01-15"
        assert data.temp_high == 5.0
        assert data.temp_low == -3.0

    def test_temperature_range(self):
        """测试温度范围"""
        data = ForecastData(temp_high=30.0, temp_low=20.0)
        assert data.temp_high > data.temp_low

    def test_weather_fields(self):
        """测试天气字段"""
        data = ForecastData(weather_day="晴", weather_night="阴")
        assert data.weather_day == "晴"
        assert data.weather_night == "阴"

    def test_empty_forecast(self):
        """测试空预报"""
        data = ForecastData()
        assert data.city_id is None
        assert data.temp_high is None
        assert data.temp_low is None


# ============ FeelsLikeResult 测试 ============


@pytest.mark.unit
class TestFeelsLikeResult:
    """体感温度结果模型测试"""

    def test_valid_result(self):
        """测试有效结果"""
        result = FeelsLikeResult(feels_like=27.5, comfort="舒适", description="体感温度适中")
        assert result.feels_like == 27.5
        assert result.comfort == "舒适"
        assert result.description == "体感温度适中"

    def test_cold_scenario(self):
        """测试寒冷场景"""
        result = FeelsLikeResult(feels_like=-12.0, comfort="寒冷", description="体感温度很低")
        assert result.feels_like < 0
        assert result.comfort == "寒冷"

    def test_hot_scenario(self):
        """测试炎热场景"""
        result = FeelsLikeResult(feels_like=42.0, comfort="酷热", description="体感温度很高")
        assert result.feels_like > 40
        assert result.comfort == "酷热"

    def test_required_fields(self):
        """测试必填字段"""
        result = FeelsLikeResult(feels_like=20.0, comfort="舒适", description="正常")
        assert result.feels_like == 20.0
        assert result.comfort == "舒适"
        assert result.description == "正常"


# ============ 模型序列化测试 ============


@pytest.mark.unit
class TestModelSerialization:
    """模型序列化测试"""

    def test_feedback_request_dict(self):
        """测试FeedbackRequest转字典"""
        req = FeedbackRequest(feedback_id="TEST001", content="测试", location="北京")
        data = req.model_dump()
        assert isinstance(data, dict)
        assert data["feedback_id"] == "TEST001"
        assert data["content"] == "测试"

    def test_weather_data_dict(self):
        """测试WeatherData转字典"""
        data = WeatherData(city_name="北京", temperature=25.0)
        result = data.model_dump()
        assert isinstance(result, dict)
        assert result["city_name"] == "北京"

    def test_model_json(self):
        """测试模型转JSON"""
        req = FeedbackRequest(feedback_id="TEST001", content="测试")
        json_str = req.model_dump_json()
        assert isinstance(json_str, str)
        assert "TEST001" in json_str
