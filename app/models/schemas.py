"""
Pydantic 数据模型 - 请求/响应 Schema
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ============ 请求模型 ============

class FeedbackRequest(BaseModel):
    """负反馈分析请求"""
    feedback_id: str = Field(..., description="反馈ID")
    content: str = Field(..., description="反馈内容")
    time: Optional[str] = Field(None, description="反馈时间")
    location: Optional[str] = Field(None, description="位置")
    user_id: Optional[str] = Field(None, description="用户ID")
    source: Optional[str] = Field(None, description="来源: APP/WEB/API")


class BatchAnalyzeRequest(BaseModel):
    """批量分析请求"""
    feedbacks: list[FeedbackRequest] = Field(..., description="反馈列表")


# ============ Skill 返回模型 ============

class DataSourceResult(BaseModel):
    """数据源检查结果"""
    status: str = Field(..., description="正常/异常")
    station_id: Optional[str] = None
    data_quality: Optional[str] = None
    coverage: Optional[bool] = None
    detail: Optional[str] = None


class PipelineStepResult(BaseModel):
    """链路单步检查结果"""
    status: str = Field(..., description="正常/异常")
    detail: Optional[str] = None


class PipelineResult(BaseModel):
    """链路检查结果"""
    data_source: PipelineStepResult
    collection: PipelineStepResult
    processing: PipelineStepResult
    storage: PipelineStepResult
    publishing: PipelineStepResult


class WeatherData(BaseModel):
    """实况气象数据"""
    city_id: Optional[str] = Field(None, description="城市编号")
    city_name: Optional[str] = Field(None, description="城市名")
    temperature: Optional[float] = Field(None, description="温度(℃)")
    real_feel: Optional[float] = Field(None, description="体感温度(℃)")
    humidity: Optional[float] = Field(None, description="相对湿度(%)")
    wind_speed: Optional[float] = Field(None, description="风速(m/s)")
    wind_dir: Optional[str] = Field(None, description="风向")
    wind_level: Optional[int] = Field(None, description="风力等级")
    weather_zh: Optional[str] = Field(None, description="天气现象")
    visibility: Optional[float] = Field(None, description="能见度(km)")
    pressure: Optional[float] = Field(None, description="气压(hPa)")
    precipitation: Optional[float] = Field(None, description="1h降水量(mm)")
    update_time: Optional[str] = Field(None, description="数据更新时间")


class HourlyData(BaseModel):
    """逐时预报数据"""
    city_id: Optional[str] = None
    predict_time: Optional[str] = Field(None, description="预报时间")
    temperature: Optional[float] = Field(None, description="温度(℃)")
    humidity: Optional[float] = Field(None, description="相对湿度(%)")
    wind_speed: Optional[float] = Field(None, description="风速(m/s)")
    wind_dir: Optional[str] = Field(None, description="风向")
    weather_zh: Optional[str] = Field(None, description="天气现象")
    pop: Optional[float] = Field(None, description="降水概率(%)")
    precipitation: Optional[float] = Field(None, description="降水量(mm)")
    pressure: Optional[float] = Field(None, description="气压(hPa)")
    visibility: Optional[float] = Field(None, description="能见度(km)")


class ForecastData(BaseModel):
    """逐天预报数据"""
    city_id: Optional[str] = None
    predict_date: Optional[str] = Field(None, description="预报日期")
    temp_high: Optional[float] = Field(None, description="最高温度(℃)")
    temp_low: Optional[float] = Field(None, description="最低温度(℃)")
    weather_day: Optional[str] = Field(None, description="白天天气")
    weather_night: Optional[str] = Field(None, description="夜间天气")
    wind_dir_day: Optional[str] = Field(None, description="白天风向")
    wind_level_day: Optional[str] = Field(None, description="白天风力")
    wind_dir_night: Optional[str] = Field(None, description="夜间风向")
    wind_level_night: Optional[str] = Field(None, description="夜间风力")
    humidity_day: Optional[float] = Field(None, description="白天湿度(%)")
    humidity_night: Optional[float] = Field(None, description="夜间湿度(%)")
    pop_day: Optional[float] = Field(None, description="白天降水概率(%)")
    pop_night: Optional[float] = Field(None, description="夜间降水概率(%)")
    sunrise: Optional[str] = Field(None, description="日出时间")
    sunset: Optional[str] = Field(None, description="日落时间")


class AlertData(BaseModel):
    """预警数据"""
    has_alert: bool = Field(False, description="是否有预警")
    alert_type: Optional[str] = None
    alert_level: Optional[str] = None
    alert_time: Optional[str] = None
    detail: Optional[str] = None


class FeelsLikeResult(BaseModel):
    """体感温度结果"""
    feels_like: float = Field(..., description="体感温度(℃)")
    comfort: str = Field(..., description="舒适度描述")
    description: str = Field(..., description="详细说明")


class KnowledgeResult(BaseModel):
    """知识检索结果"""
    content: str
    solution: Optional[str] = None
    score: float


# ============ 响应模型 ============

class AnalysisResult(BaseModel):
    """分析结果"""
    analysis_id: str
    feedback_type: Optional[str] = None
    problem_location: Optional[str] = None
    root_cause: Optional[str] = None
    actual_data: Optional[WeatherData] = None
    feels_like: Optional[FeelsLikeResult] = None
    alert_data: Optional[AlertData] = None
    meteorological_explanation: Optional[str] = None
    suggestion: Optional[str] = None
    reply_content: Optional[str] = None


class AnalysisResponse(BaseModel):
    """分析接口响应"""
    code: int = 200
    message: str = "success"
    data: Optional[AnalysisResult] = None


class BatchAnalysisResponse(BaseModel):
    """批量分析响应"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class AnalysisQueryResponse(BaseModel):
    """查询分析结果响应"""
    code: int = 200
    message: str = "success"
    data: Optional[AnalysisResult] = None
