"""
简单测试 - 不需要数据库连接
"""

import pytest


@pytest.mark.unit
def test_basic_math():
    """基础数学测试"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


@pytest.mark.unit
def test_string_operations():
    """字符串操作测试"""
    assert "hello".upper() == "HELLO"
    assert "world".capitalize() == "World"


@pytest.mark.unit
def test_list_operations():
    """列表操作测试"""
    my_list = [1, 2, 3]
    my_list.append(4)
    assert len(my_list) == 4
    assert my_list[-1] == 4


@pytest.mark.unit
def test_dict_operations():
    """字典操作测试"""
    my_dict = {"a": 1, "b": 2}
    my_dict["c"] = 3
    assert len(my_dict) == 3
    assert my_dict["c"] == 3


@pytest.mark.unit
class TestDataStructures:
    """数据结构测试"""

    def test_tuple(self):
        my_tuple = (1, 2, 3)
        assert len(my_tuple) == 3
        assert my_tuple[0] == 1

    def test_set(self):
        my_set = {1, 2, 2, 3}
        assert len(my_set) == 3
        assert 3 in my_set

    def test_dict_keys(self):
        my_dict = {"x": 10, "y": 20}
        assert "x" in my_dict.keys()
        assert 20 in my_dict.values()
