-- =============================================
-- 气象负反馈分析系统 - 建库建表脚本
-- =============================================

CREATE DATABASE IF NOT EXISTS weather DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE weather;

-- =============================================
-- 1. 城市表
-- =============================================
CREATE TABLE IF NOT EXISTS city (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city_id VARCHAR(20) NOT NULL UNIQUE COMMENT '城市编号',
    city_name VARCHAR(64) COMMENT '城市名',
    longitude FLOAT COMMENT '经度',
    latitude FLOAT COMMENT '纬度',
    province VARCHAR(32) COMMENT '省份',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) COMMENT='城市表';

-- =============================================
-- 2. 实况数据表
-- =============================================
CREATE TABLE IF NOT EXISTS weather_cn (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    city_id VARCHAR(20) NOT NULL COMMENT '城市编号',
    get_time INT COMMENT '采集时间戳',
    update_time VARCHAR(32) COMMENT '数据更新时间',
    temp FLOAT COMMENT '温度(℃)',
    real_feel FLOAT COMMENT '体感温度(℃)',
    humidity FLOAT COMMENT '相对湿度(%)',
    wspd FLOAT COMMENT '风速(m/s)',
    wdir VARCHAR(8) COMMENT '风向',
    wind_level INT COMMENT '风力等级',
    weather_zh VARCHAR(32) COMMENT '天气现象',
    vis FLOAT COMMENT '能见度(km)',
    pressure FLOAT COMMENT '气压(hPa)',
    mslp FLOAT COMMENT '海平面气压(hPa)',
    precip_1h FLOAT COMMENT '1小时降水量(mm)',
    wind_degrees FLOAT COMMENT '风向角度',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cn_city_time (city_id, get_time)
) COMMENT='实况数据表';

-- =============================================
-- 3. 逐时预报表
-- =============================================
CREATE TABLE IF NOT EXISTS weather_hh (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    city_id VARCHAR(20) NOT NULL COMMENT '城市编号',
    get_time INT COMMENT '采集时间戳',
    update_time VARCHAR(32) COMMENT '数据更新时间',
    predict_timestamp INT COMMENT '预报时间戳',
    predict_date VARCHAR(32) COMMENT '预报日期',
    predict_hour INT COMMENT '预报小时',
    weather_zh VARCHAR(32) COMMENT '天气现象',
    temp FLOAT COMMENT '温度(℃)',
    wdir VARCHAR(8) COMMENT '风向',
    wspd FLOAT COMMENT '风速(m/s)',
    humidity FLOAT COMMENT '相对湿度(%)',
    wind_level INT COMMENT '风力等级',
    wind_degrees FLOAT COMMENT '风向角度',
    pop FLOAT COMMENT '降水概率(%)',
    qpf FLOAT COMMENT '降水量(mm)',
    snow FLOAT COMMENT '降雪量(mm)',
    pressure FLOAT COMMENT '气压(hPa)',
    vis FLOAT COMMENT '能见度(km)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_hh_city_time (city_id, predict_timestamp)
) COMMENT='逐时预报表';

-- =============================================
-- 4. 逐天预报表
-- =============================================
CREATE TABLE IF NOT EXISTS weather_ff (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    city_id VARCHAR(20) NOT NULL COMMENT '城市编号',
    get_time INT COMMENT '采集时间戳',
    update_time VARCHAR(32) COMMENT '数据更新时间',
    predict_date VARCHAR(32) COMMENT '预报日期',
    temp_high FLOAT COMMENT '最高温度(℃)',
    temp_low FLOAT COMMENT '最低温度(℃)',
    weather_day VARCHAR(32) COMMENT '白天天气',
    weather_night VARCHAR(32) COMMENT '夜间天气',
    wind_dir_day VARCHAR(8) COMMENT '白天风向',
    wind_level_day VARCHAR(8) COMMENT '白天风力',
    wind_dir_night VARCHAR(8) COMMENT '夜间风向',
    wind_level_night VARCHAR(8) COMMENT '夜间风力',
    sunrise VARCHAR(32) COMMENT '日出时间',
    sunset VARCHAR(32) COMMENT '日落时间',
    humidity_day FLOAT COMMENT '白天湿度(%)',
    humidity_night FLOAT COMMENT '夜间湿度(%)',
    wind_degrees_day FLOAT COMMENT '白天风向角度',
    wspd_day FLOAT COMMENT '白天风速(m/s)',
    wind_degrees_night FLOAT COMMENT '夜间风向角度',
    wspd_night FLOAT COMMENT '夜间风速(m/s)',
    pop_day FLOAT COMMENT '白天降水概率(%)',
    pop_night FLOAT COMMENT '夜间降水概率(%)',
    pressure_day FLOAT COMMENT '白天气压(hPa)',
    pressure_night FLOAT COMMENT '夜间气压(hPa)',
    mslp_day FLOAT COMMENT '白天海平面气压(hPa)',
    mslp_night FLOAT COMMENT '夜间海平面气压(hPa)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ff_city_date (city_id, predict_date)
) COMMENT='逐天预报表';

-- =============================================
-- 5. 预警数据表
-- =============================================
CREATE TABLE IF NOT EXISTS alert_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alert_id VARCHAR(64) NOT NULL COMMENT '预警ID',
    city_id VARCHAR(20) NOT NULL COMMENT '城市编号',
    city_name VARCHAR(32) COMMENT '城市名',
    alert_type VARCHAR(32) COMMENT '预警类型',
    alert_level VARCHAR(16) COMMENT '预警级别',
    title VARCHAR(128) COMMENT '预警标题',
    content TEXT COMMENT '预警内容',
    start_time VARCHAR(32) COMMENT '预警开始时间',
    end_time VARCHAR(32) COMMENT '预警结束时间',
    update_time VARCHAR(32) COMMENT '数据更新时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_alert_id (alert_id),
    INDEX idx_alert_city (city_id),
    INDEX idx_alert_time (start_time, end_time),
    INDEX idx_alert_type (alert_type)
) COMMENT='预警数据表';

-- =============================================
-- 6. 分析结果表
-- =============================================
CREATE TABLE IF NOT EXISTS analysis_result (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    analysis_id VARCHAR(64) NOT NULL UNIQUE COMMENT '分析ID',
    feedback_id VARCHAR(64) NOT NULL COMMENT '反馈ID',
    feedback_content TEXT COMMENT '反馈内容',
    location VARCHAR(64) COMMENT '位置',
    user_id VARCHAR(64) COMMENT '用户ID',
    source VARCHAR(32) COMMENT '来源',
    feedback_type VARCHAR(32) COMMENT '问题类型',
    root_cause TEXT COMMENT '问题根因',
    meteorological_explanation TEXT COMMENT '气象解释',
    suggestion TEXT COMMENT '改进建议',
    reply_content TEXT COMMENT '回复内容',
    actual_temp FLOAT COMMENT '实际温度',
    actual_humidity FLOAT COMMENT '实际湿度',
    actual_wind_speed FLOAT COMMENT '实际风速',
    feels_like FLOAT COMMENT '体感温度',
    alert_type VARCHAR(32) COMMENT '预警类型',
    alert_level VARCHAR(16) COMMENT '预警级别',
    alert_time VARCHAR(32) COMMENT '预警时间',
    status VARCHAR(16) DEFAULT 'pending' COMMENT '状态: pending/approved/rejected/sent',
    reviewer VARCHAR(64) COMMENT '审核人',
    review_time DATETIME COMMENT '审核时间',
    review_comment TEXT COMMENT '审核意见',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_feedback (feedback_id),
    INDEX idx_created (created_at)
) COMMENT='分析结果表';

-- =============================================
-- 7. 生活指数表
-- =============================================
CREATE TABLE IF NOT EXISTS live_index (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    city_id VARCHAR(20) NOT NULL COMMENT '城市编号',
    city_name VARCHAR(32) COMMENT '城市名',
    index_date DATE NOT NULL COMMENT '指数日期',
    index_type VARCHAR(32) NOT NULL COMMENT '指数类型',
    level VARCHAR(16) COMMENT '等级文字',
    score INT COMMENT '1-5分',
    tip TEXT COMMENT '建议文案',
    risk_factors JSON COMMENT '风险因子',
    calc_input JSON COMMENT '计算输入',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city_date (city_id, index_date),
    INDEX idx_type (index_type)
) COMMENT='生活指数表';

-- =============================================
-- 8. 天气现象映射表
-- =============================================
CREATE TABLE IF NOT EXISTS weather_icon (
    id INT COMMENT 'ID',
    weather_id BIGINT COMMENT '天气ID',
    icon_day BIGINT COMMENT '白天图标',
    icon_night BIGINT COMMENT '夜间图标',
    condition_zh TEXT COMMENT '天气现象(中文)',
    condition_en TEXT COMMENT '天气现象(英文)',
    condition_tw TEXT COMMENT '天气现象(繁体)',
    condition_hk TEXT COMMENT '天气现象(香港)',
    condition_es TEXT COMMENT '天气现象(西班牙)',
    condition_pt TEXT COMMENT '天气现象(葡萄牙)',
    condition_ru TEXT COMMENT '天气现象(俄语)',
    condition_r TEXT COMMENT '天气现象(俄语2)',
    condition_de TEXT COMMENT '天气现象(德语)',
    condition_ar TEXT COMMENT '天气现象(阿拉伯)',
    condition_ko TEXT COMMENT '天气现象(韩语)',
    condition_ja TEXT COMMENT '天气现象(日语)',
    condition_hi TEXT COMMENT '天气现象(印地语)',
    condition_te TEXT COMMENT '天气现象(泰卢固语)'
) COMMENT='天气现象映射表';
