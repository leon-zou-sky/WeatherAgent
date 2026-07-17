"""
数据抓取 + 解析
从北京局 v2 接口下载实况、逐时、逐天数据
"""

import time
import datetime
import logging

import httpx

from downloader.models import WeatherCondition, WeatherHourly, WeatherForecast
from app.skills.weather_codes import get_weather_name

logger = logging.getLogger(__name__)

# 风向角度 → 中文
DEGREE_LIST = [
    (337.5, 360, "北风"),
    (0, 22.5, "北风"),
    (22.5, 67.5, "东北风"),
    (67.5, 112.5, "东风"),
    (112.5, 157.5, "东南风"),
    (157.5, 202.5, "南风"),
    (202.5, 247.5, "西南风"),
    (247.5, 292.5, "西风"),
    (292.5, 337.5, "西北风"),
]


def degree_to_dir(degree: float) -> str:
    """角度转风向"""
    if degree == 360:
        return "北风"
    for low, high, direction in DEGREE_LIST:
        if low <= degree < high:
            return direction
    return "未知"


# ============ API 接口 ============

BASE_URL = "http://bjtqyb.com/moji"

API_PATHS = {
    "condition": "/observev2all/keys/{key}",
    "hourly": "/hoursv2all/keys/{key}",
    "forecast": "/forecastv2dall/keys/{key}",
}


def fetch_json(url: str, timeout: int = 30) -> dict | None:
    """请求接口，返回 JSON"""
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"接口返回异常: code={data.get('code')}, url={url}")
                return None
            return data
    except Exception as e:
        logger.error(f"请求失败: {url}, error={e}")
        return None


# ============ 实况数据解析 ============

def fetch_condition(api_key: str) -> list[WeatherCondition]:
    """抓取实况数据"""
    url = BASE_URL + API_PATHS["condition"].format(key=api_key)
    data = fetch_json(url)
    if not data or not data.get("data"):
        return []

    now_ts = int(time.time())
    results = []
    for item in data["data"]:
        try:
            row = WeatherCondition(
                city_id=item["cityId"],
                get_time=now_ts,
                update_time=item.get("lastUpdate"),
                temp=item.get("temp"),
                real_feel=item.get("atemp"),
                humidity=item.get("humidity"),
                wspd=item.get("speed"),
                wdir=degree_to_dir(float(item.get("degrees", 0))),
                wind_level=int(item.get("windgrade", 0)),
                weather_zh=get_weather_name(item.get("weather", "")),
                vis=item.get("visibility"),
                pressure=item.get("pressure"),
                mslp=item.get("seaPressure"),
                precip_1h=item.get("rainfall"),
                wind_degrees=item.get("degrees"),
            )
            results.append(row)
        except Exception as e:
            logger.warning(f"解析实况数据异常: {item.get('cityId')}, {e}")
    logger.info(f"实况数据: 抓取 {len(results)} 条")
    return results


# ============ 逐时预报解析 ============

def fetch_hourly(api_key: str) -> list[WeatherHourly]:
    """抓取逐时预报"""
    url = BASE_URL + API_PATHS["hourly"].format(key=api_key)
    data = fetch_json(url)
    if not data or not data.get("data"):
        return []

    now_ts = int(time.time())
    results = []
    for city_data in data["data"]:
        city_id = city_data.get("city_id")
        update_time = city_data.get("update_time")
        for fi in city_data.get("list", []):
            try:
                predict_time = fi["date_time"]
                dt = datetime.datetime.strptime(predict_time, "%Y-%m-%d %H:%M:%S")
                row = WeatherHourly(
                    city_id=city_id,
                    get_time=now_ts,
                    update_time=update_time,
                    predict_timestamp=int(dt.timestamp()),
                    predict_date=dt.strftime("%Y-%m-%d"),
                    predict_hour=dt.hour,
                    weather_zh=get_weather_name(fi.get("weather", "")),
                    temp=fi.get("temp"),
                    wdir=degree_to_dir(float(fi.get("degrees", 0))),
                    wspd=fi.get("speed"),
                    humidity=fi.get("humidity"),
                    wind_level=int(fi.get("windgrade", 0)),
                    wind_degrees=fi.get("degrees"),
                    pop=fi.get("rain_probability"),
                    qpf=fi.get("rainfall"),
                    snow=fi.get("snowfall"),
                    pressure=fi.get("pressure"),
                    vis=fi.get("visibility"),
                )
                results.append(row)
            except Exception as e:
                logger.warning(f"解析逐时数据异常: {city_id}, {e}")
    logger.info(f"逐时预报: 抓取 {len(results)} 条")
    return results


# ============ 逐天预报解析 ============

def fetch_forecast(api_key: str) -> list[WeatherForecast]:
    """抓取15天预报"""
    url = BASE_URL + API_PATHS["forecast"].format(key=api_key)
    data = fetch_json(url)
    if not data or not data.get("data"):
        return []

    now_ts = int(time.time())
    results = []
    for city_data in data["data"]:
        city_id = city_data.get("city_id")
        update_time = city_data.get("update_time")
        for fi in city_data.get("list", []):
            try:
                row = WeatherForecast(
                    city_id=city_id,
                    get_time=now_ts,
                    update_time=update_time,
                    predict_date=fi.get("date"),
                    temp_high=fi.get("max_temp"),
                    temp_low=fi.get("min_temp"),
                    weather_day=get_weather_name(fi.get("day_weather", "")),
                    weather_night=get_weather_name(fi.get("night_weather", "")),
                    wind_dir_day=degree_to_dir(float(fi.get("day_degrees", 0))),
                    wind_level_day=str(fi.get("day_windgrade", "")),
                    wind_dir_night=degree_to_dir(float(fi.get("night_degrees", 0))),
                    wind_level_night=str(fi.get("night_windgrade", "")),
                    sunrise=fi.get("sun_rise"),
                    sunset=fi.get("sun_set"),
                    humidity_day=fi.get("day_humidity"),
                    humidity_night=fi.get("night_humidity"),
                    wind_degrees_day=fi.get("day_degrees"),
                    wspd_day=fi.get("day_speed"),
                    wind_degrees_night=fi.get("night_degrees"),
                    wspd_night=fi.get("night_speed"),
                    pop_day=fi.get("day_rain_probability"),
                    pop_night=fi.get("night_rain_probability"),
                    pressure_day=fi.get("day_pressure"),
                    pressure_night=fi.get("night_pressure"),
                    mslp_day=fi.get("day_seaPressure"),
                    mslp_night=fi.get("night_seaPressure"),
                )
                results.append(row)
            except Exception as e:
                logger.warning(f"解析逐天数据异常: {city_id}, {e}")
    logger.info(f"逐天预报: 抓取 {len(results)} 条")
    return results
