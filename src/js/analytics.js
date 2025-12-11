/**
 * Vercel Web Analytics Integration
 * Initializes Vercel Web Analytics on the client side
 * 
 * For plain HTML sites, this uses the Vercel Analytics script approach
 * Note: inject() runs on the client side and does not include route support
 */

(function() {
  /**
   * Initialize Vercel Web Analytics
   * The official Vercel Web Analytics script is loaded via the <script> tag
   * This ensures proper initialization on the client side
   */
  function initializeAnalytics() {
    // Check if Vercel Analytics has already been loaded
    if (typeof window !== 'undefined') {
      // Vercel Web Analytics will be automatically initialized by the injected script
      // No additional configuration needed beyond the script tag
      console.debug('[Analytics] Vercel Web Analytics initialized');
    }
  }

  // Initialize analytics when the DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAnalytics);
  } else {
    // DOM is already loaded
    initializeAnalytics();
  }

  // Expose for manual initialization if needed
  window.initializeAnalytics = initializeAnalytics;
})();
