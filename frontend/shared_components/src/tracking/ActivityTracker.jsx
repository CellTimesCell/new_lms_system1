// Activity Tracking module for frontend applications
import { v4 as uuidv4 } from 'uuid';

/**
 * ActivityTracker class for monitoring and recording student activity
 */
class ActivityTracker {
  constructor() {
    this.isEnabled = true;
    this.userId = null;
    this.sessionStartTime = new Date();
    this.lastActivityTime = new Date();
    this.currentPagePath = window.location.pathname;
    this.currentPageStartTime = new Date();
    this.currentResourceType = null;
    this.currentResourceId = null;
    this.activityBuffer = [];
    this.bufferSize = 10; // Number of events to batch before sending
    this.flushInterval = 30000; // 30 seconds
    this.idleThreshold = 300000; // 5 minutes
    this.idleCheckInterval = 60000; // 1 minute
    this.apiEndpoint = '/api/analytics/track';

    // Setup flush interval
    this.flushIntervalId = setInterval(() => this.flush(), this.flushInterval);

    // Setup idle detection
    this.idleIntervalId = setInterval(() => this.checkIdle(), this.idleCheckInterval);

    // Bind event handlers
    this.handlePageChange = this.handlePageChange.bind(this);
    this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
    this.handleUserActivity = this.handleUserActivity.bind(this);
    this.handleBeforeUnload = this.handleBeforeUnload.bind(this);

    // Attach event listeners
    this.attachEventListeners();
  }

  /**
   * Initialize the tracker with user information
   *
   * @param {number} userId - The user ID
   * @param {object} options - Configuration options
   */
  init(userId, options = {}) {
    this.userId = userId;

    // Apply custom options
    if (options.bufferSize) this.bufferSize = options.bufferSize;
    if (options.flushInterval) {
      this.flushInterval = options.flushInterval;
      clearInterval(this.flushIntervalId);
      this.flushIntervalId = setInterval(() => this.flush(), this.flushInterval);
    }
    if (options.apiEndpoint) this.apiEndpoint = options.apiEndpoint;
    if (options.idleThreshold) this.idleThreshold = options.idleThreshold;

    // Track initial page view
    this.trackPageView(this.currentPagePath);

    console.log('Activity tracking initialized for user', userId);
  }

  /**
   * Attach browser event listeners
   */
  attachEventListeners() {
    // Page visibility changes
    document.addEventListener('visibilitychange', this.handleVisibilityChange);

    // User activity events
    document.addEventListener('click', this.handleUserActivity);
    document.addEventListener('keydown', this.handleUserActivity);
    document.addEventListener('mousemove', this.handleUserActivity);
    document.addEventListener('scroll', this.handleUserActivity);

    // Page navigation in SPA
    window.addEventListener('popstate', this.handlePageChange);

    // Before unload event
    window.addEventListener('beforeunload', this.handleBeforeUnload);

    // Intercept history methods for SPA navigation
    const originalPushState = history.pushState;
    history.pushState = function() {
      originalPushState.apply(this, arguments);
      window.dispatchEvent(new Event('popstate'));
    };

    const originalReplaceState = history.replaceState;
    history.replaceState = function() {
      originalReplaceState.apply(this, arguments);
      window.dispatchEvent(new Event('popstate'));
    };
  }

  /**
   * Handle page changes in SPA
   */
  handlePageChange() {
    // Calculate duration on previous page
    const now = new Date();
    const duration = Math.round((now - this.currentPageStartTime) / 1000);

    // Track page exit
    this.trackEvent('page_exit', 'page', this.currentPagePath, {
      duration_seconds: duration
    });

    // Update current page info
    this.currentPagePath = window.location.pathname;
    this.currentPageStartTime = now;

    // Track new page view
    this.trackPageView(this.currentPagePath);
  }

  /**
   * Handle visibility change events (tab focus/blur)
   */
  handleVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      // User switched away from tab
      const now = new Date();
      const duration = Math.round((now - this.currentPageStartTime) / 1000);

      this.trackEvent('tab_blur', 'page', this.currentPagePath, {
        duration_seconds: duration
      });
    } else {
      // User returned to tab
      this.trackEvent('tab_focus', 'page', this.currentPagePath);
      this.currentPageStartTime = new Date(); // Reset timer
    }
  }

  /**
   * Handle user activity events
   */
  handleUserActivity() {
    this.lastActivityTime = new Date();
  }

  /**
   * Handle page unload event
   */
  handleBeforeUnload() {
    // Calculate final duration
    const now = new Date();
    const pageDuration = Math.round((now - this.currentPageStartTime) / 1000);
    const sessionDuration = Math.round((now - this.sessionStartTime) / 1000);

    // Track page exit
    this.trackEvent('page_exit', 'page', this.currentPagePath, {
      duration_seconds: pageDuration
    });

    // Track session end
    this.trackEvent('session_end', 'session', null, {
      duration_seconds: sessionDuration
    });

    // Force flush sync
    this.flushSync();
  }

  /**
   * Check if user is idle
   */
  checkIdle() {
    const now = new Date();
    const timeSinceLastActivity = now - this.lastActivityTime;

    if (timeSinceLastActivity >= this.idleThreshold) {
      // User is idle
      this.trackEvent('user_idle', 'session', null, {
        idle_time_seconds: Math.round(timeSinceLastActivity / 1000)
      });
    }
  }

  /**
   * Track a page view
   *
   * @param {string} path - The page path
   * @param {object} metadata - Additional metadata
   */
  trackPageView(path, metadata = {}) {
    if (!this.isEnabled || !this.userId) return;

    this.trackEvent('page_view', 'page', path, {
      referrer: document.referrer,
      title: document.title,
      ...metadata
    });
  }

  /**
   * Track a resource interaction
   *
   * @param {string} resourceType - Type of resource (file, video, quiz, etc.)
   * @param {string|number} resourceId - ID of the resource
   * @param {string} action - The action (view, download, etc.)
   * @param {object} metadata - Additional metadata
   */
  trackResourceInteraction(resourceType, resourceId, action, metadata = {}) {
    if (!this.isEnabled || !this.userId) return;

    // Set current resource context
    this.currentResourceType = resourceType;
    this.currentResourceId = resourceId;

    this.trackEvent(action, resourceType, resourceId, metadata);
  }

  /**
   * Start tracking interaction with a resource
   *
   * @param {string} resourceType - Type of resource
   * @param {string|number} resourceId - ID of the resource
   * @param {object} metadata - Additional metadata
   */
  startResourceTracking(resourceType, resourceId, metadata = {}) {
    if (!this.isEnabled || !this.userId) return;

    // Set current resource context
    this.currentResourceType = resourceType;
    this.currentResourceId = resourceId;

    // Record start time
    this.resourceStartTime = new Date();

    this.trackEvent('resource_start', resourceType, resourceId, metadata);

    return this.resourceStartTime;
  }

  /**
   * End tracking interaction with a resource
   *
   * @param {object} metadata - Additional metadata
   */
  endResourceTracking(metadata = {}) {
    if (!this.isEnabled || !this.userId || !this.resourceStartTime) return;

    const now = new Date();
    const duration = Math.round((now - this.resourceStartTime) / 1000);

    this.trackEvent('resource_end', this.currentResourceType, this.currentResourceId, {
      duration_seconds: duration,
      ...metadata
    });

    // Clear resource context
    this.resourceStartTime = null;
    this.currentResourceType = null;
    this.currentResourceId = null;

    return duration;
  }

  /**
   * Track a general event
   *
   * @param {string} eventType - Type of event
   * @param {string} resourceType - Type of resource
   * @param {string|number} resourceId - ID of the resource
   * @param {object} metadata - Additional metadata
   */
  trackEvent(eventType, resourceType, resourceId, metadata = {}) {
    if (!this.isEnabled || !this.userId) return;

    const event = {
      event_id: uuidv4(),
      student_id: this.userId,
      event_type: eventType,
      resource_type: resourceType,
      resource_id: resourceId,
      timestamp: new Date().toISOString(),
      ip_address: null, // Will be set server-side
      user_agent: navigator.userAgent,
      duration_seconds: metadata.duration_seconds || 0,
      metadata: { ...metadata }
    };

    // Add to buffer
    this.activityBuffer.push(event);

    // Flush if buffer is full
    if (this.activityBuffer.length >= this.bufferSize) {
      this.flush();
    }

    return event;
  }

  /**
   * Flush activity buffer to server
   */
  async flush() {
    if (this.activityBuffer.length === 0) return;

    try {
      const eventsToSend = [...this.activityBuffer];
      this.activityBuffer = [];

      // Send events in batch
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventsToSend),
        // Keep-alive to prevent connection being closed
        keepalive: true
      });

      if (!response.ok) {
        // If send fails, add back to buffer
        this.activityBuffer = [...eventsToSend, ...this.activityBuffer];
        console.error('Failed to send activity data', response.statusText);
      }
    } catch (error) {
      // If send fails, add back to buffer
      this.activityBuffer = [...eventsToSend, ...this.activityBuffer];
      console.error('Error sending activity data', error);
    }
  }

  /**
   * Flush activity buffer synchronously (for page unload)
   */
  flushSync() {
    if (this.activityBuffer.length === 0) return;

    try {
      const eventsToSend = [...this.activityBuffer];
      this.activityBuffer = [];

      // Use synchronous XMLHttpRequest
      const xhr = new XMLHttpRequest();
      xhr.open('POST', this.apiEndpoint, false); // false for sync
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.send(JSON.stringify(eventsToSend));

      if (xhr.status !== 200) {
        console.error('Failed to send activity data', xhr.statusText);
      }
    } catch (error) {
      console.error('Error sending activity data', error);
    }
  }

  /**
   * Disable activity tracking
   */
  disable() {
    this.isEnabled = false;

    // Flush any pending events
    this.flush();

    // Clear intervals
    clearInterval(this.flushIntervalId);
    clearInterval(this.idleIntervalId);

    console.log('Activity tracking disabled');
  }

  /**
   * Enable activity tracking
   */
  enable() {
    this.isEnabled = true;

    // Restart intervals
    this.flushIntervalId = setInterval(() => this.flush(), this.flushInterval);
    this.idleIntervalId = setInterval(() => this.checkIdle(), this.idleCheckInterval);

    console.log('Activity tracking enabled');
  }

  /**
   * Clean up resources
   */
  cleanup() {
    // Flush any pending events
    this.flush();

    // Clear intervals
    clearInterval(this.flushIntervalId);
    clearInterval(this.idleIntervalId);

    // Remove event listeners
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    document.removeEventListener('click', this.handleUserActivity);
    document.removeEventListener('keydown', this.handleUserActivity);
    document.removeEventListener('mousemove', this.handleUserActivity);
    document.removeEventListener('scroll', this.handleUserActivity);
    window.removeEventListener('popstate', this.handlePageChange);
    window.removeEventListener('beforeunload', this.handleBeforeUnload);

    console.log('Activity tracking cleaned up');
  }
}

// Create singleton instance
const activityTracker = new ActivityTracker();

export default activityTracker;