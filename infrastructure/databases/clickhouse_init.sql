-- ClickHouse schema for analytics

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS lms_analytics;

-- Use the analytics database
USE lms_analytics;

-- Activity events table for student tracking
CREATE TABLE IF NOT EXISTS activity_events
(
    event_id String,
    student_id UInt32,
    event_type String,
    resource_type String,
    resource_id Nullable(String),
    timestamp DateTime,
    ip_address Nullable(String),
    user_agent Nullable(String),
    duration_seconds UInt32 DEFAULT 0,
    metadata String, -- JSON string

    -- Indices
    INDEX idx_student (student_id) TYPE minmax GRANULARITY 8192,
    INDEX idx_event_type (event_type) TYPE set(0) GRANULARITY 8192,
    INDEX idx_resource_type (resource_type) TYPE set(0) GRANULARITY 8192
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (student_id, timestamp)
SETTINGS index_granularity = 8192;

-- Course activity summary
CREATE MATERIALIZED VIEW IF NOT EXISTS course_activity_daily
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(date)
ORDER BY (date, course_id)
AS SELECT
    toDate(timestamp) AS date,
    resource_id AS course_id,
    count() AS event_count,
    uniqExact(student_id) AS unique_students,
    sum(duration_seconds) AS total_duration_seconds
FROM activity_events
WHERE resource_type = 'course'
GROUP BY date, course_id;

-- Student activity summary
CREATE MATERIALIZED VIEW IF NOT EXISTS student_activity_daily
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(date)
ORDER BY (date, student_id)
AS SELECT
    toDate(timestamp) AS date,
    student_id,
    count() AS event_count,
    countIf(event_type = 'page_view') AS page_views,
    countIf(event_type = 'resource_view') AS resource_views,
    countIf(event_type = 'submission') AS submissions,
    sum(duration_seconds) AS total_duration_seconds
FROM activity_events
GROUP BY date, student_id;

-- Reports table for storing generated reports
CREATE TABLE IF NOT EXISTS reports
(
    report_id String,
    report_type String,
    created_by UInt32,
    parameters String, -- JSON string
    status String,
    created_at DateTime DEFAULT now(),
    completed_at Nullable(DateTime),
    result_url Nullable(String),
    error_message Nullable(String)
)
ENGINE = MergeTree
ORDER BY (created_at, report_id)
SETTINGS index_granularity = 8192;

-- Assignment analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS assignment_analytics
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(date)
ORDER BY (date, assignment_id)
AS SELECT
    toDate(timestamp) AS date,
    resource_id AS assignment_id,
    countIf(event_type = 'view') AS view_count,
    countIf(event_type = 'submission') AS submission_count,
    uniqExact(student_id) AS unique_students,
    avg(duration_seconds) AS avg_duration_seconds
FROM activity_events
WHERE resource_type = 'assignment'
GROUP BY date, assignment_id;

-- Engagement score calculation
CREATE MATERIALIZED VIEW IF NOT EXISTS student_engagement_score
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(date)
ORDER BY (date, student_id, course_id)
AS SELECT
    toDate(timestamp) AS date,
    student_id,
    resource_id AS course_id,
    -- Engagement score formula: views (1 point) + submissions (5 points) + duration factor
    countIf(event_type = 'view') +
    countIf(event_type = 'submission') * 5 +
    sum(duration_seconds) / 60 AS engagement_score
FROM activity_events
WHERE resource_type = 'course' OR resource_type = 'assignment' OR resource_type = 'content'
GROUP BY date, student_id, course_id;