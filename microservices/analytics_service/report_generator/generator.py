# microservices/analytics_service/report_generator/generator.py
import uuid
import json
import logging
import os
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

from infrastructure.databases.database_config import get_clickhouse_client
from microservices.analytics_service.schemas import ReportRequest, ReportType

# Initialize logging
logger = logging.getLogger(__name__)

# Configure storage for generated reports
REPORT_STORAGE_PATH = os.getenv("REPORT_STORAGE_PATH", "./reports")
REPORT_URL_BASE = os.getenv("REPORT_URL_BASE", "http://localhost:8000/reports/files")

# Ensure storage directory exists
os.makedirs(REPORT_STORAGE_PATH, exist_ok=True)


async def generate_report(report_request: ReportRequest) -> str:
    """
    Generate an analytics report based on the request parameters

    Args:
        report_request: Report request parameters

    Returns:
        report_id: Unique ID of the generated report
    """
    # Generate unique report ID
    report_id = str(uuid.uuid4())

    try:
        # Get ClickHouse client
        ch_client = get_clickhouse_client()

        # Insert report record with status 'processing'
        query = """
        INSERT INTO reports
        (report_id, report_type, created_by, parameters, status, created_at)
        VALUES
        """
        values = (
            report_id,
            report_request.report_type,
            report_request.created_by,
            json.dumps(report_request.parameters),
            'processing',
            datetime.utcnow()
        )
        ch_client.execute(query, [values])

        # Process report based on type
        result_url = None

        if report_request.report_type == ReportType.STUDENT_ACTIVITY:
            result_url = await generate_student_activity_report(
                ch_client,
                report_id,
                report_request.parameters
            )
        elif report_request.report_type == ReportType.COURSE_ENGAGEMENT:
            result_url = await generate_course_engagement_report(
                ch_client,
                report_id,
                report_request.parameters
            )
        elif report_request.report_type == ReportType.ASSIGNMENT_COMPLETION:
            result_url = await generate_assignment_completion_report(
                ch_client,
                report_id,
                report_request.parameters
            )
        else:
            raise ValueError(f"Unsupported report type: {report_request.report_type}")

        # Update report status to 'completed'
        update_query = """
        ALTER TABLE reports
        UPDATE status = 'completed', completed_at = %(completed_at)s, result_url = %(result_url)s
        WHERE report_id = %(report_id)s
        """
        ch_client.execute(
            update_query,
            {
                'completed_at': datetime.utcnow(),
                'result_url': result_url,
                'report_id': report_id
            }
        )

        logger.info(f"Report {report_id} generated successfully")
        return report_id

    except Exception as e:
        # Update report status to 'failed'
        try:
            ch_client = get_clickhouse_client()
            update_query = """
            ALTER TABLE reports
            UPDATE status = 'failed', error_message = %(error_message)s
            WHERE report_id = %(report_id)s
            """
            ch_client.execute(
                update_query,
                {
                    'error_message': str(e),
                    'report_id': report_id
                }
            )
        except Exception as update_error:
            logger.error(f"Error updating report status: {str(update_error)}")

        logger.error(f"Error generating report: {str(e)}")
        raise


async def generate_student_activity_report(ch_client, report_id, parameters):
    """
    Generate a student activity report

    Args:
        ch_client: ClickHouse client
        report_id: Report ID
        parameters: Report parameters

    Returns:
        result_url: URL to access the generated report
    """
    student_id = parameters.get('student_id')
    start_date = parameters.get('start_date')
    end_date = parameters.get('end_date', datetime.utcnow().isoformat())

    if not student_id:
        raise ValueError("student_id is required for student activity report")

    if not start_date:
        # Default to 30 days ago if not specified
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

    # Fetch student activity data
    query = f"""
    SELECT 
        toDate(timestamp) as date,
        event_type,
        resource_type,
        count() as event_count,
        sum(duration_seconds) as duration
    FROM activity_events
    WHERE student_id = {student_id}
    AND timestamp BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY date, event_type, resource_type
    ORDER BY date
    """

    results = ch_client.execute(query)

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(
        results,
        columns=['date', 'event_type', 'resource_type', 'event_count', 'duration']
    )

    # Generate visualizations
    report_file = f"{REPORT_STORAGE_PATH}/{report_id}_student_activity.pdf"

    # Set up the PDF file
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(report_file) as pdf:
        # Create a figure for event counts over time
        plt.figure(figsize=(12, 6))
        pivot_df = df.pivot_table(
            index='date',
            columns='event_type',
            values='event_count',
            aggfunc='sum'
        ).fillna(0)

        pivot_df.plot(kind='line', marker='o')
        plt.title(f'Activity Events Over Time for Student {student_id}')
        plt.xlabel('Date')
        plt.ylabel('Number of Events')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # Create a figure for time spent by resource type
        plt.figure(figsize=(10, 8))
        resource_df = df.groupby('resource_type')['duration'].sum().reset_index()
        sns.barplot(x='resource_type', y='duration', data=resource_df)
        plt.title(f'Time Spent by Resource Type for Student {student_id}')
        plt.xlabel('Resource Type')
        plt.ylabel('Duration (seconds)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # Create a summary page
        plt.figure(figsize=(8.5, 11))
        plt.axis('off')
        plt.text(0.5, 0.95, 'Student Activity Report Summary', ha='center', fontsize=16, fontweight='bold')
        plt.text(0.5, 0.9, f'Student ID: {student_id}', ha='center')
        plt.text(0.5, 0.85, f'Period: {start_date[:10]} to {end_date[:10]}', ha='center')

        # Add summary statistics
        total_events = df['event_count'].sum()
        total_duration = df['duration'].sum()
        avg_duration_per_day = total_duration / len(df['date'].unique()) if len(df['date'].unique()) > 0 else 0

        summary_text = (
            f"Total Activities: {total_events}\n"
            f"Total Time Spent: {total_duration / 3600:.2f} hours\n"
            f"Average Daily Time: {avg_duration_per_day / 3600:.2f} hours\n\n"
            f"Top Resource Types:\n"
        )

        for i, (res_type, duration) in enumerate(resource_df.sort_values('duration', ascending=False).values[:5]):
            summary_text += f"{i + 1}. {res_type}: {duration / 3600:.2f} hours\n"

        plt.text(0.1, 0.7, summary_text, va='top', fontsize=12)
        pdf.savefig()
        plt.close()

    # Return the URL to access the report
    result_url = f"{REPORT_URL_BASE}/{report_id}_student_activity.pdf"
    return result_url


async def generate_course_engagement_report(ch_client, report_id, parameters):
    """
    Generate a course engagement report

    Args:
        ch_client: ClickHouse client
        report_id: Report ID
        parameters: Report parameters

    Returns:
        result_url: URL to access the generated report
    """
    course_id = parameters.get('course_id')
    start_date = parameters.get('start_date')
    end_date = parameters.get('end_date', datetime.utcnow().isoformat())

    if not course_id:
        raise ValueError("course_id is required for course engagement report")

    if not start_date:
        # Default to 30 days ago if not specified
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

    # Fetch course engagement data
    query = f"""
    SELECT 
        toDate(timestamp) as date,
        student_id,
        count() as event_count,
        sum(duration_seconds) as duration
    FROM activity_events
    WHERE resource_type = 'course'
    AND resource_id = '{course_id}'
    AND timestamp BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY date, student_id
    ORDER BY date
    """

    results = ch_client.execute(query)

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(
        results,
        columns=['date', 'student_id', 'event_count', 'duration']
    )

    # Generate visualizations
    report_file = f"{REPORT_STORAGE_PATH}/{report_id}_course_engagement.pdf"

    # Set up the PDF file
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(report_file) as pdf:
        # Create a figure for daily engagement
        plt.figure(figsize=(12, 6))
        daily_df = df.groupby('date')[['event_count', 'duration']].sum().reset_index()

        fig, ax1 = plt.subplots(figsize=(12, 6))

        color = 'tab:blue'
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Number of Events', color=color)
        ax1.plot(daily_df['date'], daily_df['event_count'], color=color, marker='o')
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Duration (hours)', color=color)
        ax2.plot(daily_df['date'], daily_df['duration'] / 3600, color=color, marker='x')
        ax2.tick_params(axis='y', labelcolor=color)

        plt.title(f'Daily Engagement for Course {course_id}')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # Create a figure for student engagement comparison
        plt.figure(figsize=(12, 8))
        student_df = df.groupby('student_id')[['event_count', 'duration']].sum().reset_index()
        student_df = student_df.sort_values('duration', ascending=False).head(10)  # Top 10 students

        plt.figure(figsize=(12, 8))
        sns.barplot(x='student_id', y='duration', data=student_df)
        plt.title(f'Top 10 Students by Engagement for Course {course_id}')
        plt.xlabel('Student ID')
        plt.ylabel('Total Duration (seconds)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # Create a summary page
        plt.figure(figsize=(8.5, 11))
        plt.axis('off')
        plt.text(0.5, 0.95, 'Course Engagement Report Summary', ha='center', fontsize=16, fontweight='bold')
        plt.text(0.5, 0.9, f'Course ID: {course_id}', ha='center')
        plt.text(0.5, 0.85, f'Period: {start_date[:10]} to {end_date[:10]}', ha='center')

        # Add summary statistics
        total_events = df['event_count'].sum()
        total_duration = df['duration'].sum()
        unique_students = df['student_id'].nunique()

        summary_text = (
            f"Total Activities: {total_events}\n"
            f"Total Time Spent: {total_duration / 3600:.2f} hours\n"
            f"Unique Active Students: {unique_students}\n"
            f"Average Time per Student: {total_duration / (unique_students * 3600):.2f} hours\n\n"
            f"Top Engaged Students:\n"
        )

        for i, (stud_id, _, duration) in enumerate(student_df[['student_id', 'event_count', 'duration']].values[:5]):
            summary_text += f"{i + 1}. Student {stud_id}: {duration / 3600:.2f} hours\n"

        plt.text(0.1, 0.7, summary_text, va='top', fontsize=12)
        pdf.savefig()
        plt.close()

    # Return the URL to access the report
    result_url = f"{REPORT_URL_BASE}/{report_id}_course_engagement.pdf"
    return result_url


async def generate_assignment_completion_report(ch_client, report_id, parameters):
    """
    Generate an assignment completion report

    Args:
        ch_client: ClickHouse client
        report_id: Report ID
        parameters: Report parameters

    Returns:
        result_url: URL to access the generated report
    """
    course_id = parameters.get('course_id')

    if not course_id:
        raise ValueError("course_id is required for assignment completion report")

    # Fetch assignment data - this query would need to join with the SQL database
    # In a real implementation, this would require a more complex data flow that pulls
    # data from PostgreSQL, processes it, and possibly stores results in ClickHouse

    # Simulated results for demonstration
    # In a real implementation, you would implement a database connection to the PostgreSQL database
    # to get this information or store completed assignment data in ClickHouse

    # This is a placeholder - you would replace this with actual DB queries
    import random
    assignments = [
        {'id': i, 'title': f'Assignment {i}',
         'due_date': (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()}
        for i in range(1, 6)
    ]

    students = [i for i in range(1, 11)]

    completion_data = []
    for assignment in assignments:
        for student in students:
            if random.random() > 0.2:  # 80% completion rate
                submitted_date = datetime.fromisoformat(assignment['due_date']) - timedelta(days=random.randint(0, 3))
                completion_data.append({
                    'assignment_id': assignment['id'],
                    'student_id': student,
                    'submitted_at': submitted_date.isoformat(),
                    'on_time': submitted_date <= datetime.fromisoformat(assignment['due_date']),
                    'score': random.randint(60, 100)
                })

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(completion_data)
    assignments_df = pd.DataFrame(assignments)

    # Generate visualizations
    report_file = f"{REPORT_STORAGE_PATH}/{report_id}_assignment_completion.pdf"

    # Set up the PDF file
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(report_file) as pdf:
        # Create a figure for completion rates
        plt.figure(figsize=(12, 6))
        completion_rates = []

        for assignment in assignments:
            completed = df[df['assignment_id'] == assignment['id']].shape[0]
            completion_rates.append({
                'assignment_id': assignment['id'],
                'title': assignment['title'],
                'completion_rate': completed / len(students) * 100
            })

        completion_df = pd.DataFrame(completion_rates)
        sns.barplot(x='assignment_id', y='completion_rate', data=completion_df)
        plt.title(f'Assignment Completion Rates for Course {course_id}')
        plt.xlabel('Assignment ID')
        plt.ylabel('Completion Rate (%)')
        plt.ylim(0, 100)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # Create a figure for on-time submissions
        plt.figure(figsize=(12, 6))
        on_time_counts = df.groupby('assignment_id')['on_time'].value_counts().unstack().fillna(0)
        on_time_counts.columns = ['Late', 'On Time']

        ax = on_time_counts.plot(kind='bar', stacked=True, figsize=(12, 6))
        plt.title(f'On-Time vs. Late Submissions for Course {course_id}')
        plt.xlabel('Assignment ID')
        plt.ylabel('Number of Submissions')
        plt.legend(title='Submission Status')

        # Add text labels on each bar
        for c in ax.containers:
            labels = [int(v) if v > 0 else '' for v in c.datavalues]
            ax.bar_label(c, labels=labels, label_type='center')

        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # Create a figure for score distribution
        plt.figure(figsize=(12, 6))
        sns.boxplot(x='assignment_id', y='score', data=df)
        plt.title(f'Score Distributions for Course {course_id} Assignments')
        plt.xlabel('Assignment ID')
        plt.ylabel('Score')
        plt.ylim(0, 100)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # Create a summary page
        plt.figure(figsize=(8.5, 11))
        plt.axis('off')
        plt.text(0.5, 0.95, 'Assignment Completion Report Summary', ha='center', fontsize=16, fontweight='bold')
        plt.text(0.5, 0.9, f'Course ID: {course_id}', ha='center')

        # Add summary statistics
        total_submissions = len(df)
        on_time_submissions = df[df['on_time'] == True].shape[0]
        late_submissions = total_submissions - on_time_submissions

        summary_text = (
            f"Total Assignments: {len(assignments)}\n"
            f"Total Students: {len(students)}\n"
            f"Total Submissions: {total_submissions}\n"
            f"On-Time Submissions: {on_time_submissions} ({on_time_submissions / total_submissions * 100:.1f}%)\n"
            f"Late Submissions: {late_submissions} ({late_submissions / total_submissions * 100:.1f}%)\n\n"
            f"Average Scores by Assignment:\n"
        )

        avg_scores = df.groupby('assignment_id')['score'].mean()
        for assignment_id, avg_score in avg_scores.items():
            assignment_title = assignments_df[assignments_df['id'] == assignment_id]['title'].values[0]
            summary_text += f"• {assignment_title}: {avg_score:.1f}\n"

        plt.text(0.1, 0.7, summary_text, va='top', fontsize=12)
        pdf.savefig()
        plt.close()

    # Return the URL to access the report
    result_url = f"{REPORT_URL_BASE}/{report_id}_assignment_completion.pdf"
    return result_url