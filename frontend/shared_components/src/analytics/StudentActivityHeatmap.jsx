// Student Activity Heatmap Component
import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Spin, Select, DatePicker, Tooltip, Typography, Empty } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import * as d3 from 'd3';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

/**
 * StudentActivityHeatmap Component
 *
 * Displays a heatmap of student activity across days and hours
 * Helps instructors visualize when students are most active
 *
 * @param {Object} props
 * @param {Array} props.data - Activity data
 * @param {string} props.courseId - Course ID
 * @param {boolean} props.loading - Loading state
 */
const StudentActivityHeatmap = ({ data, courseId, loading }) => {
  const { t } = useTranslation();
  const [viewType, setViewType] = useState('course');
  const [dateRange, setDateRange] = useState([
    moment().subtract(30, 'days'),
    moment()
  ]);
  const [resourceType, setResourceType] = useState('all');
  const [processedData, setProcessedData] = useState([]);
  const svgRef = useRef(null);

  // Process data when inputs change
  useEffect(() => {
    if (!data || data.length === 0) return;

    // Filter data based on selections
    let filteredData = [...data];

    // Filter by date range
    if (dateRange && dateRange.length === 2) {
      filteredData = filteredData.filter(item => {
        const itemDate = moment(item.timestamp);
        return itemDate.isSameOrAfter(dateRange[0], 'day') &&
               itemDate.isSameOrBefore(dateRange[1], 'day');
      });
    }

    // Filter by resource type
    if (resourceType !== 'all') {
      filteredData = filteredData.filter(item => item.resource_type === resourceType);
    }

    // Process data for heatmap
    const activityByDayAndHour = processActivityData(filteredData, viewType);
    setProcessedData(activityByDayAndHour);
  }, [data, viewType, dateRange, resourceType]);

  // Draw heatmap when processed data changes
  useEffect(() => {
    if (processedData.length > 0) {
      drawHeatmap();
    }
  }, [processedData]);

  // Process activity data into day/hour format
  const processActivityData = (activityData, viewType) => {
    // Define days and hours
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const hours = Array.from({ length: 24 }, (_, i) => i);

    // Initialize heatmap data structure
    const heatmapData = [];

    // Create empty grid
    days.forEach(day => {
      hours.forEach(hour => {
        heatmapData.push({
          day,
          hour,
          value: 0,
          dayIndex: days.indexOf(day)
        });
      });
    });

    // Aggregate activity data
    activityData.forEach(activity => {
      const date = new Date(activity.timestamp);
      const day = days[date.getDay()];
      const hour = date.getHours();

      // Find the corresponding cell in heatmap data
      const cell = heatmapData.find(d => d.day === day && d.hour === hour);
      if (cell) {
        if (viewType === 'count') {
          cell.value += 1; // Count events
        } else if (viewType === 'duration') {
          cell.value += activity.duration_seconds || 0; // Sum durations
        } else {
          // Course view - count unique students
          const studentId = activity.student_id;
          if (!cell.students) cell.students = new Set();
          cell.students.add(studentId);
          cell.value = cell.students.size;
        }
      }
    });

    return heatmapData;
  };

  // Draw the heatmap visualization
  const drawHeatmap = () => {
    if (!svgRef.current || processedData.length === 0) return;

    // Clear previous SVG content
    d3.select(svgRef.current).selectAll('*').remove();

    // Set up dimensions
    const margin = { top: 30, right: 30, bottom: 70, left: 80 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Create SVG element
    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Define days and hours for axes
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const hours = Array.from({ length: 24 }, (_, i) => i);

    // Create scales
    const x = d3.scaleBand()
      .domain(hours)
      .range([0, width])
      .padding(0.05);

    const y = d3.scaleBand()
      .domain(days)
      .range([0, height])
      .padding(0.05);

    // Create color scale
    const maxValue = d3.max(processedData, d => d.value);

    // Use different color scales based on view type
    let colorScale;
    if (viewType === 'duration') {
      // Use minutes instead of seconds for better readability
      colorScale = d3.scaleSequential(d3.interpolateBlues)
        .domain([0, maxValue / 60]); // Convert to minutes
    } else {
      colorScale = d3.scaleSequential(d3.interpolateBlues)
        .domain([0, maxValue]);
    }

    // Add X axis
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickFormat(h => `${h}:00`))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-65)');

    // Add Y axis
    svg.append('g')
      .call(d3.axisLeft(y));

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', -10)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .text(getChartTitle());

    // Add heatmap cells
    svg.selectAll('rect')
      .data(processedData)
      .enter()
      .append('rect')
      .attr('x', d => x(d.hour))
      .attr('y', d => y(d.day))
      .attr('width', x.bandwidth())
      .attr('height', y.bandwidth())
      .style('fill', d => d.value === 0 ? '#f0f0f0' : colorScale(viewType === 'duration' ? d.value / 60 : d.value))
      .style('stroke', '#fff')
      .style('stroke-width', 1)
      .on('mouseover', function(event, d) {
        // Show tooltip on hover
        d3.select(this).style('stroke', '#333').style('stroke-width', 2);

        // Create tooltip
        const tooltip = d3.select('#heatmap-tooltip');
        tooltip.style('display', 'block');
        tooltip.style('left', `${event.pageX + 10}px`);
        tooltip.style('top', `${event.pageY + 10}px`);

        // Format tooltip content based on view type
        let tooltipContent;
        if (viewType === 'duration') {
          const minutes = Math.floor(d.value / 60);
          const seconds = d.value % 60;
          tooltipContent = `${d.day}, ${d.hour}:00 - ${(d.hour + 1) % 24}:00<br>
            ${t('heatmap.duration')}: ${minutes}m ${seconds}s`;
        } else if (viewType === 'course') {
          tooltipContent = `${d.day}, ${d.hour}:00 - ${(d.hour + 1) % 24}:00<br>
            ${t('heatmap.activeStudents')}: ${d.value}`;
        } else {
          tooltipContent = `${d.day}, ${d.hour}:00 - ${(d.hour + 1) % 24}:00<br>
            ${t('heatmap.activityCount')}: ${d.value}`;
        }

        tooltip.html(tooltipContent);
      })
      .on('mouseout', function() {
        d3.select(this).style('stroke', '#fff').style('stroke-width', 1);
        d3.select('#heatmap-tooltip').style('display', 'none');
      });

    // Add legend
    const legendWidth = 200;
    const legendHeight = 20;

    const legendScale = d3.scaleLinear()
      .domain([0, viewType === 'duration' ? maxValue / 60 : maxValue])
      .range([0, legendWidth]);

    const legend = svg.append('g')
      .attr('transform', `translate(${width - legendWidth}, ${height + 40})`);

    // Legend gradient
    const legendData = Array.from({ length: 100 }, (_, i) => i / 100 * (viewType === 'duration' ? maxValue / 60 : maxValue));

    legend.selectAll('rect')
      .data(legendData)
      .enter()
      .append('rect')
      .attr('x', d => legendScale(d))
      .attr('width', legendWidth / 100)
      .attr('height', legendHeight)
      .style('fill', d => colorScale(d));

    // Legend axis
    const legendAxis = d3.axisBottom(legendScale)
      .ticks(5)
      .tickFormat(d => {
        if (viewType === 'duration') {
          return `${Math.round(d)}m`;
        }
        return d;
      });

    legend.append('g')
      .attr('transform', `translate(0, ${legendHeight})`)
      .call(legendAxis);

    // Legend title
    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .text(getLegendTitle());
  };

  // Get chart title based on view type
  const getChartTitle = () => {
    if (viewType === 'duration') {
      return t('heatmap.durationTitle');
    } else if (viewType === 'count') {
      return t('heatmap.countTitle');
    } else {
      return t('heatmap.courseTitle');
    }
  };

  // Get legend title based on view type
  const getLegendTitle = () => {
    if (viewType === 'duration') {
      return t('heatmap.durationLegend');
    } else if (viewType === 'count') {
      return t('heatmap.countLegend');
    } else {
      return t('heatmap.courseLegend');
    }
  };

  return (
    <Card className="activity-heatmap" loading={loading}>
      <div className="heatmap-header">
        <Title level={4}>
          {t('heatmap.title')}
          <Tooltip title={t('heatmap.info')}>
            <InfoCircleOutlined style={{ marginLeft: 8 }} />
          </Tooltip>
        </Title>

        <div className="heatmap-controls">
          <div className="control-item">
            <Text>{t('heatmap.viewType')}:</Text>
            <Select
              value={viewType}
              onChange={setViewType}
              style={{ width: 150, marginLeft: 8 }}
            >
              <Option value="course">{t('heatmap.activeStudents')}</Option>
              <Option value="count">{t('heatmap.activityCount')}</Option>
              <Option value="duration">{t('heatmap.duration')}</Option>
            </Select>
          </div>

          <div className="control-item">
            <Text>{t('heatmap.resourceType')}:</Text>
            <Select
              value={resourceType}
              onChange={setResourceType}
              style={{ width: 150, marginLeft: 8 }}
            >
              <Option value="all">{t('heatmap.allResources')}</Option>
              <Option value="course">{t('heatmap.course')}</Option>
              <Option value="assignment">{t('heatmap.assignment')}</Option>
              <Option value="file">{t('heatmap.file')}</Option>
              <Option value="video">{t('heatmap.video')}</Option>
              <Option value="quiz">{t('heatmap.quiz')}</Option>
            </Select>
          </div>

          <div className="control-item">
            <Text>{t('heatmap.dateRange')}:</Text>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              allowClear={false}
              style={{ marginLeft: 8 }}
            />
          </div>
        </div>
      </div>

      <div className="heatmap-container">
        {loading ? (
          <div className="heatmap-loading">
            <Spin size="large" />
            <Text>{t('heatmap.loading')}</Text>
          </div>
        ) : processedData.length > 0 ? (
          <>
            <svg ref={svgRef} />
            <div id="heatmap-tooltip" className="heatmap-tooltip" />
          </>
        ) : (
          <Empty description={t('heatmap.noData')} />
        )}
      </div>
    </Card>
  );
};

export default StudentActivityHeatmap;