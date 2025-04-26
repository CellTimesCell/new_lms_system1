// Teacher Dashboard component
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Card, Row, Col, Alert, Table, Tabs, Button, Typography,
  Statistic, Spin, Dropdown, Menu
} from 'antd';
import {
  TeamOutlined, FileOutlined, LineChartOutlined,
  ClockCircleOutlined, MoreOutlined, DownloadOutlined,
  EyeOutlined, BellOutlined, SettingOutlined
} from '@ant-design/icons';
import CourseTable from '../components/CourseTable';
import StudentActivityHeatmap from '../components/StudentActivityHeatmap';
import GradeDistributionChart from '../components/GradeDistributionChart';
import {
  fetchCoursesTeaching,
  fetchPendingAssignments,
  fetchCourseAnalytics,
  fetchStudentActivity
} from '../api/teacherApi';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

/**
 * Teacher Dashboard component
 *
 * Provides an overview of courses, pending assignments, and student activity
 * with detailed analytics for monitoring student engagement
 */
const TeacherDashboard = () => {
  const { t } = useTranslation();
  const [courses, setCourses] = useState([]);
  const [pendingAssignments, setPendingAssignments] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [studentActivity, setStudentActivity] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch courses
        const coursesData = await fetchCoursesTeaching();
        setCourses(coursesData);

        // Set default selected course if available
        if (coursesData.length > 0 && !selectedCourse) {
          setSelectedCourse(coursesData[0].id);
        }

        // Fetch pending assignments
        const assignmentsData = await fetchPendingAssignments();
        setPendingAssignments(assignmentsData);

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

  // Fetch course-specific analytics when selected course changes
  useEffect(() => {
    const fetchCourseData = async () => {
      if (!selectedCourse) return;

      try {
        setLoading(true);

        // Fetch course analytics and student activity in parallel
        const [analyticsData, activityData] = await Promise.all([
          fetchCourseAnalytics(selectedCourse),
          fetchStudentActivity(selectedCourse)
        ]);

        setAnalytics(analyticsData);
        setStudentActivity(activityData);
      } catch (err) {
        console.error('Error fetching course data:', err);
        // Don't set overall error, just log it
      } finally {
        setLoading(false);
      }
    };

    fetchCourseData();
  }, [selectedCourse]);

  // Handle course selection change
  const handleCourseChange = (courseId) => {
    setSelectedCourse(courseId);
  };

  // Generate course options for dropdown
  const courseOptions = courses.map(course => ({
    key: course.id,
    label: course.title
  }));

  // Columns for pending assignments table
  const assignmentColumns = [
    {
      title: t('dashboard.assignmentName'),
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: t('dashboard.course'),
      dataIndex: 'course_title',
      key: 'course',
    },
    {
      title: t('dashboard.submittedDate'),
      dataIndex: 'submitted_at',
      key: 'submitted_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: t('dashboard.student'),
      dataIndex: 'student_name',
      key: 'student',
    },
    {
      title: t('dashboard.actions'),
      key: 'actions',
      render: (_, record) => (
        <Button
          type="primary"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => window.location.href = `/submissions/${record.id}`}
        >
          {t('dashboard.grade')}
        </Button>
      ),
    },
  ];

  // Generate activity stats for selected course
  const getActivityStats = () => {
    if (!analytics.activity) return [];

    return [
      {
        title: t('dashboard.activeUsers'),
        value: analytics.activity.active_users || 0,
        icon: <TeamOutlined />
      },
      {
        title: t('dashboard.avgTimeSpent'),
        value: analytics.activity.avg_time_spent ? `${analytics.activity.avg_time_spent} min` : '0 min',
        icon: <ClockCircleOutlined />
      },
      {
        title: t('dashboard.resourcesViewed'),
        value: analytics.activity.resources_viewed || 0,
        icon: <EyeOutlined />
      },
      {
        title: t('dashboard.submissionRate'),
        value: analytics.activity.submission_rate ? `${analytics.activity.submission_rate}%` : '0%',
        icon: <FileOutlined />
      }
    ];
  };

  if (loading && !courses.length) {
    return (
      <div className="dashboard-loading">
        <Spin size="large" />
        <Text>{t('dashboard.loading')}</Text>
      </div>
    );
  }

  return (
    <div className="teacher-dashboard">
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
        {/* Header with course selector */}
        <Col span={24}>
          <Card>
            <div className="dashboard-header">
              <div>
                <Title level={2}>{t('dashboard.teacherDashboard')}</Title>
                <Text>{t('dashboard.welcomeMessage')}</Text>
              </div>

              <div className="course-selector">
                <Text>{t('dashboard.viewingCourse')}:</Text>
                <Dropdown
                  overlay={
                    <Menu
                      items={courseOptions}
                      onClick={({key}) => handleCourseChange(key)}
                    />
                  }
                >
                  <Button>
                    {courses.find(c => c.id === selectedCourse)?.title || t('dashboard.selectCourse')}
                  </Button>
                </Dropdown>
              </div>
            </div>
          </Card>
        </Col>

        {/* Activity Stats Cards */}
        {selectedCourse && (
          <Col span={24}>
            <Row gutter={[16, 16]}>
              {getActivityStats().map((stat, index) => (
                <Col xs={12} md={6} key={index}>
                  <Card>
                    <Statistic
                      title={
                        <div className="stat-title">
                          {stat.icon}
                          <span>{stat.title}</span>
                        </div>
                      }
                      value={stat.value}
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          </Col>
        )}

        {/* Courses Table */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <div className="section-title">
                <TeamOutlined />
                <span>{t('dashboard.myCourses')}</span>
              </div>
            }
            extra={
              <Button
                type="primary"
                icon={<FileOutlined />}
                onClick={() => window.location.href = '/courses/new'}
              >
                {t('dashboard.newCourse')}
              </Button>
            }
          >
            <CourseTable
              courses={courses}
              loading={loading}
            />
          </Card>
        </Col>

        {/* Pending Assignments */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <div className="section-title">
                <FileOutlined />
                <span>{t('dashboard.pendingAssignments')}</span>
              </div>
            }
            extra={
              <Button
                type="link"
                onClick={() => window.location.href = '/assignments/pending'}
              >
                {t('dashboard.viewAll')}
              </Button>
            }
          >
            <Table
              dataSource={pendingAssignments}
              columns={assignmentColumns}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              loading={loading}
              size="small"
            />
          </Card>
        </Col>

        {/* Analytics Tabs */}
        {selectedCourse && (
          <Col span={24}>
            <Card
              title={
                <div className="section-title">
                  <LineChartOutlined />
                  <span>{t('dashboard.courseAnalytics')}</span>
                </div>
              }
              extra={
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => {/* Download analytics report */}}
                >
                  {t('dashboard.exportReport')}
                </Button>
              }
            >
              <Tabs defaultActiveKey="1">
                <TabPane tab={t('dashboard.studentActivity')} key="1">
                  <StudentActivityHeatmap
                    data={studentActivity}
                    loading={loading}
                  />
                </TabPane>
                <TabPane tab={t('dashboard.gradeDistribution')} key="2">
                  <GradeDistributionChart
                    data={analytics.gradeDistribution || []}
                    loading={loading}
                  />
                </TabPane>
                <TabPane tab={t('dashboard.contentEngagement')} key="3">
                  {/* Content engagement analytics */}
                  <div className="coming-soon">
                    <Text>{t('dashboard.comingSoon')}</Text>
                  </div>
                </TabPane>
              </Tabs>
            </Card>
          </Col>
        )}

        {/* Quick Actions */}
        <Col span={24}>
          <Card>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <Button
                  type="primary"
                  icon={<BellOutlined />}
                  block
                  onClick={() => window.location.href = '/notifications'}
                >
                  {t('dashboard.sendNotifications')}
                </Button>
              </Col>
              <Col xs={24} sm={8}>
                <Button
                  icon={<FileOutlined />}
                  block
                  onClick={() => window.location.href = '/assignments/create'}
                >
                  {t('dashboard.createAssignment')}
                </Button>
              </Col>
              <Col xs={24} sm={8}>
                <Button
                  icon={<SettingOutlined />}
                  block
                  onClick={() => window.location.href = '/settings'}
                >
                  {t('dashboard.courseSettings')}
                </Button>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TeacherDashboard;