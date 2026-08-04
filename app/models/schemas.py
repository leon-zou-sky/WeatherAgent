"""
Pydantic 数据模型 - 请求/响应 Schema
"""

from pydantic import BaseModel, Field

# ============ 请求模型 ============


class FeedbackRequest(BaseModel):
    """负反馈分析请求"""

    feedback_id: str = Field(..., description="反馈ID")
    content: str = Field(..., description="反馈内容")
    time: str | None = Field(None, description="反馈时间")
    location: str | None = Field(None, description="位置")
    user_id: str | None = Field(None, description="用户ID")
    source: str | None = Field(None, description="来源: APP/WEB/API")


class BatchAnalyzeRequest(BaseModel):
    """批量分析请求"""

    feedbacks: list[FeedbackRequest] = Field(..., description="反馈列表")


# ============ Skill 返回模型 ============


class DataSourceResult(BaseModel):
    """数据源检查结果"""

    status: str = Field(..., description="正常/异常")
    station_id: str | None = None
    data_quality: str | None = None
    coverage: bool | None = None
    detail: str | None = None


class PipelineStepResult(BaseModel):
    """链路单步检查结果"""

    status: str = Field(..., description="正常/异常")
    detail: str | None = None


class PipelineResult(BaseModel):
    """链路检查结果"""

    data_source: PipelineStepResult
    collection: PipelineStepResult
    processing: PipelineStepResult
    storage: PipelineStepResult
    publishing: PipelineStepResult


class WeatherData(BaseModel):
    """实况气象数据"""

    city_id: str | None = Field(None, description="城市编号")
    city_name: str | None = Field(None, description="城市名")
    temperature: float | None = Field(None, description="温度(℃)")
    real_feel: float | None = Field(None, description="体感温度(℃)")
    humidity: float | None = Field(None, description="相对湿度(%)")
    wind_speed: float | None = Field(None, description="风速(m/s)")
    wind_dir: str | None = Field(None, description="风向")
    wind_level: int | None = Field(None, description="风力等级")
    weather_zh: str | None = Field(None, description="天气现象")
    visibility: float | None = Field(None, description="能见度(km)")
    pressure: float | None = Field(None, description="气压(hPa)")
    precipitation: float | None = Field(None, description="1h降水量(mm)")
    update_time: str | None = Field(None, description="数据更新时间")


class HourlyData(BaseModel):
    """逐时预报数据"""

    city_id: str | None = None
    predict_time: str | None = Field(None, description="预报时间")
    temperature: float | None = Field(None, description="温度(℃)")
    humidity: float | None = Field(None, description="相对湿度(%)")
    wind_speed: float | None = Field(None, description="风速(m/s)")
    wind_dir: str | None = Field(None, description="风向")
    weather_zh: str | None = Field(None, description="天气现象")
    pop: float | None = Field(None, description="降水概率(%)")
    precipitation: float | None = Field(None, description="降水量(mm)")
    pressure: float | None = Field(None, description="气压(hPa)")
    visibility: float | None = Field(None, description="能见度(km)")


class ForecastData(BaseModel):
    """逐天预报数据"""

    city_id: str | None = None
    predict_date: str | None = Field(None, description="预报日期")
    temp_high: float | None = Field(None, description="最高温度(℃)")
    temp_low: float | None = Field(None, description="最低温度(℃)")
    weather_day: str | None = Field(None, description="白天天气")
    weather_night: str | None = Field(None, description="夜间天气")
    wind_dir_day: str | None = Field(None, description="白天风向")
    wind_level_day: str | None = Field(None, description="白天风力")
    wind_dir_night: str | None = Field(None, description="夜间风向")
    wind_level_night: str | None = Field(None, description="夜间风力")
    humidity_day: float | None = Field(None, description="白天湿度(%)")
    humidity_night: float | None = Field(None, description="夜间湿度(%)")
    pop_day: float | None = Field(None, description="白天降水概率(%)")
    pop_night: float | None = Field(None, description="夜间降水概率(%)")
    sunrise: str | None = Field(None, description="日出时间")
    sunset: str | None = Field(None, description="日落时间")


class AlertData(BaseModel):
    """预警数据"""

    has_alert: bool = Field(False, description="是否有预警")
    alert_type: str | None = None
    alert_level: str | None = None
    alert_time: str | None = None
    detail: str | None = None


class FeelsLikeResult(BaseModel):
    """体感温度结果"""

    feels_like: float = Field(..., description="体感温度(℃)")
    comfort: str = Field(..., description="舒适度描述")
    description: str = Field(..., description="详细说明")


class KnowledgeResult(BaseModel):
    """知识检索结果"""

    content: str
    solution: str | None = None
    score: float


# ============ 响应模型 ============


class AnalysisResult(BaseModel):
    """分析结果"""

    analysis_id: str
    feedback_type: str | None = None
    problem_location: str | None = None
    root_cause: str | None = None
    actual_data: WeatherData | None = None
    feels_like: FeelsLikeResult | None = None
    alert_data: AlertData | None = None
    meteorological_explanation: str | None = None
    suggestion: str | None = None
    reply_content: str | None = None


class AnalysisResponse(BaseModel):
    """分析接口响应"""

    code: int = 200
    message: str = "success"
    data: AnalysisResult | None = None


class BatchAnalysisResponse(BaseModel):
    """批量分析响应"""

    code: int = 200
    message: str = "success"
    data: dict | None = None


class AnalysisQueryResponse(BaseModel):
    """查询分析结果响应"""

    code: int = 200
    message: str = "success"
    data: AnalysisResult | None = None
