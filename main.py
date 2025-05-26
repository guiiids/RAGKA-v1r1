import traceback
from flask import Flask, request, jsonify, render_template_string, Response, send_from_directory
import json
import logging
import sys
import os

# Import directly from the current directory
from rag_assistant import FlaskRAGAssistant
from llm_summary_compact import summarize_batch_comparison

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

# HTML template with Tailwind CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RAG Knowledge Assistant</title>
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
  <div class="chat-container w-[70%] mx-auto">
    <!-- Header -->
    <div class="bg-white border-b-2 border-gray-100 px-4 py-3 flex items-center justify-between">
      <div class="flex items-center">
        <img class='h-10 w-auto ml-2' src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/logo-spark-1.png" alt="Logo"> 
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
        <div id="mode-buttons-container" class="ml-4 flex space-x-2">
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
      <img class="h-60 w-auto inline-block object-cover md:h-60" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/This-is-a-to-do-item-This-is-completed-item.png" alt="Logo">
              </div>
      
      <!-- Bot welcome message (initially hidden) -->
         <div id="welcome-message" class="flex items-start gap-2.5 mb-4 hidden">
        <img class="w-8 h-8 rounded-full" src="https://content.tst-34.aws.agilent.com/wp-content/uploads/2025/05/dalle.png" alt="AI Agent">
            <div class="flex flex-col w-auto max-w-[90%] leading-1.5">
          <div class="flex items-center space-x-2 rtl:space-x-reverse">
            <span class="text-sm font-semibold text-gray-900 dark:text-white">SPARK/<span class="mt-1 text-sm leading-tight font-medium text-indigo-500 hover:underline">AI Agent</span></span>
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
        <input id="query-input" type="text" class="w-full bg-transparent placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded-2xl pl-3 pr-20 py-3 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow" placeholder="Ask me anything about our knowledge base..." />
        <button id="submit-btn" class="absolute right-1 top-1 rounded bg-slate-800 py-2 px-4 border border-transparent text-center text-sm text-white transition-all shadow-sm hover:shadow focus:bg-slate-700 focus:shadow-none active:bg-slate-700 hover:bg-slate-700 active:shadow-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none" type="button">
          Send
        </button>
      </div>
    </div>
    <div class="flex items-center justify-center ml-4 overflow-visible">
      <button id="toggle-console-btn" class="group px-3 py-1 w-full bg-white hover:bg-gray-300 text-gray-800 rounded relative inline-flex items-center justify-center">
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
            <span class="text-xs font-semibold text-gray-900 dark:text-white">SPARK/<span class="mt-1 text-sm leading-tight font-strong text-indigo-500 hover:underline">AI</span></span>
          </div>
          <div class="text-sm font-normal py-2 text-gray-900 dark:text-white message-bubble bot-bubble">
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
            // Old sources panel display logic removed. dynamic-container.js will handle it.
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
    
    // Make functions available globally for the unified module
    window.addUserMessage = addUserMessage;
    window.addBotMessage = addBotMessage;
    window.addTypingIndicator = addTypingIndicator;
    window.escapeHtml = escapeHtml;
    window.formatMessage = formatMessage;
    window.openDrawer = openDrawer;
    window.logsContainer = consoleLogsContent;
    // Old DOMContentLoaded listener for sources panel removed.
  </script>

  <!-- Load the unified developer evaluation module -->
  
<script src="/static/js/unifiedEval.js"></script>
<script src="/static/js/custom.js"></script> <!-- This file is empty/deprecated -->
<script src="/static/js/debug-logger.js"></script>
<script src="/static/js/dynamic-container.js"></script>
<!-- <script src="/static/js/citation-toggle.js"></script> --> <!-- Removed -->
<script src="/static/js/feedback-integration.js"></script>
<script src="/static/js/feedback_thumbs.js"></script>
<!-- Placeholder citation click handler and its listener removed -->
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
    feedback_data = {
        "question": data.get("question", ""),
        "response": data.get("response", ""),
        "feedback_tags": data.get("feedback_tags", []),
        "comment": data.get("comment", ""),
        "evaluation_json": {}
    }
    
    try:
        # For now, just log the feedback
        logger.info(f"Feedback received: {feedback_data}")
        return jsonify({"success": True}), 200
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
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
    from llm_summary import developer_evaluate_job, generate_markdown_report
    import uuid

    data = request.get_json()
    query = data.get("query", "")
    prompt = data.get("prompt", "")
    params = data.get("parameters", {}) or {}
    temperature = params.get("temperature", 0.3)
    top_p = params.get("top_p", 1.0)
    max_tokens = params.get("max_tokens", 1000)

    settings = {
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens
    }
    if prompt:
        settings["system_prompt"] = prompt
        settings["system_prompt_mode"] = "Override"

    try:
        rag_assistant = FlaskRAGAssistant(settings=settings)
        answer, sources, _, evaluation, context = rag_assistant.generate_rag_response(query)
        dev_eval = developer_evaluate_job(
            query=query,
            prompt=prompt,
            parameters=params,
            result=answer
        )
        # Save to file and provide download link
        result_obj = {
            "query": query,
            "prompt": prompt,
            "parameters": params,
            "result": answer,
            "sources": sources,
            "developer_evaluation": dev_eval
        }
        
        # Generate markdown report
        markdown_report = generate_markdown_report(result_obj)
        
        # Save with a unique filename
        file_id = str(uuid.uuid4())
        json_filename = f"dev_eval_{file_id}.json"
        md_filename = f"dev_eval_{file_id}.md"
        
        file_path = os.path.join("reask_dashboard", "static", "dev_eval_reports")
        os.makedirs(file_path, exist_ok=True)
        
        # Save JSON file
        json_path = os.path.join(file_path, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, indent=2, ensure_ascii=False)
        
        # Save Markdown file
        md_path = os.path.join(file_path, md_filename)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        
        # Download URLs
        json_url = f"/static/dev_eval_reports/{json_filename}"
        md_url = f"/static/dev_eval_reports/{md_filename}"
        
        return jsonify({
            "result": answer,
            "sources": sources,
            "developer_evaluation": dev_eval,
            "download_url_json": json_url,
            "download_url_md": md_url,
            "markdown_report": markdown_report
        })
    except Exception as e:
        logger.error(f"Error in api_dev_eval: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": str(e)
        }), 500
# Add these routes to your main.py file

@app.route('/api/dev_eval', methods=['POST'])
def dev_eval():
    """Handle developer evaluation mode requests"""
    data = request.json
    
    # Extract parameters
    query = data.get('query', '')
    prompt = data.get('prompt', '')
    parameters = data.get('parameters', {})
    
    # Log the request
    logger.info(f"Developer evaluation request: query={query}, prompt={prompt}, parameters={parameters}")
    
    # Use your existing RAG assistant
    settings = {
        "temperature": parameters.get('temperature', 0.3),
        "top_p": parameters.get('top_p', 1.0),
        "max_tokens": parameters.get('max_tokens', 1000)
    }
    
    if prompt:
        settings["system_prompt"] = prompt
        settings["system_prompt_mode"] = "Override"
    
    try:
        assistant = FlaskRAGAssistant(settings=settings)
        answer, sources, _, evaluation, context = assistant.generate_rag_response(query)
        
        # Try to get developer evaluation if llm_summary module is available
        developer_evaluation = None
        try:
            from llm_summary import developer_evaluate_job
            developer_evaluation = developer_evaluate_job(
                query=query,
                prompt=prompt,
                parameters=parameters,
                result=answer
            )
        except ImportError:
            logger.warning("llm_summary module not available for developer evaluation")
        
        # Generate unique ID for this evaluation
        import uuid
        eval_id = str(uuid.uuid4())
        
        # Save results to files
        os.makedirs('static/dev_eval_reports', exist_ok=True)
        
        # Save JSON report
        json_file = f"static/dev_eval_reports/dev_eval_{eval_id}.json"
        json_data = {
            "query": query,
            "prompt": prompt,
            "parameters": parameters,
            "result": answer,
            "sources": sources,
            "developer_evaluation": developer_evaluation
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save Markdown report
        md_file = f"static/dev_eval_reports/dev_eval_{eval_id}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Developer Evaluation Report\n\n")
            f.write(f"## Query\n\n{query}\n\n")
            f.write(f"## Parameters\n\n")
            f.write(f"- Temperature: {parameters.get('temperature', 0.3)}\n")
            f.write(f"- Top P: {parameters.get('top_p', 1.0)}\n")
            f.write(f"- Max Tokens: {parameters.get('max_tokens', 1000)}\n\n")
            if prompt:
                f.write(f"## Custom Prompt\n\n{prompt}\n\n")
            f.write(f"## LLM Output\n\n{answer}\n\n")
            if sources:
                f.write(f"## Sources\n\n")
                for i, source in enumerate(sources):
                    f.write(f"{i+1}. {source}\n")
                f.write("\n")
            if developer_evaluation:
                f.write(f"## Developer Evaluation\n\n{developer_evaluation}\n\n")
        
        # Return response
        return jsonify({
            "result": answer,
            "sources": sources,
            "developer_evaluation": developer_evaluation,
            "download_url_json": f"/static/dev_eval_reports/dev_eval_{eval_id}.json",
            "download_url_md": f"/static/dev_eval_reports/dev_eval_{eval_id}.md",
            "markdown_report": open(md_file, 'r', encoding='utf-8').read()
        })
    
    except Exception as e:
        logger.error(f"Error in developer evaluation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/dev_eval_batch', methods=['POST'])
def dev_eval_batch():
    """Handle batch evaluation mode requests"""
    data = request.json
    
    # Extract parameters
    query = data.get('query', '')
    prompt = data.get('prompt', '')
    parameters = data.get('parameters', {})
    runs = data.get('runs', 1)
    
    # Log the request
    logger.info(f"Batch evaluation request: query={query}, prompt={prompt}, parameters={parameters}, runs={runs}")
    
    # Use your existing RAG assistant
    settings = {
        "temperature": parameters.get('temperature', 0.3),
        "top_p": parameters.get('top_p', 1.0),
        "max_tokens": parameters.get('max_tokens', 1000)
    }
    
    if prompt:
        settings["system_prompt"] = prompt
        settings["system_prompt_mode"] = "Override"
    
    try:
        results = []
        assistant = FlaskRAGAssistant(settings=settings)
        
        for i in range(runs):
            try:
                answer, sources, _, evaluation, context = assistant.generate_rag_response(query)
                results.append({
                    "run": i+1,
                    "answer": answer,
                    "sources": sources,
                    "evaluation": evaluation,
                    "context": context
                })
            except Exception as e:
                logger.error(f"Error on run {i+1}: {str(e)}")
                logger.error(traceback.format_exc())
                results.append({
                    "run": i+1,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        # Evaluate prompt effectiveness for this batch
        prompt_evaluation = None
        try:
            from llm_summary_compact import evaluate_prompt_effectiveness
            prompt_evaluation = evaluate_prompt_effectiveness({
                "query": query,
                "system_prompt": prompt,
                "parameters": parameters,
                "results": results
            })
        except ImportError:
            logger.warning("llm_summary_compact module not available for prompt evaluation")
        
        # Generate unique ID for this evaluation
        import uuid
        eval_id = str(uuid.uuid4())
        
        # Save results to files
        os.makedirs('static/dev_eval_reports', exist_ok=True)
        
        # Save JSON report
        json_file = f"static/dev_eval_reports/batch_eval_{eval_id}.json"
        json_data = {
            "query": query,
            "prompt": prompt,
            "parameters": parameters,
            "runs": runs,
            "results": results,
            "prompt_evaluation": prompt_evaluation
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save Markdown report
        md_file = f"static/dev_eval_reports/batch_eval_{eval_id}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Batch Evaluation Report\n\n")
            f.write(f"## Query\n\n{query}\n\n")
            f.write(f"## Parameters\n\n")
            f.write(f"- Temperature: {parameters.get('temperature', 0.3)}\n")
            f.write(f"- Top P: {parameters.get('top_p', 1.0)}\n")
            f.write(f"- Max Tokens: {parameters.get('max_tokens', 1000)}\n")
            f.write(f"- Runs: {runs}\n\n")
            if prompt:
                f.write(f"## Custom Prompt\n\n{prompt}\n\n")
        # Ensure prompt evaluation and results are written inside the file context
        if prompt_evaluation:
            f.write(f"## Prompt Evaluation\n\n{prompt_evaluation}\n\n")
            f.write(f"## Results\n\n")
            for result in results:
                f.write(f"### Run {result.get('run')}\n\n")
                if 'error' in result:
                    f.write(f"**Error:** {result.get('error')}\n\n")
                else:
                    f.write(f"**Answer:**\n\n{result.get('answer')}\n\n")
                    if result.get('sources'):
                        f.write(f"**Sources:**\n\n")
                        for i, source in enumerate(result.get('sources', [])):
                            f.write(f"{i+1}. {source}\n")
                        f.write("\n")
        
        # Return response
        return jsonify({
            "results": results,
            "prompt_evaluation": prompt_evaluation,
            "download_url_json": f"/static/dev_eval_reports/batch_eval_{eval_id}.json",
            "download_url_md": f"/static/dev_eval_reports/batch_eval_{eval_id}.md",
            "markdown_report": open(md_file, 'r', encoding='utf-8').read()
        })
    
    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/api/dev_eval_compare", methods=["POST"])
def api_dev_eval_compare():
    """
    Developer Evaluation Compare API endpoint.
    Expects JSON: {
        "query": "...",
        "prompt": "...",  # Prompt for batch 1
        "parameters": { "temperature": ..., "top_p": ..., "max_tokens": ... },  # Parameters for batch 1
        "runs": 1,  # Number of runs for batch 1
        "batch2": {
            "temperature": ...,
            "top_p": ...,
            "max_tokens": ...,
            "runs": 1,
            "prompt": "..."  # Separate prompt for batch 2
        },
        "generate_llm_analysis": true/false  # Whether to generate LLM analysis of the comparison
    }
    Returns: {
        "batch1_results": [...],
        "batch2_results": [...],
        "download_url_json": "...",
        "download_url_md": "...",
        "markdown_report": "...",
        "llm_analysis": "..." (if requested)
    }
    """
    from llm_summary import developer_evaluate_job, generate_markdown_report
    import uuid

    data = request.get_json()
    query = data.get("query", "")
    
    # Log the incoming request
    logger.info(f"Compare evaluation request: query={query}, prompt={data.get('prompt', '')}, batch1={data.get('parameters', {})}, batch2={data.get('batch2', {})}")
    
    # Check if LLM analysis is requested
    generate_llm_analysis = data.get("generate_llm_analysis", True)  # Default to True
    
    # Extract batch 1 parameters
    prompt1 = data.get("prompt", "")
    params1 = data.get("parameters", {}) or {}
    temperature1 = params1.get("temperature", 0.3)
    top_p1 = params1.get("top_p", 1.0)
    max_tokens1 = params1.get("max_tokens", 1000)
    runs1 = data.get("runs", 1)
    
    # Extract batch 2 parameters
    batch2 = data.get("batch2", {})
    prompt2 = batch2.get("prompt", prompt1)  # Default to batch 1 prompt if not specified
    temperature2 = batch2.get("temperature", 0.3)
    top_p2 = batch2.get("top_p", 1.0)
    max_tokens2 = batch2.get("max_tokens", 1000)
    runs2 = batch2.get("runs", 1)
    
    try:
        # Process batch 1
        batch1_results = []
        for i in range(runs1):
            settings1 = {
                "temperature": temperature1,
                "top_p": top_p1,
                "max_tokens": max_tokens1
            }
            if prompt1:
                settings1["system_prompt"] = prompt1
                settings1["system_prompt_mode"] = "Override"
            
            rag_assistant1 = FlaskRAGAssistant(settings=settings1)
            answer1, sources1, _, evaluation1, context1 = rag_assistant1.generate_rag_response(query)
            
            batch1_results.append({
                "run": i+1,
                "answer": answer1,
                "sources": sources1,
                "evaluation": evaluation1
            })
        
        # Process batch 2
        batch2_results = []
        for i in range(runs2):
            settings2 = {
                "temperature": temperature2,
                "top_p": top_p2,
                "max_tokens": max_tokens2
            }
            if prompt2:
                settings2["system_prompt"] = prompt2
                settings2["system_prompt_mode"] = "Override"
            
            rag_assistant2 = FlaskRAGAssistant(settings=settings2)
            answer2, sources2, _, evaluation2, context2 = rag_assistant2.generate_rag_response(query)
            
            batch2_results.append({
                "run": i+1,
                "answer": answer2,
                "sources": sources2,
                "evaluation": evaluation2
            })
        
        # Generate developer evaluation for the comparison
        dev_eval = developer_evaluate_job(
            query=query,
            prompt=f"Batch 1: {prompt1}\nBatch 2: {prompt2}",
            parameters={
                "batch1": {
                    "temperature": temperature1,
                    "top_p": top_p1,
                    "max_tokens": max_tokens1,
                    "runs": runs1
                },
                "batch2": {
                    "temperature": temperature2,
                    "top_p": top_p2,
                    "max_tokens": max_tokens2,
                    "runs": runs2
                }
            },
            result=f"Batch 1 (first run): {batch1_results[0]['answer'] if batch1_results else 'No results'}\n\nBatch 2 (first run): {batch2_results[0]['answer'] if batch2_results else 'No results'}"
        )
        
        # Generate LLM analysis if requested
        llm_analysis = None
        if generate_llm_analysis:
            logger.info("Generating LLM analysis for comparison")
            # Prepare data for summarize_batch_comparison
            comparison_data = {
                "query": query,
                "batch_1": {
                    "system_prompt": prompt1,
                    "parameters": {
                        "temperature": temperature1,
                        "top_p": top_p1,
                        "max_tokens": max_tokens1,
                        "n_runs": runs1
                    },
                    "results": batch1_results
                },
                "batch_2": {
                    "system_prompt": prompt2,
                    "parameters": {
                        "temperature": temperature2,
                        "top_p": top_p2,
                        "max_tokens": max_tokens2,
                        "n_runs": runs2
                    },
                    "results": batch2_results
                }
            }
            
            try:
                llm_analysis = summarize_batch_comparison(comparison_data)
                logger.info("LLM analysis generated successfully")
            except Exception as e:
                logger.error(f"Error generating LLM analysis: {str(e)}")
                logger.error(traceback.format_exc())
                llm_analysis = f"Error generating LLM analysis: {str(e)}"
        
        # Create a combined result for markdown report compatibility
        combined_result = f"BATCH 1 (first run):\n{batch1_results[0]['answer'] if batch1_results else 'No results'}\n\nBATCH 2 (first run):\n{batch2_results[0]['answer'] if batch2_results else 'No results'}"
        
        # Save to file and provide download link
        result_obj = {
            "query": query,
            "prompt": f"Batch 1: {prompt1}\nBatch 2: {prompt2}",
            "parameters": {
                "batch1": {
                    "temperature": temperature1,
                    "top_p": top_p1,
                    "max_tokens": max_tokens1,
                    "runs": runs1
                },
                "batch2": {
                    "temperature": temperature2,
                    "top_p": top_p2,
                    "max_tokens": max_tokens2,
                    "runs": runs2
                }
            },
            "result": combined_result,  # Add the combined result for markdown report compatibility
            "batch1": {
                "prompt": prompt1,
                "parameters": {
                    "temperature": temperature1,
                    "top_p": top_p1,
                    "max_tokens": max_tokens1,
                    "runs": runs1
                },
                "results": batch1_results
            },
            "batch2": {
                "prompt": prompt2,
                "parameters": {
                    "temperature": temperature2,
                    "top_p": top_p2,
                    "max_tokens": max_tokens2,
                    "runs": runs2
                },
                "results": batch2_results
            },
            "developer_evaluation": dev_eval,
            "llm_analysis": llm_analysis
        }
        
        # Save with a unique filename
        file_id = str(uuid.uuid4())
        json_filename = f"dev_eval_compare_{file_id}.json"
        md_filename = f"dev_eval_compare_{file_id}.md"
        
        file_path = os.path.join("reask_dashboard", "static", "dev_eval_reports")
        os.makedirs(file_path, exist_ok=True)
        
        # Generate markdown report
        markdown_report = generate_markdown_report(result_obj)
        
        # Add LLM analysis to markdown report if available
        if llm_analysis:
            markdown_report += f"\n## LLM Analysis\n\n{llm_analysis}\n\n"
        
        # Save JSON file
        json_path = os.path.join(file_path, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, indent=2, ensure_ascii=False)
        
        # Save Markdown file
        md_path = os.path.join(file_path, md_filename)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        
        # Download URLs
        json_url = f"/static/dev_eval_reports/{json_filename}"
        md_url = f"/static/dev_eval_reports/{md_filename}"
        
        response_data = {
            "batch1_results": batch1_results,
            "batch2_results": batch2_results,
            "developer_evaluation": dev_eval,
            "download_url_json": json_url,
            "download_url_md": md_url,
            "markdown_report": markdown_report
        }
        
        # Include LLM analysis in the response if available
        if llm_analysis:
            response_data["llm_analysis"] = llm_analysis
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in api_dev_eval_compare: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
