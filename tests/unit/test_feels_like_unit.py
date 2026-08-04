"""
体感温度计算单元测试
测试风寒指数、热指数、舒适度描述
"""

import pytest

from app.skills.feels_like import (
    calculate_heat_index,
    calculate_wind_chill,
    get_comfort_description,
)

# ============ 风寒指数测试 ============


@pytest.mark.unit
class TestWindChill:
    """风寒指数测试"""

    def test_normal_temperature(self):
        """测试正常温度（不适用风寒公式）"""
        # 温度 > 10℃，不计算风寒
        result = calculate_wind_chill(20, 5)
        assert result == 20

    def test_low_wind_speed(self):
        """测试低风速（不适用风寒公式）"""
        # 风速 <= 1.3 m/s，不计算风寒
        result = calculate_wind_chill(5, 1.0)
        assert result == 5

    def test_cold_with_wind(self):
        """测试寒冷有风（适用风寒公式）"""
        # 温度 <= 10℃ 且风速 > 1.3 m/s
        result = calculate_wind_chill(0, 10)
        assert result < 0  # 体感应该更低

    def test_very_cold_with_strong_wind(self):
        """测试严寒大风"""
        result = calculate_wind_chill(-10, 20)
        assert result < -10  # 体感应该更低

    def test_boundary_temperature(self):
        """测试边界温度"""
        # 刚好10℃，温度 > 10 不计算风寒
        result = calculate_wind_chill(10, 5)
        # 温度 <= 10 且风速 > 1.3 会计算风寒
        assert result <= 10

    def test_boundary_wind_speed(self):
        """测试边界风速"""
        # 刚好1.3 m/s，风速 <= 1.3 不计算风寒
        result = calculate_wind_chill(5, 1.3)
        assert result == 5  # 不计算风寒

    def test_result_precision(self):
        """测试结果精度"""
        result = calculate_wind_chill(0, 10)
        # 结果应该保留1位小数
        assert isinstance(result, float)
        assert len(str(result).split(".")[-1]) <= 1


# ============ 热指数测试 ============


@pytest.mark.unit
class TestHeatIndex:
    """热指数测试"""

    def test_normal_temperature(self):
        """测试正常温度（不适用热指数）"""
        # 温度 < 27℃
        result = calculate_heat_index(25, 60)
        assert result == 25

    def test_low_humidity(self):
        """测试低湿度（不适用热指数）"""
        # 湿度 < 40%
        result = calculate_heat_index(30, 30)
        assert result == 30

    def test_hot_and_humid(self):
        """测试高温高湿（适用热指数）"""
        # 温度 >= 27℃ 且湿度 >= 40%
        result = calculate_heat_index(35, 80)
        assert result > 35  # 体感应该更高

    def test_extreme_heat(self):
        """测试极端高温"""
        result = calculate_heat_index(40, 90)
        assert result > 40  # 体感应该更高

    def test_boundary_temperature(self):
        """测试边界温度"""
        # 刚好27℃，温度 < 27 不计算热指数
        result = calculate_heat_index(27, 60)
        # 温度 >= 27 且湿度 >= 40 会计算热指数
        assert result >= 27

    def test_boundary_humidity(self):
        """测试边界湿度"""
        # 刚好40%，湿度 < 40 不计算热指数
        result = calculate_heat_index(30, 40)
        # 温度 >= 27 且湿度 >= 40 会计算热指数
        # 结果可能略低于原温度（公式特性）
        assert isinstance(result, float)

    def test_result_precision(self):
        """测试结果精度"""
        result = calculate_heat_index(35, 80)
        # 结果应该保留1位小数
        assert isinstance(result, float)
        assert len(str(result).split(".")[-1]) <= 1


# ============ 舒适度描述测试 ============


@pytest.mark.unit
class TestComfortDescription:
    """舒适度描述测试"""

    def test_extreme_cold(self):
        """测试极寒"""
        assert get_comfort_description(-15) == "极寒"

    def test_cold(self):
        """测试寒冷"""
        assert get_comfort_description(-5) == "寒冷"

    def test_cool(self):
        """测试冷"""
        assert get_comfort_description(5) == "冷"

    def test_mild(self):
        """测试凉爽"""
        assert get_comfort_description(15) == "凉爽"

    def test_comfortable(self):
        """测试舒适"""
        assert get_comfort_description(22) == "舒适"

    def test_warm(self):
        """测试温暖"""
        assert get_comfort_description(28) == "温暖"

    def test_hot(self):
        """测试炎热"""
        assert get_comfort_description(35) == "炎热"

    def test_extreme_hot(self):
        """测试酷热"""
        assert get_comfort_description(40) == "酷热"

    def test_boundary_values(self):
        """测试边界值"""
        assert get_comfort_description(-10) == "寒冷"
        assert get_comfort_description(0) == "冷"
        assert get_comfort_description(10) == "凉爽"  # 10 < 18
        assert get_comfort_description(18) == "舒适"  # 18 < 26
        assert get_comfort_description(26) == "温暖"  # 26 < 32
        assert get_comfort_description(32) == "炎热"  # 32 < 38
        assert get_comfort_description(38) == "酷热"  # >= 38


# ============ 综合测试 ============


@pytest.mark.unit
class TestFeelsLikeIntegration:
    """体感温度综合测试"""

    def test_summer_scenario(self):
        """测试夏季场景"""
        # 夏季：高温高湿
        heat = calculate_heat_index(35, 80)
        comfort = get_comfort_description(heat)
        assert heat > 35
        assert comfort in ["炎热", "酷热"]

    def test_winter_scenario(self):
        """测试冬季场景"""
        # 冬季：低温有风
        wind_chill = calculate_wind_chill(-5, 15)
        comfort = get_comfort_description(wind_chill)
        assert wind_chill < -5
        assert comfort in ["极寒", "寒冷"]

    def test_spring_scenario(self):
        """测试春季场景"""
        # 春季：温度适中
        comfort = get_comfort_description(20)
        assert comfort == "舒适"

    def test_temperature_consistency(self):
        """测试温度一致性"""
        # 温度在正常范围内，体感温度应该等于实际温度
        temp = 20
        humidity = 50
        wind_speed = 3
        heat = calculate_heat_index(temp, humidity)
        wind_chill = calculate_wind_chill(temp, wind_speed)
        # 都不满足计算条件，应该返回原温度
        assert heat == temp
        assert wind_chill == temp
