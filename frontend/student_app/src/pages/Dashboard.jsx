// Student Dashboard component
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Row, Col, Alert, List, Progress, Button, Typography, Spin } from 'antd';
import { CalendarOutlined, BookOutlined, ClockCircleOutlined, TrophyOutlined } from '@ant-design/icons';
import CourseCard from '../components/CourseCard';
import AssignmentList from '../components/AssignmentList';
import ActivityChart from '../components/ActivityChart';
import { fetchEnrolledCourses, fetchUpcomingAssignments, fetchUserActivity } from '../api/studentApi';

const { Title, Text } = Typography;

/**
 * Student Dashboard showing enrolled courses, upcoming assignments, and activity
 */
const Dashboard = () => {
  const { t } = useTranslation();
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [activityData, setActivityData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Track when the student viewed this page for analytics
  useEffect(() => {
    // Log page view for analytics
    const logPageView = async () => {
      try {
        const timestamp = new Date();
        await fetch('/api/analytics/track', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            event_id: crypto.randomUUID(),
            student_id: localStorage.getItem('userId'),
            event_type: 'page_view',
            resource_type: 'dashboard',
            resource_id: null,
            timestamp: timestamp.toISOString(),
            ip_address: null, // Will be captured server-side
            user_agent: navigator.userAgent,
            duration_seconds: 0, // Will be updated on unmount
            metadata: {
              referrer: document.referrer,
              screen_width: window.innerWidth,
              screen_height: window.innerHeight
            }
          }),
        });
      } catch (err) {
        console.error('Failed to log analytics event:', err);
      }
    };

    logPageView();

    const startTime = Date.now();

    // On unmount, log the duration
    return () => {
      const endTime = Date.now();
      const durationSeconds = Math.round((endTime - startTime) / 1000);

      // Log the duration
      fetch('/api/analytics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_id: crypto.randomUUID(),
          student_id: localStorage.getItem('userId'),
          event_type: 'page_duration',
          resource_type: 'dashboard',
          resource_id: null,
          timestamp: new Date().toISOString(),
          ip_address: null,
          user_agent: navigator.userAgent,
          duration_seconds: durationSeconds,
          metadata: {}
        }),
      }).catch(err => console.error('Failed to log duration:', err));
    };
  }, []);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch courses, assignments, and activity in parallel
        const [coursesData, assignmentsData, activityData] = await Promise.all([
          fetchEnrolledCourses(),
          fetchUpcomingAssignments(),
          fetchUserActivity()
        ]);

        setCourses(coursesData);
        setAssignments(assignmentsData);
        setActivityData(activityData);
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError(t('dashboard.errorLoading'));
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [t]);

  // Calculate overall progress
  const calculateOverallProgress = () => {
    if (!courses.length) return 0;

    const totalProgress = courses.reduce((sum, course) => sum + (course.completion_percentage || 0), 0);
    return Math.round(totalProgress / courses.length);
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <Spin size="large" />
        <Text>{t('dashboard.loading')}</Text>
      </div>
    );
  }

  return (
    <div className="student-dashboard">
      {error && (
        <Alert
          message={t('dashboard.error')}
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 20 }}
        />
      )}

      <Row gutter={[24, 24]}>
        {/* Welcome Section */}
        <Col span={24}>
          <Card>
            <Title level={2}>{t('dashboard.welcome', { name: 'Student' })}</Title>
            <div className="progress-section">
              <Text>{t('dashboard.overallProgress')}</Text>
              <Progress percent={calculateOverallProgress()} />
            </div>
          </Card>
        </Col>

        {/* Enrolled Courses */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <div className="section-title">
                <BookOutlined />
                <span>{t('dashboard.myCourses')}</span>
              </div>
            }
            extra={<Button type="link">{t('dashboard.viewAll')}</Button>}
          >
            {courses.length > 0 ? (
              <Row gutter={[16, 16]}>
                {courses.map(course => (
                  <Col xs={24} sm={12} key={course.id}>
                    <CourseCard course={course} />
                  </Col>
                ))}
              </Row>
            ) : (
              <div className="empty-state">
                <Text>{t('dashboard.noCoursesEnrolled')}</Text>
                <Button type="primary">{t('dashboard.browseCourses')}</Button>
              </div>
            )}
          </Card>
        </Col>

        {/* Upcoming Assignments */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <div className="section-title">
                <CalendarOutlined />
                <span>{t('dashboard.upcomingAssignments')}</span>
              </div>
            }
            className="upcoming-assignments"
          >
            <AssignmentList assignments={assignments} />
          </Card>
        </Col>

        {/* Activity Chart */}
        <Col span={24}>
          <Card
            title={
              <div className="section-title">
                <ClockCircleOutlined />
                <span>{t('dashboard.recentActivity')}</span>
              </div>
            }
          >
            <ActivityChart data={activityData} />
          </Card>
        </Col>

        {/* Achievements Section - Basic implementation */}
        <Col span={24}>
          <Card
            title={
              <div className="section-title">
                <TrophyOutlined />
                <span>{t('dashboard.achievements')}</span>
              </div>
            }
          >
            <div className="achievements-section">
              {/* Placeholder for achievements */}
              <Text>{t('dashboard.achievementsComingSoon')}</Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;