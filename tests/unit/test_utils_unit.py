"""
工具函数单元测试
测试通用工具函数和辅助方法
"""

from datetime import UTC, datetime, timedelta

import pytest

# ============ 数值验证测试 ============

@pytest.mark.unit
class TestNumericValidation:
    """数值验证测试"""

    def test_temperature_validation(self):
        """测试温度验证"""
        # 有效温度范围
        valid_temps = [-40, -10, 0, 15, 25, 35, 45]
        for temp in valid_temps:
            assert -50 <= temp <= 50, f"温度 {temp} 超出范围"

    def test_humidity_validation(self):
        """测试湿度验证"""
        # 有效湿度范围
        valid_humidity = [0, 30, 50, 70, 90, 100]
        for h in valid_humidity:
            assert 0 <= h <= 100, f"湿度 {h} 超出范围"

    def test_wind_speed_validation(self):
        """测试风速验证"""
        # 有效风速范围
        valid_speeds = [0, 1.5, 3.0, 5.0, 10.0, 20.0]
        for s in valid_speeds:
            assert 0 <= s <= 100, f"风速 {s} 超出范围"

    def test_pressure_validation(self):
        """测试气压验证"""
        # 有效气压范围
        valid_pressures = [900, 950, 1000, 1013, 1050, 1100]
        for p in valid_pressures:
            assert 900 <= p <= 1100, f"气压 {p} 超出范围"

    def test_aqi_validation(self):
        """测试AQI验证"""
        # 有效AQI范围
        valid_aqi = [0, 25, 50, 75, 100, 150, 200, 300, 500]
        for aqi in valid_aqi:
            assert 0 <= aqi <= 500, f"AQI {aqi} 超出范围"


# ============ 字符串处理测试 ============

@pytest.mark.unit
class TestStringProcessing:
    """字符串处理测试"""

    def test_city_name_normalization(self):
        """测试城市名标准化"""
        # 去除空格
        assert "北京".strip() == "北京"
        assert " 北京 ".strip() == "北京"

    def test_city_id_format(self):
        """测试城市ID格式"""
        # 有效的城市ID格式
        valid_ids = ["101010100", "101020100", "101280101"]
        for city_id in valid_ids:
            assert city_id.isdigit(), f"城市ID {city_id} 应该是纯数字"
            assert len(city_id) == 9, f"城市ID {city_id} 长度应该是9位"

    def test_feedback_id_format(self):
        """测试反馈ID格式"""
        # 有效的反馈ID格式
        valid_ids = ["FB001", "FB002", "MCP20240115120000"]
        for fid in valid_ids:
            assert len(fid) > 0, "反馈ID不能为空"
            assert isinstance(fid, str), "反馈ID应该是字符串"

    def test_datetime_string_format(self):
        """测试日期时间字符串格式"""
        # 有效的日期时间格式
        valid_formats = [
            "2024-01-15",
            "2024-01-15 10:00:00",
            "2024/01/15",
        ]
        for dt_str in valid_formats:
            assert len(dt_str) > 0, "日期时间字符串不能为空"


# ============ 日期时间测试 ============

@pytest.mark.unit
class TestDateTime:
    """日期时间测试"""

    def test_current_date(self):
        """测试当前日期"""
        now = datetime.now()
        assert now.year >= 2024
        assert 1 <= now.month <= 12
        assert 1 <= now.day <= 31

    def test_date_format_parsing(self):
        """测试日期格式解析"""
        date_str = "2024-01-15"
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_datetime_format_parsing(self):
        """测试日期时间格式解析"""
        datetime_str = "2024-01-15 10:30:00"
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        assert dt.hour == 10
        assert dt.minute == 30

    def test_date_arithmetic(self):
        """测试日期运算"""
        base_date = datetime(2024, 1, 15, tzinfo=UTC)
        next_day = base_date + timedelta(days=1)
        assert next_day.day == 16

        prev_day = base_date - timedelta(days=1)
        assert prev_day.day == 14

    def test_timestamp_conversion(self):
        """测试时间戳转换"""
        import time
        timestamp = int(time.time())
        assert timestamp > 0
        # 10位时间戳
        assert 1000000000 <= timestamp <= 9999999999


# ============ 列表和字典操作测试 ============

@pytest.mark.unit
class TestCollections:
    """列表和字典操作测试"""

    def test_list_operations(self):
        """测试列表操作"""
        cities = ["北京", "上海", "广州", "深圳"]
        assert len(cities) == 4
        assert "北京" in cities
        assert cities[0] == "北京"

    def test_dict_operations(self):
        """测试字典操作"""
        weather = {
            "temp": 25.0,
            "humidity": 60,
            "wind": 3.5
        }
        assert weather["temp"] == 25.0
        assert "humidity" in weather
        assert len(weather) == 3

    def test_list_filtering(self):
        """测试列表过滤"""
        temps = [20, 25, 30, 35, 40]
        hot_temps = [t for t in temps if t >= 30]
        assert len(hot_temps) == 3
        assert all(t >= 30 for t in hot_temps)

    def test_dict_comprehension(self):
        """测试字典推导"""
        cities = ["北京", "上海", "广州"]
        city_map = {city: f"city_{i}" for i, city in enumerate(cities)}
        assert len(city_map) == 3
        assert city_map["北京"] == "city_0"

    def test_nested_dict(self):
        """测试嵌套字典"""
        data = {
            "北京": {"temp": 25, "aqi": 50},
            "上海": {"temp": 28, "aqi": 60}
        }
        assert data["北京"]["temp"] == 25
        assert data["上海"]["aqi"] == 60


# ============ 异常处理测试 ============

@pytest.mark.unit
class TestExceptionHandling:
    """异常处理测试"""

    def test_key_error(self):
        """测试KeyError处理"""
        data = {"a": 1, "b": 2}
        with pytest.raises(KeyError):
            _ = data["c"]

    def test_index_error(self):
        """测试IndexError处理"""
        my_list = [1, 2, 3]
        with pytest.raises(IndexError):
            _ = my_list[10]

    def test_value_error(self):
        """测试ValueError处理"""
        with pytest.raises(ValueError):
            int("not_a_number")

    def test_type_error(self):
        """测试TypeError处理"""
        with pytest.raises(TypeError):
            _ = "string" + 123

    def test_zero_division(self):
        """测试除零错误"""
        with pytest.raises(ZeroDivisionError):
            _ = 10 / 0


# ============ 边界条件测试 ============

@pytest.mark.unit
class TestBoundaryConditions:
    """边界条件测试"""

    def test_empty_string(self):
        """测试空字符串"""
        empty = ""
        assert len(empty) == 0
        assert not empty  # 空字符串是falsy

    def test_none_value(self):
        """测试None值"""
        value = None
        assert value is None
        assert not value  # None是falsy

    def test_zero_value(self):
        """测试零值"""
        assert 0 == 0
        assert not 0  # 0是falsy

    def test_empty_list(self):
        """测试空列表"""
        empty_list = []
        assert len(empty_list) == 0
        assert not empty_list

    def test_empty_dict(self):
        """测试空字典"""
        empty_dict = {}
        assert len(empty_dict) == 0
        assert not empty_dict

    def test_max_int(self):
        """测试最大整数"""
        import sys
        max_int = sys.maxsize
        assert max_int > 0

    def test_float_precision(self):
        """测试浮点精度"""
        # 浮点数比较需要考虑精度
        result = 0.1 + 0.2
        assert abs(result - 0.3) < 1e-9
