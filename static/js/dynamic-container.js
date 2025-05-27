/**
 * Dynamic Container Module
 * Implements a right-side container that shows programmatically and takes 30% of the area
 * When shown, the main chat area compresses from 70% to 50% width
 */

class DynamicContainer {
  constructor() {
    this.isVisible = false;
    this.container = null;
    this.chatContainer = null;
    this.init();
    
    // Log initialization if debug logger is available
    if (window.debugLogger) {
      window.debugLogger.log('Dynamic Container initialized', 'system');
    }
  }

  init() {
    // Get the main chat container
    this.chatContainer = document.querySelector('.chat-container');
    if (!this.chatContainer) {
      console.error('Chat container not found');
      return;
    }

    // Create the dynamic container
    this.createDynamicContainer();
    
    // Add event listeners
    this.addEventListeners();
    
    // Add CSS for transitions
    this.addTransitionStyles();
  }

  createDynamicContainer() {
    // Create the dynamic container element
    this.container = document.createElement('div');
    this.container.id = 'dynamic-container';
    this.container.className = 'dynamic-container hidden';
    
    // Create the container structure
    this.container.innerHTML = `
      <div class="dynamic-container-header">
        <h2 id="dynamic-container-title" class="text-lg font-semibold text-gray-900">Dynamic Content</h2>
        <button id="dynamic-container-close" class="close-btn">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      <div id="dynamic-container-content" class="dynamic-container-content">
        <!-- Content will be inserted here -->
      </div>
    `;

    // Insert the container after the chat container
    this.chatContainer.parentNode.insertBefore(this.container, this.chatContainer.nextSibling);
  }

  addTransitionStyles() {
    // Add CSS styles for the dynamic container and transitions
    const style = document.createElement('style');
    style.textContent = `
      /* Dynamic container styles */
      .dynamic-container {
        position: fixed;
        top: 0;
        right: 0;
        width: 30%;
        height: 100vh;
        background: white;
        border-left: 2px solid #e5e7eb;
        box-shadow: -4px 0 6px -1px rgba(0, 0, 0, 0.1);
        transform: translateX(100%);
        transition: transform 0.3s ease-in-out;
        z-index: 30;
        display: flex;
        flex-direction: column;
      }

      .dynamic-container.visible {
        transform: translateX(0);
      }

      .dynamic-container-header {
        padding: 1rem;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        justify-content: between;
        align-items: center;
        background: #f9fafb;
      }

      .dynamic-container-content {
        flex: 1;
        padding: 1rem;
        overflow-y: auto;
      }

      .close-btn {
        padding: 0.25rem;
        border-radius: 0.375rem;
        color: #6b7280;
        hover:color: #374151;
        hover:background-color: #f3f4f6;
        transition: all 0.2s;
      }

      .close-btn:hover {
        color: #374151;
        background-color: #f3f4f6;
      }

      /* Chat container transitions */
      .chat-container {
        transition: width 0.3s ease-in-out, margin 0.3s ease-in-out;
      }

      .chat-container.compressed {
        width: 70% !important;
        margin-left: 0 !important;
        margin-right: auto !important;
      }

      /* Responsive adjustments */
      @media (max-width: 768px) {
        .dynamic-container {
          width: 100%;
        }
        
        .chat-container.compressed {
          width: 100% !important;
          margin: 0 auto !important;
        }
      }

      /* Hyperlink styles for triggering dynamic container */
      .dynamic-trigger {
        cursor: pointer;
        color: #2563eb;
        text-decoration: underline;
        transition: color 0.2s;
      }

      .dynamic-trigger:hover {
        color: #1d4ed8;
      }
      
    `;
    
    document.head.appendChild(style);
  }

  addEventListeners() {
    // Close button event listener
    document.addEventListener('click', (e) => {
      if (e.target.closest('#dynamic-container-close')) {
        this.hide();
      }
    });

    // Listen for hyperlink clicks in chat messages
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');
      if (link && this.shouldTriggerDynamicContainer(link)) {
        e.preventDefault();
        this.handleLinkClick(link);
      }
    });

    // Listen for citation clicks
    document.addEventListener('click', (e) => {
      const citationLink = e.target.closest('.citation-link');
      if (citationLink) {
        e.preventDefault();
        this.handleCitationClick(citationLink);
      }
    });

    // Click outside to close
    document.addEventListener('click', (e) => {
      if (this.isVisible && this.container && !this.container.contains(e.target)) {
        // Check if the click is not on a citation link or any element that should trigger the container
        const isOnCitationLink = e.target.closest('.citation-link');
        const isOnTriggerLink = e.target.closest('a[href]') && 
                               this.shouldTriggerDynamicContainer(e.target.closest('a[href]'));
        
        if (!isOnCitationLink && !isOnTriggerLink) {
          // Log the click-outside event if debug logger is available
          if (window.debugLogger) {
            window.debugLogger.log('Click outside dynamic container detected', 'user-action', {
              target: e.target.tagName,
              containerVisible: this.isVisible
            });
          }
          
          this.hide();
        }
      }
    });

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isVisible) {
        // Log the escape key press if debug logger is available
        if (window.debugLogger) {
          window.debugLogger.log('Escape key pressed to close container', 'user-action');
        }
        
        this.hide();
      }
    });
  }

  shouldTriggerDynamicContainer(link) {
    // Check if the link should trigger the dynamic container
    // You can customize this logic based on your needs
    const href = link.getAttribute('href');
    
    // Trigger for external links (but not citations)
    if (href && href.startsWith('http') && !link.classList.contains('citation-link')) {
      return true;
    }
    
    // Trigger for links with specific classes or data attributes
    if (link.classList.contains('dynamic-trigger') || link.hasAttribute('data-dynamic-content')) {
      return true;
    }
    
    return false;
  }

  handleLinkClick(link) {
    const href = link.getAttribute('href');
    const linkText = link.textContent;
    const dynamicContent = link.getAttribute('data-dynamic-content');
    
    let title = 'Link Details';
    let content = '';
    
    if (dynamicContent) {
      // Use custom content if provided
      title = link.getAttribute('data-dynamic-title') || 'Dynamic Content';
      content = dynamicContent;
    } else if (href && href.startsWith('http')) {
      // Handle external links
      title = 'External Link';
      content = `
        <div class="space-y-4">
          <div>
            <h3 class="font-medium text-gray-900 mb-2">Link Information</h3>
            <p class="text-sm text-gray-600 mb-2"><strong>URL:</strong> ${href}</p>
            <p class="text-sm text-gray-600 mb-4"><strong>Text:</strong> ${linkText}</p>
          </div>
          <div class="border-t pt-4">
            <p class="text-sm text-gray-500 mb-3">This link leads to an external website. Would you like to:</p>
            <div class="space-y-2">
              <button onclick="window.open('${href}', '_blank')" class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                Open in New Tab
              </button>
              <button onclick="navigator.clipboard.writeText('${href}')" class="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors">
                Copy URL
              </button>
            </div>
          </div>
        </div>
      `;
    }
    
    this.show(content, title);
  }

  removeAllHighlights() {
    document.querySelectorAll('.bg-yellow-100').forEach(el => el.classList.remove('bg-yellow-100'));
  }

  handleCitationClick(citationLink) {
    const sourceId = citationLink.getAttribute('data-source-id');
    
    // Log the citation click if debug logger is available
    if (window.debugLogger) {
      window.debugLogger.log('Citation link clicked (dynamic mode)', 'user-action', {
        sourceId: sourceId,
        linkText: citationLink.textContent,
        linkHref: citationLink.getAttribute('href')
      });
    }
    
    // Remove any existing highlights
    this.removeAllHighlights();
    
    // Get source information from the global lastSources
    if (window.lastSources && Array.isArray(window.lastSources)) {
      const sourceIndex = parseInt(sourceId) - 1;
      const source = window.lastSources[sourceIndex];
      
      if (source) {
        let title = `Source [${sourceId}]`;
        let content = '';
        
        if (typeof source === 'string') {
          content = `
            <div class="space-y-4">
              <div>
                <h3 class="font-medium text-gray-900 mb-2">Source Content</h3>
                <div class="bg-gray-50 p-3 rounded text-sm">
                  ${source}
                </div>
              </div>
            </div>
          `;
        } else if (typeof source === 'object') {
          title = source.title || source.id || `Source [${sourceId}]`;
          content = `
            <div class="space-y-4">
              <div>
                <h3 class="font-medium text-gray-900 mb-2">Source Information</h3>
                ${source.title ? `<p class="text-sm text-gray-600 mb-2"><strong>Title:</strong> ${source.title}</p>` : ''}
                ${source.id ? `<p class="text-sm text-gray-600 mb-2"><strong>ID:</strong> ${source.id}</p>` : ''}
              </div>
              ${source.content ? `
                <div>
                  <h4 class="font-medium text-gray-900 mb-2">Content</h4>
                  <div class="bg-gray-50 p-3 rounded text-sm max-h-64 overflow-y-auto">
                    ${source.content}
                  </div>
                </div>
              ` : ''}
            </div>
          `;
        }
        
        // Show the container with the source content
        this.show(content, title);
      }
    }
  }

  show(content, title = 'Dynamic Content') {
    if (!this.container) return;
    
    // Log the show action if debug logger is available
    if (window.debugLogger) {
      window.debugLogger.log('Showing dynamic container', 'ui-state', {
        title: title,
        contentLength: content ? content.length : 0,
        contentType: typeof content
      });
    }
    
    // Set the title and content
    const titleElement = document.getElementById('dynamic-container-title');
    const contentElement = document.getElementById('dynamic-container-content');
    
    if (titleElement) titleElement.textContent = title;
    if (contentElement) contentElement.innerHTML = content;
    
    // Show the container
    this.container.classList.remove('hidden');
    setTimeout(() => {
      this.container.classList.add('visible');
    }, 10);
    
    // Compress the chat container
    this.chatContainer.classList.add('compressed');
    
    this.isVisible = true;
  }

  hide() {
    if (!this.container) return;
    
    // Log the hide action if debug logger is available
    if (window.debugLogger) {
      window.debugLogger.log('Hiding dynamic container', 'ui-state', {
        wasVisible: this.isVisible,
        title: document.getElementById('dynamic-container-title')?.textContent
      });
    }
    
    // Hide the container
    this.container.classList.remove('visible');
    
    // Restore the chat container
    this.chatContainer.classList.remove('compressed');
    
    setTimeout(() => {
      this.container.classList.add('hidden');
    }, 300);
    
    this.isVisible = false;
  }

  // Public API methods
  showContent(content, title) {
    this.show(content, title);
  }

  hideContainer() {
    this.hide();
  }

  isContainerVisible() {
    return this.isVisible;
  }
}

// Initialize the dynamic container when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.dynamicContainer = new DynamicContainer();
});

// Make the class available globally for external use
window.DynamicContainer = DynamicContainer;
