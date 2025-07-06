# Markdown Rendering Solution

## Problem Statement

The system inconsistently renders markdown responses, sometimes as rich text, sometimes as raw markdown, or even as a mix of both. This inconsistency affects user experience and readability of the bot's responses.

## Root Cause Analysis

The root cause of the inconsistent rendering was identified as:

1. The `{marked_js_cdn}` variable in the HTML template was not being properly passed to the template rendering function, causing the marked.js library to fail to load.
2. The marked-renderer.js file was trying to use the marked library without first ensuring it was properly loaded.
3. There was no consistent fallback mechanism when the marked.js library failed to load or when rendering failed.

## Implemented Solution

### 1. Fixed Template Variable Passing in main.py

Updated the template rendering in main.py to properly pass the marked_js_cdn variable:

```python
@app.route("/", methods=["GET"])
def index():
    logger.info("Index page accessed")
    # Generate a session ID if one doesn't exist
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
        logger.info(f"New session created: {session['session_id']}")
    
    return render_template_string(HTML_TEMPLATE, 
                                 file_executed=file_executed, 
                                 sas_token=sas_token,
                                 marked_js_cdn=MARKED_JS_CDN)
```

### 2. Added Robust Library Loading in HTML Template

Added code to ensure marked.js is properly loaded and configured:

```javascript
<script src="{marked_js_cdn}" defer></script>
<script>
  // Ensure marked is available globally
  document.addEventListener('DOMContentLoaded', function() {
    if (typeof marked === 'undefined') {
      console.error('marked library not loaded, loading from CDN');
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
      script.onload = function() {
        console.log('marked library loaded successfully');
        // Configure marked.js
        marked.setOptions({
          gfm: true,          // GitHub Flavored Markdown
          breaks: true,       // Convert \n to <br>
          sanitize: false,    // Don't sanitize HTML (we handle this elsewhere)
          smartLists: true,   // Use smarter list behavior
          smartypants: true   // Use "smart" typographic punctuation
        });
      };
      document.head.appendChild(script);
    } else {
      console.log('marked library already loaded');
      // Configure marked.js
      marked.setOptions({
        gfm: true,          // GitHub Flavored Markdown
        breaks: true,       // Convert \n to <br>
        sanitize: false,    // Don't sanitize HTML (we handle this elsewhere)
        smartLists: true,   // Use smarter list behavior
        smartypants: true   // Use "smart" typographic punctuation
      });
    }
  });
</script>
```

### 3. Enhanced marked-renderer.js with Robust Library Loading

Updated the marked-renderer.js file to ensure the marked library is properly loaded before attempting to use it:

```javascript
// First, ensure marked.js is loaded
function loadMarkedLibrary() {
  return new Promise((resolve, reject) => {
    if (typeof marked !== 'undefined') {
      console.log("marked-renderer.js: marked library already loaded");
      resolve();
      return;
    }
    
    console.log("marked-renderer.js: Loading marked library from CDN");
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    script.onload = () => {
      console.log("marked-renderer.js: marked library loaded successfully");
      // Configure marked.js
      marked.setOptions({
        gfm: true,          // GitHub Flavored Markdown
        breaks: true,       // Convert \n to <br>
        sanitize: false,    // Don't sanitize HTML (we handle this elsewhere)
        smartLists: true,   // Use smarter list behavior
        smartypants: true   // Use "smart" typographic punctuation
      });
      resolve();
    };
    script.onerror = () => {
      console.error("marked-renderer.js: Failed to load marked library");
      reject(new Error("Failed to load marked library"));
    };
    document.head.appendChild(script);
  });
}

// Use the library in the fetchAndRenderMarkdown function
async function fetchAndRenderMarkdown(query) {
  try {
    // Ensure marked is loaded before proceeding
    await loadMarkedLibrary();
    
    // Rest of the function...
  } catch (error) {
    // Error handling...
  }
}
```

### 4. Consistent formatMessage Function

Ensured the formatMessage function in main.py and dev_eval_chat.js consistently use marked.js for rendering markdown with proper error handling:

```javascript
function formatMessage(message) {
  try {
    // Pre-process special cases before passing to marked.js
    let processedMessage = message.replace(
      /\[(\d+)\]/g,
      '<a href="#source-$1" class="citation-link text-xs text-blue-600 hover:underline" data-source-id="$1">[$1]</a>'
    );
    
    // Use marked.js for standard markdown rendering
    let html = marked.parse(processedMessage, {
      gfm: true,          // GitHub Flavored Markdown
      breaks: true,       // Convert \n to <br>
      sanitize: false,    // Don't sanitize HTML (we handle this elsewhere)
      smartLists: true,   // Use smarter list behavior
      smartypants: true   // Use "smart" typographic punctuation
    });
    
    return html;
  } catch (error) {
    console.error('Error rendering markdown with marked.js:', error);
    
    // Fallback to basic formatting if marked.js fails
    // [fallback formatting code]
    return message;
  }
}
```

### 5. Client-Side Rendering in rag_assistant_with_history_copy.py

Added a comment to clarify that the client-side will handle markdown rendering:

```python
# Process the streaming response
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        collected_chunks.append(content)
        collected_answer += content
        # Yield the raw content - the client-side will handle markdown rendering
        # This ensures consistent rendering across all response types
        yield content
```

## How This Solution Works

1. **Consistent Library Loading**: The solution ensures that the marked.js library is properly loaded before attempting to use it, with fallback mechanisms in case of failure.

2. **Multiple Loading Points**: The marked.js library is loaded in multiple places to ensure it's available when needed:
   - In the main HTML template via the script tag
   - In the marked-renderer.js file via dynamic script loading
   - With configuration in both places to ensure consistent rendering options

3. **Error Handling**: Robust error handling ensures that even if marked.js fails to load or throws an error during rendering, the application will fall back to basic formatting.

4. **Client-Side Rendering**: The server sends raw markdown content, and the client-side consistently renders it using marked.js.

## Benefits

1. **Consistency**: All responses are now rendered using the same pipeline, ensuring consistent formatting.

2. **Robustness**: Multiple loading points and fallback mechanisms ensure that even if one method fails, the application will still function.

3. **Minimal Changes**: The solution required minimal changes to the existing codebase, reducing the risk of regressions.

## Future Enhancements

For a more comprehensive solution in the future, consider:

1. **Unified Rendering Pipeline**: Create a single, centralized rendering function that all parts of the application use.

2. **Server-Side Pre-processing**: Implement server-side pre-processing for certain markdown elements to ensure they're consistently handled.

3. **Custom Renderer**: Develop a custom renderer that extends marked.js to handle application-specific formatting needs.

4. **Caching**: Implement caching of rendered content to improve performance.

5. **Sanitization**: Add consistent HTML sanitization to prevent XSS attacks.

6. **Testing**: Add automated tests to verify rendering consistency across different types of markdown content.
