
print("Running:", __file__)
import traceback
from flask import Flask, request, jsonify, render_template_string, Response, send_from_directory
import json
import logging
import sys
import os
from dotenv import load_dotenv
load_dotenv() 


# Import directly from the current directory
from rag_assistant import FlaskRAGAssistant
from db_manager import DatabaseManager

# Configure logginghttps://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/logo-spark-1.png
logger = logging.getLogger(__name__)
# Clear any existing handlers
if logger.handlers:
    logger.handlers.clear()
# Add file handler with absolute path
file_handler = logging.FileHandler('app.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# Stream logs to stdout for visibility
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)
import os
print(os.path.abspath(__file__))

file_executed = os.path.abspath(__file__)

# Log startup message to verify logging is working
logger.info("Flask RAG application starting up")

app = Flask(__name__)
# Serve static files from the 'assets' folder
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)


# HTML template with Tailwind CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SAGE Knowledge Navigator
</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style id="custom-styles">
  /*  p, li, a {
      font-size: 14px !important;
    } */
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
    /* Added to ensure hidden class works as expected */
    .hidden {
      display: none !important;
    }
    /* Styles for mode buttons */
    .mode-button {
      transition: all 0.3s ease;
    }
    .mode-button.active {
      transform: scale(1.05);
    }
    /* Emergency disable button */
    #emergency-disable-unified-dev-eval {
      display: none;
    }
    /* Feedback system styles */
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
  <!-- Passcode Overlay -->

 <div id="passcode-overlay" class="fixed inset-0 bg-gray-900 bg-opacity-35 z-50 flex flex-col items-center justify-center" style="background-image: url('/assets/overlay_2.jpeg'); background-repeat: no-repeat; background-position: center; background-size: cover; background-blend-mode: darken;">
    <div class="text-center max-w-md mx-auto p-8">
      
      
      <h2 class="text-xl font-bold mb-8 text-white">Restricted Area</h2>
      <div class="relative mb-6">
        <input type="password" id="passcode-input" class="w-full bg-gray-100 rounded-full py-3 px-4 pl-12 pr-20 text-lg" placeholder="Passcode">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <i class="fas fa-lock text-gray-500"></i>
        </div>
        <button id="access-btn" class="absolute inset-y-0 right-0 flex items-center bg-gray-800 text-white rounded-full py-2 px-4 mr-1 text-lg">
          <i class="fas fa-unlock mr-2"></i>
        </button>
      </div>
    </div>
  </div>  
  <div class="chat-container w-[60%] mx-auto">
    <!-- Header -->
    <div class="bg-white border-b-2 border-gray-100 px-4 py-3 flex items-center justify-between">
      <div class="flex items-center">
<!-- <img id="nav-logo" class="h-auto max-w-sm w-auto inline-block object-cover md:h-4" alt="Logo" src=""> --> 
<h4 class="text-lg font-semibold text-gray-900 ml-2">RAG Knowledge Assistant</h4>
      </div>
      <div class=" inline-flex rounded-md shadow-xs ">
        <a href="#" aria-current="page" class="px-4 py-2 text-sm font-medium text-blue-700 bg-white border border-gray-200 rounded-s-lg hover:bg-gray-100 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 hidden">
          Chat
        </a>
        <a href="#" id="toggle-settings-btn" class="px-4 py-2 text-sm font-medium text-gray-900 bg-white border-t border-b border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 hidden">
          Settings
        </a>
        <a href="#" class="px-4 py-2 text-sm font-medium text-gray-900 bg-white border border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 hidden">
          Analytics
        </a>
        <!-- Mode buttons will be dynamically added here by unifiedDevEval.js -->
        <div id="mode-buttons-container" class="ml-4 flex space-x-2" style="display:none;">
          <button id="toggle-developer-mode-btn" class="mode-button px-4 py-2 text-xs font-medium text-black bg-white border rounded hover:bg-blue-200 hover:underline focus:outline-none focus:underline focus:ring-red-400" type="button">
           eVal Mode
          </button>
          <!-- Batch and Compare mode buttons will be added here -->
        </div>
      </div>
    </div>
    
    <!-- Chat Messages Area -->
    <div id="chat-messages" class="chat-messages">
      <!-- Logo centered in message area before first message -->
      <div id="center-logo" class="flex flex-col items-center justify-center h-full ">
        <img id="random-logo" class="h-160 w-auto inline-block object-cover md:h-80" alt="Logo" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/06/logo-gif-3.gif">
<h3 class="text-md font-normal text-gray-700 mt-4">[    Logo approved. <span class=" font-bold"> Upload will start shortly.    </span>]</h3>   
         <h1 class="text-2xl font-bold text-gray-900 mt-2">RAG Knowledge Assistant</h1>
      </div>
      <script>  
      (function() {
        const logos = [
          
         
          'https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/06/logo-2.gif',
          
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
            <span class="text-sm font-semibold text-gray-900 dark:text-white">RAGKA/<span class="mt-1 text-sm leading-tight font-medium text-indigo-500 hover:underline">AI Agent</span></span>
          </div>
          <div class="text-sm font-normal py-2 text-gray-900 dark:text-white">
            Hi there! I'm an AI assistant trained on your knowledge base. What would you like to know?
          </div>
          <span class="text-sm font-normal text-gray-500 dark:text-gray-400">Delivered</span>
        </div>
      </div>
      <!-- Messages will be added here dynamically -->
    </div>
    
    <!-- Chat Input Area -->
    <div class="chat-input">
      <div class="relative">
        <textarea id="query-input" rows="1" class="w-full bg-transparent placeholder:text-slate-400 text-slate-700 text-sm border border-slate-300 rounded-2xl pl-3 pr-20 py-3 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow resize-none overflow-hidden" placeholder="Ask me anything about our knowledge base..."></textarea>
        <button id="submit-btn" class="absolute right-1 bottom-3 rounded-2xl bg-slate-800 py-2 px-4 border border-transparent text-center text-sm text-white transition-all shadow-sm hover:shadow focus:bg-slate-700 focus:shadow-none active:bg-slate-700 hover:bg-slate-700 active:shadow-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none" type="button">
          Send
        </button>
      </div>
    </div>
    <div class="flex items-center justify-center ml-4 overflow-visible">
      <button id="toggle-console-btn" class="group hidden px-3 py-1 w-full bg-white hover:bg-gray-300 text-gray-800 rounded relative inline-flex items-center justify-center">
        Console Logs
        <svg xmlns="http://www.w3.org/2000/svg" class="ml-1 h-4 w-4 text-gray-800" viewBox="0 0 20 20" fill="buttoncurrentColor">
          <path fill-rule="evenodd" d="M18 10c0 4.418-3.582 8-8 8-4.418 0-8-3.582-8-8s3.582-8 8-8 8 3.582 8 8zm-9 4a1 1 0 112 0 1 1 0 01-2 0zm.75-7.001a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z" clip-rule="evenodd"/>
        </svg>
        <span class="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded py-1 px-2 shadow-lg whitespace-nowrap invisible opacity-0 group-hover:visible group-hover:opacity-100 transition-opacity duration-150 z-10">
          This feature is experimental and may be buggy.
        </span>
      </button>
    </div>
          <!--  <span class="text-xs font-semibold text-green-500 text-center ml-2">{{ file_executed }}</span> -->

    <!-- Settings Drawer Backdrop & Panel -->
    <div id="settings-backdrop" class="fixed inset-0 bg-black/50 hidden z-40"></div>
    <div id="settings-drawer" class="fixed inset-y-0 right-0 w-96 bg-white shadow-lg transform translate-x-full transition-transform duration-300 z-50 flex flex-col">
      <div class="p-4 border-b flex items-center justify-between">
        <h2 class="text-lg font-semibold">Settings</h2>
        <button id="close-settings-btn" class="px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded">&times;</button>
      </div>
      <form id="settings-form" class="flex-1 flex flex-col p-4 space-y-4 overflow-y-auto">
        <div>
          <label for="custom-prompt" class="block text-sm font-medium text-gray-700 mb-1">Custom Instructions</label>
          <textarea id="custom-prompt" rows="5" class="w-full border border-gray-300 rounded p-2 text-sm" placeholder="Add custom instructions to the system prompt..."></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Prompt Mode</label>
          <div class="flex items-center space-x-4">
            <label class="inline-flex items-center">
              <input type="radio" name="prompt-mode" value="Append" class="form-radio" checked>
              <span class="ml-2">Append</span>
            </label>
            <label class="inline-flex items-center">
              <input type="radio" name="prompt-mode" value="Override" class="form-radio">
              <span class="ml-2">Override</span>
            </label>
          </div>
        </div>
        
        <!-- Developer Settings Section -->
        <div id="developer-settings" class="mt-4 pt-4 border-t border-gray-200">
          <h3 class="text-lg font-medium text-gray-900 mb-2">Developer Settings</h3>
          <p class="text-sm text-gray-500 mb-4">These settings are used in Developer Mode for evaluation.</p>
          
          <div class="mb-4">
            <label for="dev-temperature" class="block text-sm font-medium text-gray-700 mb-1">Temperature: <span id="temperature-value">0.3</span></label>
            <input type="range" id="dev-temperature" min="0" max="2" step="0.1" value="0.3" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
            <div class="flex justify-between text-xs text-gray-500">
              <span>0.0</span>
              <span>1.0</span>
              <span>2.0</span>
            </div>
          </div>
          
          <div class="mb-4">
            <label for="dev-top-p" class="block text-sm font-medium text-gray-700 mb-1">Top P: <span id="top-p-value">1.0</span></label>
            <input type="range" id="dev-top-p" min="0" max="1" step="0.05" value="1.0" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
            <div class="flex justify-between text-xs text-gray-500">
              <span>0.0</span>
              <span>0.5</span>
              <span>1.0</span>
            </div>
          </div>
          
          <div class="mb-4">
            <label for="dev-max-tokens" class="block text-sm font-medium text-gray-700 mb-1">Max Tokens:</label>
            <input type="number" id="dev-max-tokens" min="1" max="4000" value="1000" class="w-full border border-gray-300 rounded p-2 text-sm">
            <div class="text-xs text-gray-500 mt-1">Range: 1-4000</div>
          </div>
        </div>
        <div class="flex space-x-2">
          <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Apply</button>
          <button type="button" id="reset-settings-btn" class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">Reset</button>
          <button type="button" id="restore-default-btn" class="px-4 py-2 bg-green-100 text-green-800 rounded hover:bg-green-200 border border-green-300">Restore Default</button>
        </div>
        <div id="settings-status" class="hidden mt-2 flex items-center space-x-2 bg-green-100 border border-green-300 text-green-800 px-3 py-2 rounded text-sm">
          <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"></path></svg>
          <span id="settings-status-text"></span>
        </div>
      </form>
    </div>
    <!-- Console Drawer Backdrop & Panel -->
    <div id="console-backdrop" class="fixed inset-0 bg-black/50 hidden z-40"></div>
    <div id="console-drawer" class="fixed inset-y-0 right-0 w-80 bg-white shadow-lg transform translate-x-full transition-transform duration-300 z-50 flex flex-col">
      <div class="p-4 border-b flex items-center justify-between">
        <h2 class="text-lg font-semibold">Console Logs</h2>
        <div class="flex items-center">
          <button id="clear-console-btn" class="px-2 py-1 bg-red-500 text-white rounded">Clear Logs</button>
          <button id="close-console-btn" class="ml-2 px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded">&times;</button>
        </div>
      </div>
      <div id="console-logs-content" class="flex-1 p-4 overflow-auto font-mono text-sm bg-gray-50"></div>
    </div>
  </div>

  <!-- Configuration for unified developer evaluation module -->
  <script>
    // Configuration that can be externally modified
    window.unifiedDevEvalConfig = {
      enabled: true,
      apiEndpoints: {
        developer: '/api/dev_eval',
        batch: '/api/dev_eval_batch',
        compare: '/api/dev_eval_compare'
      },
      defaultParams: {
        temperature: 0.3,
        top_p: 1.0,
        max_tokens: 1000,
        runs: 1
      },
      uiOptions: {
        showModeButtons: true,
        persistSettings: true,
        animateTransitions: true
      }
    };
  </script>

  <!-- Utility functions and base chat functionality -->
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
              <span class="text-xs font-semibold text-gray-900 dark:text-white "><span class="mt-1 text-xs leading-tight font-medium text-indigo-500 hover:underline">ME</span></span>
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
            <span class="text-xs font-semibold text-gray-900 dark:text-white">RAGKA/<span class="mt-1 text-sm leading-tight font-strong text-indigo-500 hover:underline">AI</span></span>
          </div>
          <div class="text-sm leading-6 font-normal py-2 text-gray-900 dark:text-white message-bubble bot-bubble">
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
      
      // Submit button click handler (will be overridden by unifiedDevEval.js if enabled)
      submitBtn.addEventListener('click', function() {
        // This will be replaced by the unified module's handler
        // but serves as a fallback if the module fails to load
        submitQuery();
      });
    }
    
    // Standard query submission (will be overridden by unifiedDevEval.js)
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
    
    // Settings drawer functionality
    const settingsBtn = document.getElementById('toggle-settings-btn');
    const settingsDrawer = document.getElementById('settings-drawer');
    const settingsBackdrop = document.getElementById('settings-backdrop');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    
    if (settingsBtn && settingsDrawer && settingsBackdrop && closeSettingsBtn) {
      // Open settings drawer
      settingsBtn.addEventListener('click', function(e) {
        e.preventDefault();
        settingsDrawer.classList.remove('translate-x-full');
        settingsBackdrop.classList.remove('hidden');
      });
      
      // Close settings drawer
      function closeSettingsDrawer() {
        settingsDrawer.classList.add('translate-x-full');
        settingsBackdrop.classList.add('hidden');
      }
      
      closeSettingsBtn.addEventListener('click', closeSettingsDrawer);
      settingsBackdrop.addEventListener('click', closeSettingsDrawer);
    }
    
    // Console drawer functionality
    const consoleBtn = document.getElementById('toggle-console-btn');
    const consoleDrawer = document.getElementById('console-drawer');
    const consoleBackdrop = document.getElementById('console-backdrop');
    const closeConsoleBtn = document.getElementById('close-console-btn');
    const clearConsoleBtn = document.getElementById('clear-console-btn');
    const consoleLogsContent = document.getElementById('console-logs-content');
    
    if (consoleBtn && consoleDrawer && consoleBackdrop && closeConsoleBtn) {
      // Open console drawer
      consoleBtn.addEventListener('click', function() {
        consoleDrawer.classList.remove('translate-x-full');
        consoleBackdrop.classList.remove('hidden');
      });
      
      // Close console drawer
      function closeConsoleDrawer() {
        consoleDrawer.classList.add('translate-x-full');
        consoleBackdrop.classList.add('hidden');
      }
      
      closeConsoleBtn.addEventListener('click', closeConsoleDrawer);
      consoleBackdrop.addEventListener('click', closeConsoleDrawer);
      
      // Clear console logs
      if (clearConsoleBtn && consoleLogsContent) {
        clearConsoleBtn.addEventListener('click', function() {
          consoleLogsContent.innerHTML = '';
        });
      }
    }
    
    // Function to open console drawer (used by unifiedDevEval.js)
    function openDrawer() {
      if (consoleDrawer && consoleBackdrop) {
        consoleDrawer.classList.remove('translate-x-full');
        consoleBackdrop.classList.remove('hidden');
      }
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
          // This ensures the newly added links work with the existing citation functionality
          setTimeout(() => {
            const newCitationLinks = lastBotMessage.querySelectorAll('.citation-link');
            newCitationLinks.forEach(link => {
              link.addEventListener('click', function(e) {
                e.preventDefault();
                const sourceId = this.getAttribute('data-source-id');
                
                // Trigger the same behavior as inline citations
                // This will scroll to and highlight the source in the sidebar
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

    // Make functions available globally for the unified module
    window.addUserMessage = addUserMessage;
    window.addBotMessage = addBotMessage;
    window.addTypingIndicator = addTypingIndicator;
    window.escapeHtml = escapeHtml;
    window.formatMessage = formatMessage;
    window.openDrawer = openDrawer;
    window.logsContainer = consoleLogsContent;
    window.addSourcesUtilizedSection = addSourcesUtilizedSection;
    // Old DOMContentLoaded listener for sources panel removed.
  </script>

  <!-- Load the unified developer evaluation module -->
  
<!-- <script src="/static/js/unifiedEval.js"></script> -->
<script src="/static/js/custom.js"></script> <!-- This file is empty/deprecated -->
<script src="/static/js/debug-logger.js"></script>
<script src="/static/js/dynamic-container.js"></script>
<!-- <script src="/static/js/citation-toggle.js"></script> --> <!-- Removed -->
<script src="/static/js/feedback-integration.js"></script>
<script src="/static/js/feedback_thumbs.js"></script>
<!-- Placeholder citation click handler and its listener removed -->

<script>

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
</script>
  </body>
</html>

"""

@app.route("/", methods=["GET"])
def index():
    logger.info("Index page accessed")
    return render_template_string(HTML_TEMPLATE, file_executed=file_executed)

@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json()
    logger.info("DEBUG - Incoming /api/query payload: %s", json.dumps(data))
    user_query = data.get("query", "")
    logger.info(f"API query received: {user_query}")
    
    # Extract any settings from the request
    settings = data.get("settings", {})
    logger.info(f"DEBUG - Request settings: {json.dumps(settings)}")
    
    try:
        # Initialize the RAG assistant with settings if provided
        rag_assistant = FlaskRAGAssistant(settings=settings)
        logger.info(f"DEBUG - Using model: {rag_assistant.deployment_name}")
        logger.info(f"DEBUG - Temperature: {rag_assistant.temperature}")
        logger.info(f"DEBUG - Max tokens: {rag_assistant.max_tokens}")
        logger.info(f"DEBUG - Top P: {rag_assistant.top_p}")
        logger.info(f"DEBUG - Presence penalty: {rag_assistant.presence_penalty}")
        logger.info(f"DEBUG - Frequency penalty: {rag_assistant.frequency_penalty}")
        
        answer, cited_sources, _, evaluation, context = rag_assistant.generate_rag_response(user_query)
        logger.info(f"API query response generated for: {user_query}")
        logger.info(f"DEBUG - Response length: {len(answer)}")
        logger.info(f"DEBUG - Number of cited sources: {len(cited_sources)}")
        
        return jsonify({
            "answer": answer,
            "sources": cited_sources,
            "evaluation": evaluation
        })
    except Exception as e:
        logger.error(f"Error in api_query: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route("/api/stream_query", methods=["POST"])
def api_stream_query():
    data = request.get_json()
    user_query = data.get("query", "")
    logger.info(f"Stream query received: {user_query}")
    logger.info(f"DEBUG - Full request payload: {json.dumps(data)}")
    
    # Extract any settings from the request
    settings = data.get("settings", {})
    logger.info(f"DEBUG - Request settings: {json.dumps(settings)}")
    
    def generate():
        try:
            # Initialize the RAG assistant with settings if provided
            rag_assistant = FlaskRAGAssistant(settings=settings)
            logger.info(f"Starting stream response for: {user_query}")
            logger.info(f"DEBUG - Using model: {rag_assistant.deployment_name}")
            logger.info(f"DEBUG - Temperature: {rag_assistant.temperature}")
            logger.info(f"DEBUG - Max tokens: {rag_assistant.max_tokens}")
            logger.info(f"DEBUG - Top P: {rag_assistant.top_p}")
            logger.info(f"DEBUG - Presence penalty: {rag_assistant.presence_penalty}")
            logger.info(f"DEBUG - Frequency penalty: {rag_assistant.frequency_penalty}")
            
            # Use streaming method
            for chunk in rag_assistant.stream_rag_response(user_query):
                logger.info("DEBUG - AI stream chunk: %s", chunk)
                if isinstance(chunk, str):
                    yield chunk
                else:
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

@app.route("/api/dev_eval", methods=["POST"])
def api_dev_eval():
    """
    Developer Evaluation API endpoint.
    Expects JSON: { "query": ..., "prompt": ..., "parameters": { "temperature": ..., "top_p": ..., "max_tokens": ... } }
    Returns: { "result": ..., "developer_evaluation": ..., "download_url_json": ..., "download_url_md": ..., "markdown_report": ... }
    """
    
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Flask RAG application')
    parser.add_argument('--port', type=int, default=int(os.environ.get("PORT", 5002)),
                        help='Port to run the server on (default: 5002)')
    args = parser.parse_args()
    
    port = args.port
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
