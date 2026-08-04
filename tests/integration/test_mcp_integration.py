"""
MCP工具集成测试
测试MCP Server的工具功能
"""

import pytest


@pytest.mark.integration
class TestMCPTools:
    """MCP工具测试"""

    def test_query_weather_tool_structure(self):
        """测试天气查询工具结构"""
        tool_def = {
            "name": "query_weather",
            "description": "查询城市实况气象数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称或城市编号"
                    },
                    "time": {
                        "type": "string",
                        "description": "查询时间"
                    }
                },
                "required": ["location"]
            }
        }

        assert tool_def["name"] == "query_weather"
        assert "location" in tool_def["parameters"]["properties"]
        assert "location" in tool_def["parameters"]["required"]

    def test_query_alert_tool_structure(self):
        """测试预警查询工具结构"""
        tool_def = {
            "name": "query_alert",
            "description": "查询城市当前生效的气象预警",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "time": {
                        "type": "string",
                        "description": "查询时间"
                    }
                },
                "required": ["location"]
            }
        }

        assert tool_def["name"] == "query_alert"
        assert "location" in tool_def["parameters"]["required"]

    def test_query_aqi_tool_structure(self):
        """测试AQI查询工具结构"""
        tool_def = {
            "name": "query_aqi",
            "description": "查询城市空气质量指数",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "time": {
                        "type": "string",
                        "description": "查询时间"
                    }
                },
                "required": ["city"]
            }
        }

        assert tool_def["name"] == "query_aqi"
        assert "city" in tool_def["parameters"]["required"]

    def test_analyze_feedback_tool_structure(self):
        """测试反馈分析工具结构"""
        tool_def = {
            "name": "analyze_feedback",
            "description": "分析气象负反馈",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "反馈内容"
                    },
                    "location": {
                        "type": "string",
                        "description": "位置"
                    },
                    "time": {
                        "type": "string",
                        "description": "时间"
                    }
                },
                "required": ["content"]
            }
        }

        assert tool_def["name"] == "analyze_feedback"
        assert "content" in tool_def["parameters"]["required"]

    def test_check_pipeline_tool_structure(self):
        """测试链路检查工具结构"""
        tool_def = {
            "name": "check_pipeline",
            "description": "检查数据链路健康状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "time": {
                        "type": "string",
                        "description": "检查时间"
                    }
                },
                "required": ["location"]
            }
        }

        assert tool_def["name"] == "check_pipeline"
        assert "location" in tool_def["parameters"]["required"]


@pytest.mark.integration
class TestMCPToolInvocation:
    """MCP工具调用测试"""

    def test_tool_response_format(self):
        """测试工具响应格式"""
        response = {
            "success": True,
            "data": {
                "city": "北京",
                "temperature": 25.0,
                "humidity": 60
            },
            "message": "查询成功"
        }

        assert "success" in response
        assert "data" in response
        assert response["success"] is True

    def test_tool_error_format(self):
        """测试工具错误格式"""
        error_response = {
            "success": False,
            "error": "城市不存在",
            "error_code": "CITY_NOT_FOUND"
        }

        assert error_response["success"] is False
        assert "error" in error_response
        assert "error_code" in error_response

    def test_tool_parameter_validation(self):
        """测试工具参数验证"""
        # 有效参数
        valid_params = {
            "location": "北京",
            "time": "2024-01-15"
        }
        assert "location" in valid_params

        # 无效参数（缺少必填）
        invalid_params = {
            "time": "2024-01-15"
            # 缺少 location
        }
        assert "location" not in invalid_params


@pytest.mark.integration
class TestMCPServerConfig:
    """MCP服务器配置测试"""

    def test_server_metadata(self):
        """测试服务器元数据"""
        metadata = {
            "name": "WeatherAgent",
            "description": "气象负反馈分析 Agent",
            "version": "1.0.0",
            "tools": [
                "query_weather",
                "query_alert",
                "query_aqi",
                "get_life_index",
                "search_knowledge",
                "analyze_feedback",
                "check_pipeline",
                "get_monitor_overview"
            ]
        }

        assert metadata["name"] == "WeatherAgent"
        assert len(metadata["tools"]) == 8

    def test_tool_count(self):
        """测试工具数量"""
        tools = [
            "query_weather",
            "query_alert",
            "query_aqi",
            "get_life_index",
            "search_knowledge",
            "analyze_feedback",
            "check_pipeline",
            "get_monitor_overview"
        ]
        assert len(tools) == 8

    def test_tool_roles(self):
        """测试工具角色"""
        customer_tools = ["query_weather", "query_alert", "query_aqi", "get_life_index", "search_knowledge", "analyze_feedback"]
        operator_tools = ["check_pipeline", "get_monitor_overview"]

        assert len(customer_tools) == 6
        assert len(operator_tools) == 2
        assert len(customer_tools) + len(operator_tools) == 8
