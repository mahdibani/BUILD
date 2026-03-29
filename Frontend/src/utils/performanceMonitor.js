// Performance monitoring utilities

class PerformanceMonitor {
  constructor() {
    this.metrics = {
      initialLoad: null,
      slideTransitions: [],
      imageLoads: [],
      fps: [],
    };
    this.observers = [];
  }

  /**
   * Mark the initial load time
   */
  markInitialLoad() {
    if (window.performance && window.performance.timing) {
      const timing = window.performance.timing;
      const loadTime = timing.loadEventEnd - timing.navigationStart;
      this.metrics.initialLoad = loadTime;
      
      if (loadTime > 1000) {
        console.warn(`Initial load took ${loadTime}ms (target: < 1000ms)`);
      }
    }
  }

  /**
   * Measure slide transition time
   * @param {Function} callback - Transition callback
   * @returns {Promise} Resolves when transition completes
   */
  async measureTransition(callback) {
    const startTime = performance.now();
    
    await callback();
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    this.metrics.slideTransitions.push(duration);
    
    // Keep only last 20 transitions
    if (this.metrics.slideTransitions.length > 20) {
      this.metrics.slideTransitions.shift();
    }
    
    if (duration > 300) {
      console.warn(`Slide transition took ${duration.toFixed(2)}ms (target: < 300ms)`);
    }
    
    return duration;
  }

  /**
   * Measure image load time
   * @param {string} url - Image URL
   * @param {number} startTime - Load start time
   */
  recordImageLoad(url, startTime) {
    const duration = performance.now() - startTime;
    this.metrics.imageLoads.push({ url, duration });
    
    // Keep only last 50 image loads
    if (this.metrics.imageLoads.length > 50) {
      this.metrics.imageLoads.shift();
    }
  }

  /**
   * Start FPS monitoring
   * @returns {Function} Stop function
   */
  startFPSMonitoring() {
    let frameCount = 0;
    let lastTime = performance.now();
    let animationId;

    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime >= lastTime + 1000) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
        this.metrics.fps.push(fps);
        
        // Keep only last 60 seconds of FPS data
        if (this.metrics.fps.length > 60) {
          this.metrics.fps.shift();
        }
        
        if (fps < 60) {
          console.warn(`FPS dropped to ${fps} (target: 60fps)`);
        }
        
        frameCount = 0;
        lastTime = currentTime;
      }
      
      animationId = requestAnimationFrame(measureFPS);
    };

    animationId = requestAnimationFrame(measureFPS);

    // Return stop function
    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }

  /**
   * Get performance report
   * @returns {Object} Performance metrics
   */
  getReport() {
    const avgTransitionTime = this.metrics.slideTransitions.length > 0
      ? this.metrics.slideTransitions.reduce((a, b) => a + b, 0) / this.metrics.slideTransitions.length
      : 0;

    const avgImageLoadTime = this.metrics.imageLoads.length > 0
      ? this.metrics.imageLoads.reduce((sum, img) => sum + img.duration, 0) / this.metrics.imageLoads.length
      : 0;

    const avgFPS = this.metrics.fps.length > 0
      ? this.metrics.fps.reduce((a, b) => a + b, 0) / this.metrics.fps.length
      : 0;

    const minFPS = this.metrics.fps.length > 0
      ? Math.min(...this.metrics.fps)
      : 0;

    return {
      initialLoad: this.metrics.initialLoad,
      avgTransitionTime: avgTransitionTime.toFixed(2),
      avgImageLoadTime: avgImageLoadTime.toFixed(2),
      avgFPS: avgFPS.toFixed(1),
      minFPS,
      totalTransitions: this.metrics.slideTransitions.length,
      totalImageLoads: this.metrics.imageLoads.length,
      meetsTargets: {
        initialLoad: this.metrics.initialLoad ? this.metrics.initialLoad < 1000 : null,
        transitions: avgTransitionTime < 300,
        fps: avgFPS >= 60,
      },
    };
  }

  /**
   * Reset all metrics
   */
  reset() {
    this.metrics = {
      initialLoad: null,
      slideTransitions: [],
      imageLoads: [],
      fps: [],
    };
  }
}

// Singleton instance
const performanceMonitor = new PerformanceMonitor();

export default performanceMonitor;
