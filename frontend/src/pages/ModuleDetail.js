import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';

function ModuleDetail() {
  const { moduleId } = useParams();
  const [module, setModule] = useState(null);
  const [contentItems, setContentItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        // For a real implementation, you would fetch the module details
        // Here we're just getting content items
        const items = await api.getModuleContent(moduleId);
        setContentItems(items);

        // In a real app, you'd get module details from an API
        // For now, we'll create dummy data
        setModule({
          id: moduleId,
          title: "Module",
          description: "Module description"
        });
      } catch (err) {
        setError('Failed to load module content');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [moduleId]);

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading module content...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
        <p className="mt-2">
          <Link to="/courses" className="text-red-700 font-bold">Return to courses</Link>
        </p>
      </div>
    );
  }

  if (!module) {
    return (
      <div className="text-center py-10">
        <p className="text-xl text-gray-700">Module not found</p>
        <p className="mt-2">
          <Link to="/courses" className="text-blue-500 hover:text-blue-700">Return to courses</Link>
        </p>
      </div>
    );
  }

  const renderContentItem = (item) => {
    switch (item.content_type) {
      case 'text':
        return (
          <div className="prose max-w-none">
            {item.content}
          </div>
        );
      case 'video':
        return (
          <div className="aspect-w-16 aspect-h-9">
            <div className="bg-gray-200 p-4 text-center">
              <p>Video content: {item.content}</p>
              <p className="text-sm text-gray-500">(Video player would be implemented here)</p>
            </div>
          </div>
        );
      case 'file':
        return (
          <div className="p-4 border border-gray-200 rounded">
            <p>File: {item.content}</p>
            <button className="mt-2 text-blue-500 hover:text-blue-700">
              Download File
            </button>
          </div>
        );
      default:
        return (
          <div className="p-4 border border-gray-200 rounded">
            <p>Content: {item.content}</p>
          </div>
        );
    }
  };

  return (
    <div>
      <div className="mb-6">
        <Link to={`/courses/${module.course_id || 1}`} className="text-blue-500 hover:text-blue-700">
          &larr; Back to Course
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h1 className="text-3xl font-bold mb-2">{module.title}</h1>
        <p className="text-gray-600 mb-4">{module.description}</p>
      </div>

      <h2 className="text-2xl font-bold mb-4">Content</h2>

      {contentItems.length === 0 ? (
        <p className="text-gray-500">No content available for this module.</p>
      ) : (
        <div className="space-y-6">
          {contentItems.map(item => (
            <div key={item.id} className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">{item.title}</h3>
              {renderContentItem(item)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ModuleDetail;