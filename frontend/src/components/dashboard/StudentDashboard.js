import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

function StudentDashboard({ profile }) {
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [availableCourses, setAvailableCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        // Get enrolled courses
        const enrollments = await api.getMyEnrollments();

        // Get all published courses
        const courses = await api.getCourses();

        // Filter enrolled courses
        const enrolledCourseIds = enrollments.map(e => e.course_id);
        const enrolled = courses.filter(course => enrolledCourseIds.includes(course.id));

        // Filter available courses (not yet enrolled)
        const available = courses.filter(course =>
          course.is_published && !enrolledCourseIds.includes(course.id)
        );

        setEnrolledCourses(enrolled);
        setAvailableCourses(available);
      } catch (err) {
        setError('Failed to load courses');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return <div className="spinner"></div>;
  }

  return (
    <div>
      <section className="mb-10">
        <h2 className="text-2xl font-bold mb-4">My Courses</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {enrolledCourses.length === 0 ? (
          <p className="text-gray-500">You are not enrolled in any courses yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {enrolledCourses.map(course => (
              <div key={course.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="p-4">
                  <h3 className="text-xl font-semibold mb-2">{course.title}</h3>
                  <p className="text-gray-600 mb-4">{course.description}</p>
                  <Link
                    to={`/courses/${course.id}`}
                    className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"
                  >
                    Go to Course
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Available Courses</h2>

        {availableCourses.length === 0 ? (
          <p className="text-gray-500">No other courses are available at this time.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {availableCourses.map(course => (
              <div key={course.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="p-4">
                  <h3 className="text-xl font-semibold mb-2">{course.title}</h3>
                  <p className="text-gray-600 mb-4">{course.description}</p>
                  <button
                    onClick={() => api.enrollInCourse(course.id)
                      .then(() => {
                        // Update course lists after enrollment
                        setEnrolledCourses([...enrolledCourses, course]);
                        setAvailableCourses(availableCourses.filter(c => c.id !== course.id));
                      })
                      .catch(err => {
                        setError('Failed to enroll in course');
                        console.error(err);
                      })
                    }
                    className="bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded"
                  >
                    Enroll Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default StudentDashboard;