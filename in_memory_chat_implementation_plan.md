# Implementation Plan: Configurable Conversation History Window

This document describes how to limit the in-memory conversation history to the last *N* user–assistant turn pairs, make *N* configurable via settings, and notify users when trimming occurs.

## Overview

Currently, the assistant fetches the full message history on every turn:

```python
messages = self.conversation_manager.get_history()
```

This can grow without bound. We will:

- Introduce a `max_history_turns` setting (default 5).
- Trim the history to the last *N* pairs before sending to the model, always preserving the system message at index 0.
- Apply the same logic in both normal and streaming response methods.
- Add a short notification logged or returned to the user when context is dropped.
- Update all code paths using `get_history()` to include trimming.

## Flow Diagram

```mermaid
flowchart TD
  A[Initialize Assistant] --> B[Set default max_history_turns=5]
  B --> C[Load settings]
  C -->|if settings.max_history_turns| D[Override self.max_history_turns]
  D --> E[User query → _chat_answer_with_history]
  E --> F[Fetch full history (messages = get_history())]
  F --> G{len(messages) > max_history_turns*2+1?}
  G -- Yes --> H[Trim to [system] + last max_history_turns*2 messages]
  G -- No  --> I[Use full history]
  H & I --> J[Send payload to OpenAI]
  J --> K[Append assistant reply]
  K --> L[Return response, include trim notification if applied]

  E2[Stream query → stream_rag_response] --> F2[Fetch full history]
  F2 --> G2{len(messages) > max_history_turns*2+1?}
  G2 -- Yes --> H2[Trim history]
  G2 -- No  --> I2[Keep full history]
  H2 & I2 --> J2[Stream to OpenAI]
  J2 --> K2[Append assistant reply]
  K2 --> L2[Yield chunks & metadata, include trim flag]
```

## Detailed Steps

1. **Add `max_history_turns` attribute**  
   - In `FlaskRAGAssistantWithHistory.__init__`, after loading model parameters:
     ```python
     self.max_history_turns = settings.get("max_history_turns", 5)
     ```
2. **Load from settings**  
   - In `_load_settings`, check for `"max_history_turns"` in `self.settings` and update `self.max_history_turns`.
3. **Trim logic helper**  
   - Create a private method `_trim_history(messages: List[Dict]) -> Tuple[List[Dict], bool]`:
     ```python
     def _trim_history(self, messages):
         dropped = False
         if len(messages) > self.max_history_turns*2+1:
             dropped = True
             messages = [messages[0]] + messages[-self.max_history_turns*2:]
         return messages, dropped
     ```
4. **Integrate in `_chat_answer_with_history`**  
   - Replace direct `get_history()` call:
     ```python
     raw = self.conversation_manager.get_history()
     messages, trimmed = self._trim_history(raw)
     if trimmed:
         logger.info(f"Trimmed {len(raw)-len(messages)} messages from history")
         # Optionally, append a system notification at end of history
         messages.append({"role":"system","content":f"[History trimmed to last {self.max_history_turns} turns]"})
     ```
5. **Integrate in `stream_rag_response`**  
   - After fetching `raw = get_history()`, apply `_trim_history` and include trim flag in metadata:
     ```python
     messages, trimmed = self._trim_history(raw)
     if trimmed:
         logger.info("Trimmed conversation history before streaming")
         yield {"trimmed":True, "dropped": len(raw)-len(messages)}
     ```
6. **Update all `get_history()` usages**  
   - Ensure both non‐streaming and streaming code paths use the helper for trimming.
7. **User notification**  
   - In the JSON API response for `/api/query`, include a `"history_trimmed": true/false` flag when trimming occurs.
8. **Update documentation & defaults**  
   - Document the new `max_history_turns` setting in README or configuration docs.
   - Add environment variable support if desired (e.g. `MAX_HISTORY_TURNS`).
9. **Add tests**  
   - In `test_conversation_manager.py` or a new test file:
     - Simulate more than *N* turns.
     - Verify `_trim_history` drops correct count.
     - Check API response includes `"history_trimmed": true`.
     - Confirm system message always preserved.

---

Once these changes are implemented and reviewed, switch to **Code** mode to apply them in `rag_assistant_with_history_copy.py`.
