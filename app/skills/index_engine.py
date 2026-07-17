"""
生活指数规则引擎
从 travel_advice_service.py 提取，适配我们的数据格式
"""

import math
from dataclasses import dataclass, field


@dataclass
class WeatherInput:
    """天气输入数据"""
    city: str
    date: str
    temp_high: float        # 最高温
    temp_low: float         # 最低温
    humidity: float         # 湿度(%)
    wind_speed: float       # 风速(m/s)
    wind_level: int         # 风力等级
    condition: str          # 天气现象: 晴/多云/小雨...
    aqi: int = 50           # 空气质量指数
    uvi: int = 3            # 紫外线指数值
    latitude: float = 39.9  # 纬度（默认北京）
    month: int = 7          # 月份
    yesterday_temp_high: float = None  # 昨日最高温


@dataclass
class IndexResult:
    """单个指数结果"""
    name: str               # 指数名称
    level: str              # 等级文字
    score: int              # 1-5分（1最差/5最好）
    tip: str                # 建议文案
    risk_factors: list = field(default_factory=list)  # 风险因子


class IndexEngine:
    """生活指数计算引擎"""

    # 天气现象分类（来源：weather_icon 表）
    RAIN_WEATHER = ['小雨', '中雨', '大雨', '暴雨', '阵雨', '雷阵雨', '小到中雨',
                    '大到暴雨', '大暴雨', '特大暴雨', '雨夹雪', '雷阵雨伴有冰雹']
    SNOW_WEATHER = ['小雪', '中雪', '大雪', '暴雪', '阵雪', '小到中雪']
    SAND_WEATHER = ['扬沙', '浮尘', '沙尘暴', '强沙尘暴']
    SMOG_WEATHER = ['雾', '霾']

    def calc_real_feel(self, w: WeatherInput) -> float:
        """计算体感温度"""
        ts = 22.7 * (1.0 - 0.3 * math.sin((w.latitude - 23.5) * math.pi / 180)) - \
             0.3 * math.cos((w.month - 1) * 15 * math.pi / 180)
        ta = 0.7 * w.temp_high + 0.3 * w.temp_low
        rh = w.humidity
        rhs = 61.8 if ('雨' in w.condition or '雪' in w.condition) else 50
        A = 36.75 * (1 - 0.618)
        V = w.wind_speed

        if rh > rhs:
            if ta >= ts:
                tu = A * (math.exp(0.0005 * (ta - ts) * (rh - rhs)) - 1)
            else:
                tu = -A * (math.exp(0.00013 * (ts - ta) * (rh - rhs)) - 1)
        else:
            tu = 0

        if ta >= ts:
            tv = -0.03 * (ta - ts) * V
        else:
            tv = -0.01 * (ts - ta) * V

        return ta + tu + tv

    def calc_clothing(self, w: WeatherInput) -> IndexResult:
        """穿衣指数"""
        real_feel = self.calc_real_feel(w)

        if real_feel >= 29:
            if w.humidity >= 55:
                return IndexResult("穿衣", "闷热", 1, "短袖短裤，吸湿排汗面料", ["闷热", "高温"])
            else:
                return IndexResult("穿衣", "炎热", 1, "短袖短裤，注意防晒避暑", ["炎热"])
        elif real_feel >= 25:
            return IndexResult("穿衣", "热", 2, "轻薄透气夏装", ["偏热"])
        elif real_feel >= 20:
            return IndexResult("穿衣", "暖", 3, "单衣单裤", [])
        elif real_feel >= 15:
            return IndexResult("穿衣", "舒适", 4, "薄外套或长袖", [])
        elif real_feel >= 10:
            return IndexResult("穿衣", "凉", 3, "厚外套或羊毛衫", ["偏凉"])
        elif real_feel >= 5:
            return IndexResult("穿衣", "冷", 2, "棉服或皮夹克，帽子围巾", ["寒冷"])
        else:
            return IndexResult("穿衣", "寒冷", 1, "羽绒服全副武装，不宜久留户外", ["严寒"])

    def calc_uv(self, w: WeatherInput) -> IndexResult:
        """紫外线指数"""
        if w.uvi <= 2:
            return IndexResult("紫外线", "最弱", 5, "无需特别防护", [])
        elif w.uvi <= 4:
            return IndexResult("紫外线", "弱", 4, "可适当户外活动", [])
        elif w.uvi <= 6:
            return IndexResult("紫外线", "中等", 3, "建议涂防晒霜", ["紫外线"])
        elif w.uvi <= 9:
            return IndexResult("紫外线", "强", 2, "必须防晒，避开10-14点", ["紫外线强"])
        else:
            return IndexResult("紫外线", "最强", 1, "避免长时间户外，遮阳帽+防晒霜必备", ["紫外线极强"])

    def calc_heatstroke(self, w: WeatherInput) -> IndexResult:
        """中暑指数"""
        real_feel = self.calc_real_feel(w)

        if real_feel >= 35:
            return IndexResult("中暑", "极易中暑", 1, "避免户外活动，多补充水分，注意防暑降温", ["极易中暑", "高温"])
        elif real_feel >= 32:
            return IndexResult("中暑", "易中暑", 2, "减少户外活动，避免长时间暴露，多喝水", ["易中暑", "高温"])
        elif real_feel >= 29:
            return IndexResult("中暑", "较易中暑", 3, "尽量减少长时间户外活动，注意补水", ["较易中暑"])
        else:
            return IndexResult("中暑", "不易中暑", 5, "正常活动即可", [])

    def calc_cold(self, w: WeatherInput) -> IndexResult:
        """感冒指数"""
        z = 0

        # 温差（昨日与今日）
        if w.yesterday_temp_high is not None:
            temp_diff = w.yesterday_temp_high - w.temp_high
            if temp_diff >= 10:
                z += 4
            elif temp_diff > 7:
                z += 3
            elif temp_diff > 4:
                z += 2
            elif temp_diff > 0:
                z += 1

        # 湿度
        if w.humidity >= 70:
            z += 2
        elif w.humidity >= 50:
            z += 1

        # 低温
        if w.temp_low <= 0:
            z += 1

        # 昼夜温差
        day_night_diff = w.temp_high - w.temp_low
        if day_night_diff >= 10:
            z += 3
        elif day_night_diff >= 7:
            z += 2
        elif day_night_diff >= 4:
            z += 1

        # 映射到等级
        if z >= 8:
            return IndexResult("感冒", "极易发", 1, "避免人群密集场所，勤洗手勤通风", ["感冒高发"])
        elif z >= 6:
            return IndexResult("感冒", "易发", 2, "注意增减衣物，少去人群密集处", ["感冒易发"])
        elif z >= 4:
            return IndexResult("感冒", "较易发", 3, "适当增减衣物，保持室内通风", [])
        elif z >= 2:
            return IndexResult("感冒", "可能", 4, "注意保暖，坚持锻炼", [])
        else:
            return IndexResult("感冒", "少发", 5, "保持良好习惯即可", [])

    def calc_exercise(self, w: WeatherInput) -> IndexResult:
        """运动指数"""
        # 恶劣天气直接不适宜
        if w.condition in self.RAIN_WEATHER:
            return IndexResult("运动", "不适宜", 1, f"受{w.condition}影响，建议室内运动", [w.condition])
        elif w.condition in self.SNOW_WEATHER:
            return IndexResult("运动", "不适宜", 1, f"受{w.condition}影响，建议室内运动", [w.condition])
        elif w.condition in self.SAND_WEATHER or w.condition in self.SMOG_WEATHER:
            return IndexResult("运动", "不适宜", 1, f"受{w.condition}影响，不建议户外运动", [w.condition])

        # AQI判断
        if w.aqi > 200:
            return IndexResult("运动", "不适宜", 1, "空气严重污染，不建议户外运动", ["空气污染"])
        elif w.aqi > 150:
            return IndexResult("运动", "不适宜", 2, "空气中度污染，不建议户外运动", ["空气污染"])
        elif w.aqi > 100:
            return IndexResult("运动", "较不适宜", 3, "空气轻度污染，减少户外运动", ["空气轻度污染"])

        # 高温
        if w.temp_high >= 35:
            return IndexResult("运动", "不适宜", 1, "高温极易中暑，建议室内运动", ["高温"])
        elif w.temp_high >= 33:
            return IndexResult("运动", "较不适宜", 2, "气温过高，减少户外运动", ["高温"])

        # 低温
        if w.temp_low <= 0:
            return IndexResult("运动", "较不适宜", 2, "气温过低，注意保暖", ["低温"])

        # 大风
        if w.wind_level >= 5:
            return IndexResult("运动", "不适宜", 1, "大风天气，不宜户外运动", ["大风"])

        # 强紫外线
        if w.uvi >= 8:
            return IndexResult("运动", "较不适宜", 2, "紫外线太强，不宜长时间户外", ["紫外线强"])

        # 条件较好
        if w.wind_level <= 3 and w.uvi <= 4 and w.temp_high <= 30 and w.temp_low >= 5:
            return IndexResult("运动", "适宜", 5, "天气较好，适宜户外运动", [])

        return IndexResult("运动", "较适宜", 4, "可以户外运动，注意防护", [])

    def calc_comfort(self, w: WeatherInput) -> IndexResult:
        """舒适度指数"""
        real_feel = self.calc_real_feel(w)

        if 18 <= real_feel <= 25 and 30 <= w.humidity <= 60:
            return IndexResult("舒适度", "舒适", 5, "体感舒适，适合外出", [])
        elif real_feel > 30:
            return IndexResult("舒适度", "闷热", 2, "体感闷热，注意防暑", ["闷热"])
        elif real_feel < 10:
            return IndexResult("舒适度", "寒冷", 2, "体感寒冷，注意保暖", ["寒冷"])
        elif w.humidity > 75:
            return IndexResult("舒适度", "潮湿", 3, "湿度偏高，注意防潮", [])
        else:
            return IndexResult("舒适度", "一般", 4, "体感一般", [])

    def calc_travel(self, w: WeatherInput) -> IndexResult:
        """出行指数"""
        score = 5
        risks = []

        # 天气影响
        if w.condition in self.RAIN_WEATHER:
            score -= 2
            risks.append("有雨")
        if w.condition in self.SNOW_WEATHER:
            score -= 2
            risks.append("有雪")
        if w.condition in self.SAND_WEATHER or w.condition in self.SMOG_WEATHER:
            score -= 3
            risks.append(w.condition)

        # 温度影响
        if w.temp_high >= 35:
            score -= 2
            risks.append("高温")
        elif w.temp_high >= 33:
            score -= 1

        # AQI影响
        if w.aqi > 150:
            score -= 2
            risks.append("空气污染")
        elif w.aqi > 100:
            score -= 1

        # 风力影响
        if w.wind_level >= 6:
            score -= 2
            risks.append("大风")
        elif w.wind_level >= 4:
            score -= 1

        score = max(1, min(5, score))

        level_map = {5: "适宜出行", 4: "较适宜出行", 3: "一般", 2: "较不适宜出行", 1: "不适宜出行"}
        tip_map = {
            5: "天气条件好，适合外出",
            4: "可以外出，注意防护",
            3: "外出需注意天气变化",
            2: "减少外出，做好防护",
            1: "不建议外出，注意安全",
        }

        return IndexResult("出行", level_map[score], score, tip_map[score], risks)

    def calc_all(self, w: WeatherInput) -> dict:
        """计算所有指数"""
        return {
            "穿衣": self.calc_clothing(w),
            "紫外线": self.calc_uv(w),
            "中暑": self.calc_heatstroke(w),
            "感冒": self.calc_cold(w),
            "运动": self.calc_exercise(w),
            "舒适度": self.calc_comfort(w),
            "出行": self.calc_travel(w),
        }

    def get_rules(self, index_type: str) -> dict:
        """获取指数计算规则（供 Function Calling 使用）"""
        rules = {
            "穿衣": {
                "description": "基于体感温度计算穿衣建议",
                "factors": ["体感温度", "湿度"],
                "thresholds": [
                    {"condition": "体感>=29℃", "level": "炎热/闷热", "score": 1},
                    {"condition": "25℃<=体感<29℃", "level": "热", "score": 2},
                    {"condition": "20℃<=体感<25℃", "level": "暖", "score": 3},
                    {"condition": "15℃<=体感<20℃", "level": "舒适", "score": 4},
                    {"condition": "10℃<=体感<15℃", "level": "凉", "score": 3},
                    {"condition": "5℃<=体感<10℃", "level": "冷", "score": 2},
                    {"condition": "体感<5℃", "level": "寒冷", "score": 1},
                ]
            },
            "紫外线": {
                "description": "基于紫外线指数计算防护建议",
                "factors": ["紫外线指数(UVI)"],
                "thresholds": [
                    {"condition": "UVI<=2", "level": "最弱", "score": 5},
                    {"condition": "2<UVI<=4", "level": "弱", "score": 4},
                    {"condition": "4<UVI<=6", "level": "中等", "score": 3},
                    {"condition": "6<UVI<=9", "level": "强", "score": 2},
                    {"condition": "UVI>9", "level": "最强", "score": 1},
                ]
            },
            "中暑": {
                "description": "基于体感温度计算中暑风险",
                "factors": ["体感温度"],
                "thresholds": [
                    {"condition": "体感>=35℃", "level": "极易中暑", "score": 1},
                    {"condition": "32℃<=体感<35℃", "level": "易中暑", "score": 2},
                    {"condition": "29℃<=体感<32℃", "level": "较易中暑", "score": 3},
                    {"condition": "体感<29℃", "level": "不易中暑", "score": 5},
                ]
            },
            "感冒": {
                "description": "基于温差、湿度、昼夜温差计算感冒风险",
                "factors": ["昨日今日温差", "湿度", "低温", "昼夜温差"],
                "scoring": "累加计分，总分>=8极易发，>=6易发，>=4较易发，>=2可能，<2少发"
            },
            "运动": {
                "description": "综合天气、AQI、温度、风力、紫外线判断运动适宜度",
                "factors": ["天气现象", "AQI", "温度", "风力", "紫外线"],
                "conditions": [
                    "雨雪沙尘雾霾 → 不适宜",
                    "AQI>200 → 不适宜",
                    "温度>=35℃ → 不适宜",
                    "风力>=5级 → 不适宜",
                    "UVI>=8 → 较不适宜",
                    "条件好 → 适宜"
                ]
            },
            "舒适度": {
                "description": "基于体感温度和湿度判断舒适度",
                "factors": ["体感温度", "湿度"],
                "thresholds": [
                    {"condition": "18℃<=体感<=25℃ 且 30%<=湿度<=60%", "level": "舒适", "score": 5},
                    {"condition": "体感>30℃", "level": "闷热", "score": 2},
                    {"condition": "体感<10℃", "level": "寒冷", "score": 2},
                    {"condition": "湿度>75%", "level": "潮湿", "score": 3},
                ]
            },
            "出行": {
                "description": "综合天气、温度、AQI、风力判断出行适宜度",
                "factors": ["天气现象", "温度", "AQI", "风力"],
                "scoring": "基础5分，按条件扣分"
            },
        }
        return rules.get(index_type, {})
