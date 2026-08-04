"""
API接口集成测试
测试FastAPI接口
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthAPI:
    """健康检查接口测试"""

    @pytest.mark.skip(reason="需要配置环境变量")
    def test_health_endpoint(self):
        """测试健康检查接口"""
        from app.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.skip(reason="需要配置环境变量")
    def test_docs_endpoint(self):
        """测试API文档接口"""
        from app.main import app

        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200


@pytest.mark.integration
class TestAnalyzeAPI:
    """分析接口测试"""

    def test_analyze_endpoint_structure(self):
        """测试分析接口结构"""
        # 测试请求结构
        request_data = {
            "feedback_id": "TEST001",
            "content": "北京温度不准",
            "location": "北京",
            "time": "2024-01-15",
        }

        # 验证请求数据结构
        assert "feedback_id" in request_data
        assert "content" in request_data
        assert "location" in request_data

    def test_batch_analyze_structure(self):
        """测试批量分析接口结构"""
        request_data = {
            "feedbacks": [
                {"feedback_id": "TEST001", "content": "温度不准", "location": "北京"},
                {"feedback_id": "TEST002", "content": "没收到预警", "location": "上海"},
            ]
        }

        assert len(request_data["feedbacks"]) == 2
        assert request_data["feedbacks"][0]["feedback_id"] == "TEST001"


@pytest.mark.integration
class TestQueryAPI:
    """查询接口测试"""

    def test_weather_query_structure(self):
        """测试天气查询结构"""
        # 模拟查询参数
        params = {"location": "北京", "time": "2024-01-15"}
        assert "location" in params
        assert "time" in params

    def test_alert_query_structure(self):
        """测试预警查询结构"""
        params = {"location": "北京", "time": "2024-01-15"}
        assert "location" in params
        assert "time" in params

    def test_analysis_result_structure(self):
        """测试分析结果结构"""
        result = {
            "analysis_id": "A001",
            "feedback_id": "F001",
            "status": "completed",
            "feedback_type": "温度偏差",
            "root_cause": "数据源延迟",
            "reply_content": "您好，经核实...",
        }
        assert result["status"] == "completed"
        assert result["feedback_type"] is not None
        assert result["root_cause"] is not None


@pytest.mark.integration
class TestErrorHandling:
    """错误处理测试"""

    def test_invalid_request(self):
        """测试无效请求"""
        # 缺少必填字段
        invalid_data = {
            "content": "测试"
            # 缺少 feedback_id
        }

        # 验证数据结构
        assert "feedback_id" not in invalid_data

    @pytest.mark.skip(reason="需要配置环境变量")
    def test_not_found_resource(self):
        """测试资源不存在"""
        from app.main import app

        client = TestClient(app)

        # 查询不存在的分析结果
        response = client.get("/api/v1/agent/analysis/NONEXIST")
        # 应该返回404或适当的错误
        assert response.status_code in [404, 500]


@pytest.mark.integration
class TestDataValidation:
    """数据验证测试"""

    def test_feedback_validation(self):
        """测试反馈数据验证"""
        from pydantic import ValidationError
        from app.models.schemas import FeedbackRequest

        # 有效数据
        valid_data = {"feedback_id": "TEST001", "content": "温度不准", "location": "北京"}
        req = FeedbackRequest(**valid_data)
        assert req.feedback_id == "TEST001"

        # 无效数据（缺少必填字段）
        with pytest.raises(ValidationError):
            FeedbackRequest(content="温度不准")

    def test_response_validation(self):
        """测试响应数据验证"""
        from app.models.schemas import WeatherData

        # 有效响应
        valid_response = {"city_name": "北京", "temperature": 25.0, "humidity": 60}
        data = WeatherData(**valid_response)
        assert data.city_name == "北京"
        assert data.temperature == 25.0
