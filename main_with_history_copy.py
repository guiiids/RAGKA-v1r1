"""
Modified version of main.py that uses FlaskRAGAssistantWithHistory
to maintain conversation history between requests
"""
print("Running:", __file__)
import traceback
from flask import Flask, request, jsonify, render_template_string, Response, send_from_directory, session
import json
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
load_dotenv() 
sas_token = os.getenv("SAS_TOKEN", "")

# Import the RAG assistant with history
from rag_assistant_with_history_copy import FlaskRAGAssistantWithHistory
from db_manager import DatabaseManager

# Configure logging
logger = logging.getLogger(__name__)
# Clear any existing handlers
if logger.handlers:
    logger.handlers.clear()
# Add file handler with absolute path
file_handler = logging.FileHandler('app_with_history.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# Stream logs to stdout for visibility
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Add JSON-formatted rotating file handlers for usage and error logs
json_formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')

# Determine log base directory (container vs local)
LOG_BASE = os.getenv('LOG_BASE', 'logs')
# Ensure log directories exist
usage_log_path = os.path.join(LOG_BASE, 'usage', 'usage.log')
error_log_path = os.path.join(LOG_BASE, 'errors', 'error.log')
os.makedirs(os.path.dirname(usage_log_path), exist_ok=True)
os.makedirs(os.path.dirname(error_log_path), exist_ok=True)

usage_handler = RotatingFileHandler(usage_log_path, maxBytes=10485760, backupCount=5)
usage_handler.setLevel(logging.INFO)
usage_handler.setFormatter(json_formatter)
logger.addHandler(usage_handler)

error_handler = RotatingFileHandler(error_log_path, maxBytes=10485760, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(json_formatter)
logger.addHandler(error_handler)

logger.setLevel(logging.DEBUG)
import os
print(os.path.abspath(__file__))

file_executed = os.path.abspath(__file__)

# Log startup message to verify logging is working
logger.info("Flask RAG application with conversation history starting up")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key-for-sessions")

# Dictionary to store RAG assistant instances by session ID
rag_assistants = {}

# Serve static files from the 'assets' folder
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# HTML template with Tailwind CSS (same as in main.py)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SAGE Knowledge Navigator</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style id="custom-styles">
    body, html {
      height: 100%;
      margin: 0;
      padding: 0;
      overflow: hidden;
    }
    .chat-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    .chat-messages {
      flex-grow: 1;
      overflow-y: auto;
      padding: 1rem;
    }
    .chat-input {
      padding: 1rem;
      background-color: white;
    }
    .user-message {
      display: flex;
      justify-content: flex-end;
      flex-direction: row-reverse;
      margin-bottom: 1rem;
      width: 100%;
    }
    .bot-message {
      display: flex;
      justify-content: flex-start;
      margin-bottom: 1rem;
      width: 100%;
    }
    .message-bubble {
      display: inline-block;
      width: auto;
      padding: 0.75rem 1rem;
      border-radius: 1rem;
    }
    .user-bubble {
      background-color: #3b82f6;
      color: white;
      border-bottom-right-radius: 0.25rem;
      margin-left: 1rem;
      align-self: flex-end;
    }
    .bot-bubble {
      background-color: #f3f4f6;
      color: #1f2937;
      border-bottom-left-radius: 0.25rem;
    }
    .avatar {
      width: 2rem;
      height: 2rem;
      border-radius: 50%;
      margin: 0 0.5rem;
    }
    .typing-indicator {
      display: inline-block;
      padding: 0.75rem 1rem;
      background-color: #f3f4f6;
      border-radius: 1rem;
      border-bottom-left-radius: 0.25rem;
      margin-bottom: 1rem;
    }
    .typing-indicator span {
      display: inline-block;
      width: 0.5rem;
      height: 0.5rem;
      background-color: #9ca3af;
      border-radius: 50%;
      margin-right: 0.25rem;
      animation: typing 1.4s infinite both;
    }
    .typing-indicator span:nth-child(2) {
      animation-delay: 0.2s;
    }
    .typing-indicator span:nth-child(3) {
      animation-delay: 0.4s;
      margin-right: 0;
    }
    @keyframes typing {
      0% { transform: translateY(0); }
      50% { transform: translateY(-0.5rem); }
      100% { transform: translateY(0); }
    }
    .hidden {
      display: none !important;
    }
    .mode-button {
      transition: all 0.3s ease;
    }
    .mode-button.active {
      transform: scale(1.05);
    }
    .feedback-container {
      display: inline-flex;
      align-items: center;
      margin-left: 8px;
    }
    .feedback-thumb {
      transition: color 0.2s ease;
    }
    .feedback-thumb:hover {
      transform: scale(1.1);
    }
    .feedback-submit-btn {
      transition: background-color 0.2s ease;
    }
    .feedback-submit-btn:hover {
      background-color: #2563eb !important;
    }
  </style>
</head>
<body class="bg-white">
  <div class="chat-container w-[60%] mx-auto">
    <!-- Header -->
    <div class="bg-white border-b-2 border-gray-100 px-4 py-3 flex items-center justify-between">
      <div class="flex items-center">
        <img id="nav-logo" class="h-auto max-w-sm w-auto inline-block object-cover md:h-4" alt="Logo" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/06/5.png">
        <span class="ml-2 text-sm font-semibold text-blue-700">With Conversation History</span>
      </div>
      <div class="inline-flex rounded-md shadow-xs">
        <button id="clear-history-btn" class="px-4 py-2 text-sm font-medium text-gray-900 bg-white  border border-gray-200 rounded hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700">
          Clear History
        </button>
        <a href="#" id="toggle-settings-btn" class="px-4 py-2 text-sm font-medium text-gray-900 bg-white  border-t border-b border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 hidden">
          Settings
        </a>
        <div id="mode-buttons-container" class="ml-4 flex space-x-2" style="display:none;">
          <button id="toggle-developer-mode-btn" class="mode-button px-4 py-2 text-xs font-medium text-black bg-white  border rounded hover:bg-blue-200 hover:underline focus:outline-none focus:underline focus:ring-red-400" type="button">
           eVal Mode
          </button>
        </div>
      </div>
    </div>
    
    <!-- Chat Messages Area -->
    <div id="chat-messages" class="chat-messages">
      <!-- Logo centered in message area before first message -->
      <div id="center-logo" class="flex flex-col items-center justify-center h-full ">
        <img id="random-logo" class="h-160 w-auto inline-block object-cover md:h-80" alt="Logo" src="/assets/">
      </div>
      <script>  
      (function() {
        const logos = [
          'https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/06/sage_icon_logo.png',
        ];
        const chosen = logos[Math.floor(Math.random() * logos.length)];
        document.addEventListener('DOMContentLoaded', () => {
          document.getElementById('random-logo').src = chosen;
        });
      })();
      </script>

      <!-- Bot welcome message (initially hidden) -->
      <div id="welcome-message" class="flex items-start gap-2.5 mb-4 hidden">
        <img class="w-8 h-8 rounded-full" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/dalle.png" alt="AI Agent">
        <div class="flex flex-col w-auto max-w-[90%] leading-1.5">
          <div class="flex items-center space-x-2 rtl:space-x-reverse">
            <span class="text-sm font-semibold text-gray-900 ">SAGE<span class="mt-1 text-sm leading-tight font-medium text-indigo-500 hover:underline">AI Agent</span></span>
          </div>
          <div class="text-sm font-normal py-2 text-gray-900 ">
            Hi there! I'm an AI assistant trained on your knowledge base. I can remember our conversation history. What would you like to know?
          </div>
          <span class="text-sm font-normal text-gray-500 dark:text-gray-400">Delivered</span>
        </div>
      </div>
      <!-- Messages will be added here dynamically -->
    </div>
    
    <!-- Chat Input Area -->
    <div class="chat-input">
      <div class="relative rounded-3xl border border-gray-300 p-4 bg-white  max-w-3xl mx-auto mt-10 shadow-md">
        <textarea
          id="query-input"
          rows="1"
          placeholder="Type here..."
          class="w-full resize-none overflow-hidden text-sm leading-relaxed outline-none bg-transparent"
          oninput="this.style.height = 'auto'; this.style.height = (this.scrollHeight) + 'px';"
          style="min-height: 34px;"
        ></textarea>
        <button id="submit-btn" class="absolute right-2 bottom-2 rounded-2xl bg-gradient-to-r from-blue-800 to-blue-400 py-2 px-4 border border-transparent text-center text-sm text-white transition-all shadow-sm hover:opacity-90 focus:opacity-95 focus:shadow-none active:opacity-95 disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none" type="button">
          Send
        </button>
      </div>
    </div>
  </div>

  <script>
    // --- Utility Functions ---
    function escapeHtml(unsafe) {
      return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }
    
    function formatMessage(message) {
      // Convert URLs to links
      message = message.replace(
        /(https?:\/\/[^\s]+)/g, 
        '<a href="$1" target="_blank" class="text-blue-600 hover:underline">$1</a>'
      );
      // Convert **bold** to <strong>
      message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      // Convert *italic* to <em>
      message = message.replace(/\*(.*?)\*/g, '<em>$1</em>');
      // Convert newlines to <br>
      message = message.replace(/\\n/g, '<br>');
      // Convert citation references [n] to clickable links
      message = message.replace(
        /\[(\d+)\]/g,
        '<a href="#source-$1" class="citation-link text-xs text-blue-600 hover:underline" data-source-id="$1">[$1]</a>'
      );
      return message;
    }

    // --- DOM elements ---
    const chatMessages = document.getElementById('chat-messages');
    const queryInput = document.getElementById('query-input');
    const submitBtn = document.getElementById('submit-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    
    // Auto-resize textarea up to 6 lines
    const maxLines = 6;
    const lineHeight = parseInt(window.getComputedStyle(queryInput).lineHeight);
    queryInput.addEventListener('input', () => {
      queryInput.style.height = 'auto';
      const boundedHeight = Math.min(queryInput.scrollHeight, lineHeight * maxLines);
      queryInput.style.height = boundedHeight + 'px';
      queryInput.style.overflowY = queryInput.scrollHeight > lineHeight * maxLines ? 'auto' : 'hidden';
    });
    
    // --- Chat functionality ---
    // Add user message to chat
    function addUserMessage(message) {
      // Hide center logo if visible
      const centerLogo = document.getElementById('center-logo');
      if (centerLogo && !centerLogo.classList.contains('hidden')) {
        centerLogo.classList.add('hidden');
      }
      
      // Create message element
      const messageDiv = document.createElement('div');
      messageDiv.className = 'user-message';
      messageDiv.innerHTML = `
        <img class="w-8 h-8 rounded-full" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/Untitled-design-3.png" alt="AI Agent">
        <div class="flex flex-col items-end w-full max-w-[90%] leading-1.5">
          <div class="flex items-center space-x-2 rtl:space-x-reverse pr-1 pb-1">
            <span class="text-xs font-semibold text-gray-900  "><span class="mt-1 text-xs leading-tight font-medium text-indigo-500 hover:underline">ME</span></span>
          </div>
          <div class="text-sm font-normal py-2 text-white message-bubble user-bubble">
             ${formatMessage(message)}
          </div>
          <span class="text-xs font-normal text-gray-500 dark:text-gray-400">Delivered</span>
        </div>
      `;
      
      // Add to chat
      chatMessages.appendChild(messageDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add bot message to chat
    function addBotMessage(message) {
      // Hide center logo if visible
      const centerLogo = document.getElementById('center-logo');
      if (centerLogo && !centerLogo.classList.contains('hidden')) {
        centerLogo.classList.add('hidden');
      }
      
      // Create message element
      const messageDiv = document.createElement('div');
      messageDiv.className = 'bot-message';
      messageDiv.innerHTML = `
        <img class="w-8 h-8 rounded-full" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/dalle.png" alt="AI Agent">
        <div class="flex flex-col w-auto max-w-[90%] leading-1.5">
          <div class="flex items-center space-x-2 rtl:space-x-reverse pl-1 pb-1">
            <span class="text-xs font-semibold text-gray-900 ">SAGE<span class="mt-1 text-xs leading-tight font-strong text-indigo-500 hover:underline"> AI Agent</span></span>
          </div>
          <div class="text-sm leading-6 font-normal py-2 text-gray-900  message-bubble bot-bubble">
             ${formatMessage(message)}
          </div>
          <span class="text-xs font-normal text-gray-500 dark:text-gray-400 text-right pt-1">Was this helpful?</span>
        </div>
      `;
      
      // Add to chat
      chatMessages.appendChild(messageDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add typing indicator
    function addTypingIndicator() {
      const indicatorDiv = document.createElement('div');
      indicatorDiv.className = 'bot-message';
      indicatorDiv.innerHTML = `
        <img class="avatar" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/dalle.png" alt="AI">
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      `;
      
      chatMessages.appendChild(indicatorDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      
      return indicatorDiv;
    }
    
    // Basic input handling
    if (queryInput && submitBtn) {
      // Enable submit button on input
      queryInput.addEventListener('keydown', function(e) {
        submitBtn.disabled = false;
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          submitBtn.click();
        }
      });
      
      // Submit button click handler
      submitBtn.addEventListener('click', function() {
        submitQuery();
      });
    }
    
    // Clear history button
    if (clearHistoryBtn) {
      clearHistoryBtn.addEventListener('click', function() {
        // Call API to clear history
        fetch('/api/clear_history', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // Clear the chat UI
            while (chatMessages.firstChild) {
              chatMessages.removeChild(chatMessages.firstChild);
            }
            
            // Show the center logo again
            const centerLogo = document.getElementById('center-logo');
            if (centerLogo) {
              centerLogo.classList.remove('hidden');
            }
            
            // Show a notification
            alert('Conversation history has been cleared.');
          } else {
            alert('Error clearing conversation history: ' + data.error);
          }
        })
        .catch(error => {
          console.error('Error:', error);
          alert('Error clearing conversation history. Please try again.');
        });
      });
    }
    
    // Standard query submission
    function submitQuery() {
      const query = queryInput.value.trim();
      if (!query) return;
      
      addUserMessage(query);
      queryInput.value = '';
      
      // Show typing indicator
      const typingIndicator = addTypingIndicator();
      
      // Call API to get response
      fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      })
      .then(response => response.json())
      .then(data => {
        // Remove typing indicator
        if (typingIndicator) typingIndicator.remove();
        
        // Show response
        if (data.error) {
          addBotMessage('Error: ' + data.error);
        } else {
          addBotMessage(data.answer);
          
          // Show sources if available
          if (data.sources && data.sources.length > 0) {
            // Store last sources for citation click handling
            window.lastSources = data.sources;
            // Add sources utilized section
            addSourcesUtilizedSection();
          }
        }
      })
      .catch(error => {
        // Remove typing indicator
        if (typingIndicator) typingIndicator.remove();
        
        // Show error
        addBotMessage('Error: Could not connect to server. Please try again later.');
        console.error('Error:', error);
      });
    }
    
    // Add sources utilized section function
    function addSourcesUtilizedSection() {
      if (window.lastSources && window.lastSources.length > 0) {
        let sourcesHtml = '<div class="sources-section mt-4 pt-3 border-t border-gray-200">';
        sourcesHtml += '<h4 class="text-sm font-semibold text-gray-700 mb-2">Sources Utilized</h4>';
        sourcesHtml += '<ol class="text-sm text-gray-600 space-y-1 pl-4">';
        
        window.lastSources.forEach((source, index) => {
          let sourceTitle = 'Untitled Source';
          
          if (typeof source === 'string') {
            // If source is just a string, use it as the title (truncated)
            sourceTitle = source.length > 80 ? source.substring(0, 80) + '...' : source;
          } else if (typeof source === 'object' && source !== null) {
            // If source is an object, try to get title, otherwise use content or fallback
            sourceTitle = source.title || 
                         (source.content ? (source.content.length > 80 ? source.content.substring(0, 80) + '...' : source.content) : 
                         `Source ${index + 1}`);
          }
          
          // Escape HTML in the title to prevent XSS
          sourceTitle = escapeHtml(sourceTitle);
          
          // Make the source title clickable with the same functionality as inline citations
          sourcesHtml += `<li>${index + 1}. <a href="#source-${index + 1}" class="citation-link text-blue-600 hover:underline cursor-pointer" data-source-id="${index + 1}">${sourceTitle}</a></li>`;
        });
        
        sourcesHtml += '</ol>';
        sourcesHtml += '</div>';
        
        // Append to the last bot message
        const lastBotMessage = document.querySelector('.bot-message:last-child .message-bubble');
        if (lastBotMessage) {
          lastBotMessage.innerHTML += sourcesHtml;
          
          // Add click event listeners for the new citation links
          setTimeout(() => {
            const newCitationLinks = lastBotMessage.querySelectorAll('.citation-link');
            newCitationLinks.forEach(link => {
              link.addEventListener('click', function(e) {
                e.preventDefault();
                const sourceId = this.getAttribute('data-source-id');
                
                // Trigger the same behavior as inline citations
                if (window.handleCitationClick) {
                  window.handleCitationClick(sourceId);
                } else {
                  // Fallback: try to find and scroll to the source element
                  const sourceElement = document.getElementById(`source-${sourceId}`);
                  if (sourceElement) {
                    sourceElement.scrollIntoView({ behavior: 'smooth' });
                    sourceElement.classList.add('bg-yellow-100');
                    setTimeout(() => {
                      sourceElement.classList.remove('bg-yellow-100');
                    }, 2000);
                  }
                }
              });
            });
          }, 100);
        }
      }
    }

    // Make functions available globally
    window.addUserMessage = addUserMessage;
    window.addBotMessage = addBotMessage;
    window.addTypingIndicator = addTypingIndicator;
    window.escapeHtml = escapeHtml;
    window.formatMessage = formatMessage;
    window.addSourcesUtilizedSection = addSourcesUtilizedSection;
  // Old DOMContentLoaded listener for sources panel removed.
  </script>

  <!-- Load the unified developer evaluation module -->
  
<!-- <script src="/static/js/unifiedEval.js"></script> -->
<script src="/static/js/custom.js"></script> <!-- This file is empty/deprecated -->
<script src="/static/js/debug-logger.js"></script>
<script>
  window.APP_CONFIG = { sasToken: "{{ sas_token }}" };
</script>
<script src="/static/js/url-decoder.js"></script> <!-- URL decoder for source document links -->
<script src="/static/js/dynamic-container.js"></script>
<!-- <script src="/static/js/citation-toggle.js"></script> --> <!-- Removed -->
<script src="/static/js/feedback-integration.js"></script>
<script src="/static/js/feedback_thumbs.js"></script>
<!-- Placeholder citation click handler and its listener removed -->

<!-- <script>

(function() {
  const overlay = document.getElementById('passcode-overlay');
  const passcodeInput = document.getElementById('passcode-input');
  const accessBtn = document.getElementById('access-btn');
  
  // Check if already authenticated
  if (localStorage.getItem('stagingAuth') === 'true') {
    overlay.classList.add('hidden');
  }
  
  // Simple hash function for basic obfuscation
  function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return hash;
  }
  
  // The passcode hash (can be changed to any value)
  const correctPasscodeHash = -1633765023; // This would be the hash of your actual passcode "rosebud"
  

  // Validate passcode
  function validatePasscode() {
    const enteredPasscode = passcodeInput.value.trim();
    if (simpleHash(enteredPasscode) === correctPasscodeHash || enteredPasscode === "rosebud") {
      overlay.classList.add('hidden');
      localStorage.setItem('stagingAuth', 'true');
    } else {
      passcodeInput.classList.add('border-red-500');
      setTimeout(() => {
        passcodeInput.classList.remove('border-red-500');
      }, 1000);
    }
  }
  
  // Event listeners
  accessBtn.addEventListener('click', validatePasscode);
  passcodeInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      validatePasscode();
    }
  });
})();
</script> -->
  </body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    logger.info("Index page accessed")
    # Generate a session ID if one doesn't exist
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
        logger.info(f"New session created: {session['session_id']}")
    
    return render_template_string(HTML_TEMPLATE, file_executed=file_executed, sas_token=sas_token)

def get_rag_assistant(session_id):
    """Get or create a RAG assistant for the given session ID"""
    if session_id not in rag_assistants:
        logger.info(f"Creating new RAG assistant for session {session_id}")
        rag_assistants[session_id] = FlaskRAGAssistantWithHistory()
    return rag_assistants[session_id]

@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json()
    logger.info("DEBUG - Incoming /api/query payload: %s", json.dumps(data))
    user_query = data.get("query", "")
    logger.info(f"API query received: {user_query}")
    
    # Get the session ID
    session_id = session.get('session_id')
    if not session_id:
        session_id = os.urandom(16).hex()
        session['session_id'] = session_id
        logger.info(f"Created new session ID: {session_id}")
    
    # Extract any settings from the request
    settings = data.get("settings", {})
    logger.info(f"DEBUG - Request settings: {json.dumps(settings)}")
    
    try:
        # Get or create the RAG assistant for this session
        rag_assistant = get_rag_assistant(session_id)
        
        # Update settings if provided
        if settings:
            for key, value in settings.items():
                if hasattr(rag_assistant, key):
                    setattr(rag_assistant, key, value)
            
            # If model is updated, update the deployment name
            if "model" in settings:
                rag_assistant.deployment_name = settings["model"]
                rag_assistant.openai_service.deployment_name = settings["model"]
        
        logger.info(f"DEBUG - Using model: {rag_assistant.deployment_name}")
        logger.info(f"DEBUG - Temperature: {rag_assistant.temperature}")
        logger.info(f"DEBUG - Max tokens: {rag_assistant.max_tokens}")
        logger.info(f"DEBUG - Top P: {rag_assistant.top_p}")
        
        # Generate response using the RAG assistant with history
        answer, cited_sources, _, evaluation, context = rag_assistant.generate_rag_response(user_query)
        
        logger.info(f"API query response generated for: {user_query}")
        logger.info(f"DEBUG - Response length: {len(answer)}")
        logger.info(f"DEBUG - Number of cited sources: {len(cited_sources)}")
        
        # Check if history was trimmed
        history_trimmed = getattr(rag_assistant, "_history_trimmed", False)
        
        return jsonify({
            "answer": answer,
            "sources": cited_sources,
            "evaluation": evaluation,
            "history_trimmed": history_trimmed
        })
    except Exception as e:
        logger.error(f"Error in api_query: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route("/api/clear_history", methods=["POST"])
def api_clear_history():
    """Clear the conversation history for the current session"""
    try:
        session_id = session.get('session_id')
        if session_id and session_id in rag_assistants:
            logger.info(f"Clearing conversation history for session {session_id}")
            rag_assistants[session_id].clear_conversation_history()
            return jsonify({"success": True})
        else:
            logger.warning(f"No active session found to clear history")
            return jsonify({"success": True, "message": "No active session found"})
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/stream_query", methods=["POST"])
def api_stream_query():
    data = request.get_json()
    user_query = data.get("query", "")
    logger.info(f"Stream query received: {user_query}")
    
    # Get the session ID
    session_id = session.get('session_id')
    if not session_id:
        session_id = os.urandom(16).hex()
        session['session_id'] = session_id
        logger.info(f"Created new session ID for streaming: {session_id}")
    
    # Extract any settings from the request
    settings = data.get("settings", {})
    
    def generate():
        try:
            # Get or create the RAG assistant for this session
            rag_assistant = get_rag_assistant(session_id)
            
            # Update settings if provided
            if settings:
                for key, value in settings.items():
                    if hasattr(rag_assistant, key):
                        setattr(rag_assistant, key, value)
                
                # If model is updated, update the deployment name
                if "model" in settings:
                    rag_assistant.deployment_name = settings["model"]
                    rag_assistant.openai_service.deployment_name = settings["model"]
            
            logger.info(f"Starting stream response for: {user_query}")
            
            # Use streaming method
            for chunk in rag_assistant.stream_rag_response(user_query):
                logger.info("DEBUG - AI stream chunk: %s", chunk)
                if isinstance(chunk, str):
                    yield chunk
                else:
                    # If this is a trimming notification, add a flag to the metadata
                    if isinstance(chunk, dict) and chunk.get("trimmed", False):
                        logger.info(f"History was trimmed, dropped {chunk.get('dropped', 0)} messages")
                        chunk["history_trimmed"] = True
                    yield f"\n[[META]]{json.dumps(chunk)}"
            
            logger.info(f"Completed stream response for: {user_query}")
                
        except Exception as e:
            logger.error(f"Error in stream_query: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            yield f"Sorry, I encountered an error: {str(e)}"
            yield f"\n[[META]]" + json.dumps({"error": str(e)})
    
    return Response(generate(), mimetype="text/plain")

@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    data = request.get_json()
    logger.debug(f"Received feedback data: {json.dumps(data)}")
    
    feedback_data = {
        "question": data.get("question", ""),
        "response": data.get("response", ""),
        "feedback_tags": data.get("feedback_tags", []),
        "comment": data.get("comment", ""),
        "evaluation_json": {},
        "citations": data.get("citations", [])
    }
    
    # Log the processed feedback data to help diagnose issues
    logger.debug(f"Processed feedback data: {json.dumps(feedback_data)}")
    
    try:
        vote_id = DatabaseManager.save_feedback(feedback_data)
        logger.info(f"Feedback saved to DB with ID: {vote_id}")
        return jsonify({"success": True, "vote_id": vote_id}), 200
    except Exception as e:
        logger.error(f"Error saving feedback to database: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

# Serve static files from both static/ and reask_dashboard/static/
@app.route("/static/<path:filename>")
def serve_static(filename):
    # First check if the file exists in the local static directory
    local_static_path = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(os.path.join(local_static_path, filename)):
        return send_from_directory(local_static_path, filename)
    
    # If not found in local static, check in reask_dashboard/static
    reask_static_path = os.path.join(os.path.dirname(__file__), "reask_dashboard", "static")
    if os.path.exists(os.path.join(reask_static_path, filename)):
        return send_from_directory(reask_static_path, filename)
    
    # If not found in either location, return 404
    return "File not found", 404

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Flask RAG application with conversation history')
    parser.add_argument('--port', type=int, default=int(os.environ.get("PORT", 5003)),
                        help='Port to run the server on (default: 5003)')
    args = parser.parse_args()
    
    port = args.port
    logger.info(f"Starting Flask app with conversation history on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
