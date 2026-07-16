"""
Skill 5: 体感温度计算
基于风寒指数和热指数计算体感温度
"""

import math
from app.models.schemas import FeelsLikeResult


def calculate_wind_chill(temperature: float, wind_speed: float) -> float:
    """
    计算风寒指数（Wind Chill）
    适用于温度 <= 10℃ 且风速 > 1.3 m/s 的情况
    公式：WC = 13.12 + 0.6215*T - 11.37*V^0.16 + 0.3965*T*V^0.16
    """
    if temperature > 10 or wind_speed <= 1.3:
        return temperature

    v_kmh = wind_speed * 3.6  # m/s → km/h
    wc = (
        13.12
        + 0.6215 * temperature
        - 11.37 * (v_kmh ** 0.16)
        + 0.3965 * temperature * (v_kmh ** 0.16)
    )
    return round(wc, 1)


def calculate_heat_index(temperature: float, humidity: float) -> float:
    """
    计算热指数（Heat Index）
    适用于温度 >= 27℃ 且湿度 >= 40% 的情况
    简化公式（Steadman 公式）
    """
    if temperature < 27 or humidity < 40:
        return temperature

    T = temperature
    RH = humidity

    hi = (
        -8.78469475556
        + 1.61139411 * T
        + 2.33854883889 * RH
        - 0.14611605 * T * RH
        - 0.012308094 * (T ** 2)
        - 0.0164248277778 * (RH ** 2)
        + 0.002211732 * (T ** 2) * RH
        + 0.00072546 * T * (RH ** 2)
        - 0.000003582 * (T ** 2) * (RH ** 2)
    )
    return round(hi, 1)


def get_comfort_description(feels_like: float) -> str:
    """根据体感温度返回舒适度描述"""
    if feels_like < -10:
        return "极寒"
    elif feels_like < 0:
        return "寒冷"
    elif feels_like < 10:
        return "冷"
    elif feels_like < 18:
        return "凉爽"
    elif feels_like < 26:
        return "舒适"
    elif feels_like < 32:
        return "温暖"
    elif feels_like < 38:
        return "炎热"
    else:
        return "酷热"


async def calculate_feels_like(
    temperature: float, humidity: float, wind_speed: float
) -> FeelsLikeResult:
    """
    计算体感温度

    Args:
        temperature: 实际温度（℃）
        humidity: 相对湿度（%）
        wind_speed: 风速（m/s）

    Returns:
        FeelsLikeResult: 体感温度结果
    """
    feels_like = temperature

    # 低温+大风 → 风寒效应
    if temperature <= 10 and wind_speed > 1.3:
        feels_like = calculate_wind_chill(temperature, wind_speed)
        explanation = f"低温+大风，风寒效应使体感温度降低至 {feels_like}℃"

    # 高温+高湿 → 热指数效应
    elif temperature >= 27 and humidity >= 40:
        feels_like = calculate_heat_index(temperature, humidity)
        explanation = f"高温+高湿，热指数使体感温度升高至 {feels_like}℃"

    else:
        feels_like = temperature
        explanation = f"实际温度 {temperature}℃，体感温度接近实际温度"

    comfort = get_comfort_description(feels_like)

    return FeelsLikeResult(
        feels_like=feels_like,
        comfort=comfort,
        description=explanation,
    )
