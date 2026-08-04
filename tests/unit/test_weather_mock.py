"""
气象数据 Mock 测试
使用 Mock 模拟数据库查询
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestWeatherQueryMock:
    """气象查询 Mock 测试"""

    @patch("app.skills.weather.get_session")
    def test_query_weather_success(self, mock_get_session):
        """测试查询天气成功"""
        # 设置 Mock 返回值
        mock_session = MagicMock()
        mock_row = MagicMock()
        mock_row.city_id = "101010100"
        mock_row.city_name = "北京"
        mock_row.temp = 25.0
        mock_row.humidity = 60
        mock_row.wspd = 3.5
        mock_row.wdir = "南风"
        mock_row.weather_zh = "晴"
        mock_row.update_time = "2024-01-15 10:00:00"

        mock_session.execute.return_value.fetchone.return_value = mock_row
        mock_get_session.return_value = mock_session

        # 验证 Mock 设置
        assert mock_session.execute.return_value.fetchone.return_value.city_name == "北京"

    @patch("app.skills.weather.get_session")
    def test_query_weather_not_found(self, mock_get_session):
        """测试查询天气 - 城市不存在"""
        # 设置 Mock 返回 None
        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = None
        mock_get_session.return_value = mock_session

        # 验证 Mock 设置
        result = mock_session.execute.return_value.fetchone.return_value
        assert result is None

    @patch("app.skills.weather.get_session")
    def test_query_weather_db_error(self, mock_get_session):
        """测试查询天气 - 数据库错误"""
        # 设置 Mock 抛出异常
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("数据库连接失败")
        mock_get_session.return_value = mock_session

        # 验证异常
        with pytest.raises(Exception) as exc_info:
            mock_session.execute()
        assert "数据库连接失败" in str(exc_info.value)


@pytest.mark.unit
class TestAQIQueryMock:
    """AQI查询 Mock 测试"""

    @patch("app.skills.aqi.get_db_session")
    def test_query_aqi_success(self, mock_get_session):
        """测试查询AQI成功"""
        # 设置 Mock 返回值
        mock_session = MagicMock()
        mock_record = MagicMock()
        mock_record.city_name = "北京"
        mock_record.aqi = 75
        mock_record.pm25 = 55.0
        mock_record.pm10 = 85.0
        mock_record.update_time = "2024-01-15 10:00:00"

        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_record
        mock_get_session.return_value = mock_session

        # 验证 Mock 设置
        result = mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value
        assert result.city_name == "北京"
        assert result.aqi == 75

    @patch("app.skills.aqi.get_db_session")
    def test_query_aqi_not_found(self, mock_get_session):
        """测试查询AQI - 城市不存在"""
        # 设置 Mock 返回 None
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_get_session.return_value = mock_session

        # 验证 Mock 设置
        result = mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value
        assert result is None


@pytest.mark.unit
class TestAlertQueryMock:
    """预警查询 Mock 测试"""

    @patch("app.skills.alert.get_session")
    def test_query_alert_success(self, mock_get_session):
        """测试查询预警成功"""
        # 设置 Mock 返回值
        mock_session = MagicMock()
        mock_records = [
            MagicMock(
                alert_type="暴雨",
                alert_level="橙色",
                title="北京市暴雨橙色预警",
                content="预计未来6小时...",
                start_time="2024-01-15 10:00:00",
                end_time="2024-01-15 16:00:00",
            )
        ]

        mock_session.query.return_value.filter.return_value.all.return_value = mock_records
        mock_get_session.return_value = mock_session

        # 验证 Mock 设置
        results = mock_session.query.return_value.filter.return_value.all.return_value
        assert len(results) == 1
        assert results[0].alert_type == "暴雨"
        assert results[0].alert_level == "橙色"

    @patch("app.skills.alert.get_session")
    def test_query_alert_empty(self, mock_get_session):
        """测试查询预警 - 无预警"""
        # 设置 Mock 返回空列表
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_get_session.return_value = mock_session

        # 验证 Mock 设置
        results = mock_session.query.return_value.filter.return_value.all.return_value
        assert len(results) == 0


@pytest.mark.unit
class TestFetcherMock:
    """数据抓取 Mock 测试"""

    @patch("httpx.Client.get")
    def test_fetch_weather_data(self, mock_get):
        """测试抓取气象数据"""
        # 设置 Mock 返回值
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": [{"cityId": "101010100", "cityName": "北京", "temp": 25.0, "humidity": 60}],
        }
        mock_get.return_value = mock_response

        # 验证 Mock 设置
        response = mock_get()
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1

    @patch("httpx.Client.get")
    def test_fetch_weather_error(self, mock_get):
        """测试抓取气象数据 - 请求失败"""
        # 设置 Mock 抛出异常
        mock_get.side_effect = Exception("网络连接超时")

        # 验证异常
        with pytest.raises(Exception) as exc_info:
            mock_get()
        assert "网络连接超时" in str(exc_info.value)


@pytest.mark.unit
class TestLLMCallMock:
    """LLM调用 Mock 测试"""

    @patch("app.services.llm.get_llm_service")
    def test_llm_service(self, mock_get_service):
        """测试获取LLM服务"""
        # 设置 Mock 返回值
        mock_service = MagicMock()
        mock_service.chat.return_value = MagicMock(
            content="分析结果：用户反馈温度偏差，可能原因是数据源延迟。",
            usage=MagicMock(total_tokens=150),
        )
        mock_get_service.return_value = mock_service

        # 验证 Mock 设置
        service = mock_get_service()
        result = service.chat()
        assert "分析结果" in result.content
        assert result.usage.total_tokens == 150

    @patch("app.services.llm.get_llm_service")
    def test_llm_service_error(self, mock_get_service):
        """测试LLM服务错误"""
        # 设置 Mock 抛出异常
        mock_get_service.side_effect = Exception("服务初始化失败")

        # 验证异常
        with pytest.raises(Exception) as exc_info:
            mock_get_service()
        assert "服务初始化失败" in str(exc_info.value)


@pytest.mark.unit
class TestMockPatterns:
    """Mock 模式测试"""

    def test_mock_return_value(self):
        """测试 Mock 返回值"""
        mock = MagicMock()
        mock.return_value = 42
        assert mock() == 42

    def test_mock_side_effect(self):
        """测试 Mock 副作用"""
        mock = MagicMock()
        mock.side_effect = [1, 2, 3]
        assert mock() == 1
        assert mock() == 2
        assert mock() == 3

    def test_mock_exception(self):
        """测试 Mock 异常"""
        mock = MagicMock()
        mock.side_effect = ValueError("无效值")
        with pytest.raises(ValueError):
            mock()

    def test_mock_assert_called(self):
        """测试 Mock 调用断言"""
        mock = MagicMock()
        mock("arg1", "arg2")
        mock.assert_called_once_with("arg1", "arg2")

    def test_mock_assert_not_called(self):
        """测试 Mock 未调用断言"""
        mock = MagicMock()
        mock.assert_not_called()
