"""
数据库模型 - 5张表
city          城市基础信息
weather_cn    实况数据（每10分钟）
weather_hh    逐时预报（每小时）
weather_ff    逐天预报（15天）
alert_data    预警数据
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class City(Base):
    """城市表"""

    __tablename__ = "city"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(20), nullable=False, unique=True, comment="北京局城市编号 如110100")
    city_name = Column(String(64), comment="城市名")
    longitude = Column(Float, comment="经度")
    latitude = Column(Float, comment="纬度")
    province = Column(String(32), comment="省份")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WeatherCondition(Base):
    """实况数据表（condition_beijing_v2）"""

    __tablename__ = "weather_cn"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(String(20), nullable=False, comment="城市编号")
    get_time = Column(Integer, comment="采集时间戳")
    update_time = Column(String(32), comment="数据更新时间")
    temp = Column(Float, comment="温度(℃)")
    real_feel = Column(Float, comment="体感温度(℃)")
    humidity = Column(Float, comment="相对湿度(%)")
    wspd = Column(Float, comment="风速(m/s)")
    wdir = Column(String(8), comment="风向")
    wind_level = Column(Integer, comment="风力等级")
    weather_zh = Column(String(32), comment="天气现象")
    vis = Column(Float, comment="能见度(km)")
    pressure = Column(Float, comment="气压(hPa)")
    mslp = Column(Float, comment="海平面气压(hPa)")
    precip_1h = Column(Float, comment="1小时降水量(mm)")
    wind_degrees = Column(Float, comment="风向角度")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_cn_city_time", "city_id", "get_time"),)


class WeatherHourly(Base):
    """逐时预报表（hourly_beijing_v2）"""

    __tablename__ = "weather_hh"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(String(20), nullable=False, comment="城市编号")
    get_time = Column(Integer, comment="采集时间戳")
    update_time = Column(String(32), comment="数据更新时间")
    predict_timestamp = Column(Integer, comment="预报时间戳")
    predict_date = Column(String(32), comment="预报日期")
    predict_hour = Column(Integer, comment="预报小时")
    weather_zh = Column(String(32), comment="天气现象")
    temp = Column(Float, comment="温度(℃)")
    wdir = Column(String(8), comment="风向")
    wspd = Column(Float, comment="风速(m/s)")
    humidity = Column(Float, comment="相对湿度(%)")
    wind_level = Column(Integer, comment="风力等级")
    wind_degrees = Column(Float, comment="风向角度")
    pop = Column(Float, comment="降水概率(%)")
    qpf = Column(Float, comment="降水量(mm)")
    snow = Column(Float, comment="降雪量(mm)")
    pressure = Column(Float, comment="气压(hPa)")
    vis = Column(Float, comment="能见度(km)")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_hh_city_time", "city_id", "predict_timestamp"),)


class WeatherForecast(Base):
    """逐天预报表（forecast_beijing_v2）"""

    __tablename__ = "weather_ff"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(String(20), nullable=False, comment="城市编号")
    get_time = Column(Integer, comment="采集时间戳")
    update_time = Column(String(32), comment="数据更新时间")
    predict_date = Column(String(32), comment="预报日期")
    temp_high = Column(Float, comment="最高温度(℃)")
    temp_low = Column(Float, comment="最低温度(℃)")
    weather_day = Column(String(16), comment="白天天气ID")
    weather_night = Column(String(16), comment="夜间天气ID")
    wind_dir_day = Column(String(8), comment="白天风向")
    wind_level_day = Column(String(8), comment="白天风力")
    wind_dir_night = Column(String(8), comment="夜间风向")
    wind_level_night = Column(String(8), comment="夜间风力")
    sunrise = Column(String(32), comment="日出时间")
    sunset = Column(String(32), comment="日落时间")
    humidity_day = Column(Float, comment="白天湿度(%)")
    humidity_night = Column(Float, comment="夜间湿度(%)")
    wind_degrees_day = Column(Float, comment="白天风向角度")
    wspd_day = Column(Float, comment="白天风速(m/s)")
    wind_degrees_night = Column(Float, comment="夜间风向角度")
    wspd_night = Column(Float, comment="夜间风速(m/s)")
    pop_day = Column(Float, comment="白天降水概率(%)")
    pop_night = Column(Float, comment="夜间降水概率(%)")
    pressure_day = Column(Float, comment="白天气压(hPa)")
    pressure_night = Column(Float, comment="夜间气压(hPa)")
    mslp_day = Column(Float, comment="白天海平面气压(hPa)")
    mslp_night = Column(Float, comment="夜间海平面气压(hPa)")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_ff_city_date", "city_id", "predict_date"),)


class AlertData(Base):
    """预警数据表"""

    __tablename__ = "alert_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_id = Column(String(64), nullable=False, comment="预警ID")
    city_id = Column(String(20), nullable=False, comment="城市编号")
    city_name = Column(String(32), comment="城市名")
    alert_type = Column(String(32), comment="预警类型（高温/暴雨/台风等）")
    alert_level = Column(String(16), comment="预警级别（蓝/黄/橙/红）")
    title = Column(String(128), comment="预警标题")
    content = Column(Text, comment="预警内容")
    start_time = Column(String(32), comment="预警开始时间")
    end_time = Column(String(32), comment="预警结束时间")
    update_time = Column(String(32), comment="数据更新时间")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_alert_city", "city_id"),
        Index("idx_alert_time", "start_time", "end_time"),
        Index("idx_alert_type", "alert_type"),
        UniqueConstraint("alert_id", name="uq_alert_id"),
    )


class AnalysisResult(Base):
    """分析结果表"""

    __tablename__ = "analysis_result"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(String(64), nullable=False, unique=True, comment="分析ID")
    feedback_id = Column(String(64), nullable=False, comment="反馈ID")
    feedback_content = Column(Text, comment="反馈内容")
    location = Column(String(64), comment="位置")
    user_id = Column(String(64), comment="用户ID")
    source = Column(String(32), comment="来源")

    # 分析结果
    feedback_type = Column(String(32), comment="问题类型")
    root_cause = Column(Text, comment="问题根因（内部）")
    meteorological_explanation = Column(Text, comment="气象解释")
    suggestion = Column(Text, comment="改进建议（内部）")
    reply_content = Column(Text, comment="回复内容（给用户）")

    # 实况数据快照
    actual_temp = Column(Float, comment="实际温度")
    actual_humidity = Column(Float, comment="实际湿度")
    actual_wind_speed = Column(Float, comment="实际风速")
    feels_like = Column(Float, comment="体感温度")

    # 状态管理
    status = Column(String(16), default="pending", comment="状态: pending/approved/rejected/sent")
    reviewer = Column(String(64), comment="审核人")
    review_time = Column(DateTime, comment="审核时间")
    review_comment = Column(Text, comment="审核意见")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_ar_status", "status"),
        Index("idx_ar_feedback", "feedback_id"),
        Index("idx_ar_created", "created_at"),
    )


class AQICity(Base):
    """城市 AQI 实况数据表"""

    __tablename__ = "aqi_city"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(String(20), nullable=False, comment="城市ID（在意空气ID）")
    city_name = Column(String(64), comment="城市名称")
    update_time = Column(String(32), comment="数据更新时间")
    aqi = Column(Integer, comment="AQI指数")
    pm25 = Column(Float, comment="PM2.5(μg/m³)")
    pm25_iaqi = Column(Integer, comment="PM2.5分指数")
    pm10 = Column(Float, comment="PM10(μg/m³)")
    pm10_iaqi = Column(Integer, comment="PM10分指数")
    so2 = Column(Float, comment="SO2(μg/m³)")
    so2_iaqi = Column(Integer, comment="SO2分指数")
    no2 = Column(Float, comment="NO2(μg/m³)")
    no2_iaqi = Column(Integer, comment="NO2分指数")
    o3 = Column(Float, comment="O3(μg/m³)")
    o3_iaqi = Column(Integer, comment="O3分指数")
    co = Column(Float, comment="CO(mg/m³)")
    co_iaqi = Column(Integer, comment="CO分指数")
    source = Column(String(32), default="air_matters", comment="数据源")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_aqi_city_time", "city_id", "update_time"),
        Index("idx_aqi_city_name", "city_name"),
    )


class AQIStation(Base):
    """监测站 AQI 实况数据表"""

    __tablename__ = "aqi_station"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    station_code = Column(String(32), nullable=False, comment="监测站编码")
    station_name = Column(String(64), comment="监测站名称")
    city_id = Column(String(20), comment="所属城市ID")
    city_name = Column(String(64), comment="所属城市名称")
    update_time = Column(String(32), comment="数据更新时间")
    aqi = Column(Integer, comment="AQI指数")
    pm25 = Column(Float, comment="PM2.5(μg/m³)")
    pm25_iaqi = Column(Integer, comment="PM2.5分指数")
    pm10 = Column(Float, comment="PM10(μg/m³)")
    pm10_iaqi = Column(Integer, comment="PM10分指数")
    so2 = Column(Float, comment="SO2(μg/m³)")
    so2_iaqi = Column(Integer, comment="SO2分指数")
    no2 = Column(Float, comment="NO2(μg/m³)")
    no2_iaqi = Column(Integer, comment="NO2分指数")
    o3 = Column(Float, comment="O3(μg/m³)")
    o3_iaqi = Column(Integer, comment="O3分指数")
    co = Column(Float, comment="CO(mg/m³)")
    co_iaqi = Column(Integer, comment="CO分指数")
    source = Column(String(32), default="air_matters", comment="数据源")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_station_code", "station_code"),
        Index("idx_station_city", "city_id"),
    )


class WeatherIconV2(Base):
    """天气现象映射表 v2（完整版）"""

    __tablename__ = "weather_icon_v2"

    id = Column(Integer, primary_key=True, autoincrement=False, comment="主键ID")
    weather_code = Column(Integer, comment="天气代码")
    bg_code = Column(Integer, comment="背景代码")
    icon_day = Column(Integer, comment="白天图标")
    icon_night = Column(Integer, comment="夜间图标")
    condition_zh = Column(String(64), comment="天气现象中文")
    condition_en = Column(String(128), comment="天气现象英文")
    condition_enin = Column(String(128), comment="天气现象英文(印度)")
    condition_enph = Column(String(128), comment="天气现象英文(菲律宾)")
    condition_tw = Column(String(64), comment="天气现象繁体(台湾)")
    condition_hk = Column(String(64), comment="天气现象繁体(香港)")
    condition_es = Column(String(128), comment="天气现象西班牙语")
    condition_pt = Column(String(128), comment="天气现象葡萄牙语")
    condition_ru = Column(String(128), comment="天气现象俄语")
    condition_fr = Column(String(128), comment="天气现象法语")
    condition_de = Column(String(128), comment="天气现象德语")
    condition_ar = Column(String(128), comment="天气现象阿拉伯语")
    condition_ko = Column(String(128), comment="天气现象韩语")
    condition_ja = Column(String(128), comment="天气现象日语")
    condition_hi = Column(String(128), comment="天气现象印地语")
    condition_te = Column(String(128), comment="天气现象泰卢固语")
    accu_icon = Column(Integer, comment="AccuWeather图标")
    accu_condition = Column(String(128), comment="AccuWeather天气现象")
    weathercn_icon1 = Column(String(64), comment="中国天气网图标1")
    weathercn_icon2 = Column(String(64), comment="中国天气网图标2")
    wunder_condition = Column(String(128), comment="WeatherUnderground天气现象")
    wunder_icon = Column(String(64), comment="WeatherUnderground图标")
    condition_kr = Column(String(128), comment="天气现象韩语(备用)")
    smartweather = Column(Integer, comment="SmartWeather代码")
    condition_tm = Column(String(128), comment="天气现象土库曼语")

    __table_args__ = (
        Index("idx_v2_weather_code", "weather_code"),
        Index("idx_v2_condition_zh", "condition_zh"),
    )


# ============ 数据库连接工具 ============


def get_engine(
    url: str = None, host="localhost", port=3306, user="root", password="", db="weather"
):
    if url is None:
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url, pool_size=5, pool_recycle=3600)


def create_tables(engine):
    """建表"""
    Base.metadata.create_all(engine)
    print("✅ 数据表创建完成")


def get_session(engine):
    """获取数据库 session"""
    Session = sessionmaker(bind=engine)
    return Session()
