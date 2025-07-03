"""
Flask-compatible version of the RAG assistant with in-memory conversation history
"""
import logging
from typing import List, Dict, Tuple, Optional, Any, Generator, Union
import traceback
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
import re
import sys
import os
import re
from openai_logger import log_openai_call
from db_manager import DatabaseManager
from conversation_manager_copy import ConversationManager
from openai_service import OpenAIService

# Import config but handle the case where it might import streamlit
try:
    from config import (
        OPENAI_ENDPOINT,
        OPENAI_KEY,
        OPENAI_API_VERSION,
        EMBEDDING_DEPLOYMENT,
        CHAT_DEPLOYMENT,
        SEARCH_ENDPOINT,
        SEARCH_INDEX,
        SEARCH_KEY,
        VECTOR_FIELD,
    )
except ImportError as e:
    if 'streamlit' in str(e):
        # Define fallback values or load from environment
        OPENAI_ENDPOINT = os.environ.get("OPENAI_ENDPOINT")
        OPENAI_KEY = os.environ.get("OPENAI_KEY")
        OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION")
        EMBEDDING_DEPLOYMENT = os.environ.get("EMBEDDING_DEPLOYMENT")
        CHAT_DEPLOYMENT = os.environ.get("CHAT_DEPLOYMENT")
        SEARCH_ENDPOINT = os.environ.get("SEARCH_ENDPOINT")
        SEARCH_INDEX = os.environ.get("SEARCH_INDEX")
        SEARCH_KEY = os.environ.get("SEARCH_KEY")
        VECTOR_FIELD = os.environ.get("VECTOR_FIELD")
    else:
        raise

logger = logging.getLogger(__name__)


class FactCheckerStub:
    """No-op evaluator so we still return a dict in the tuple."""
    def evaluate_response(
        self, query: str, answer: str, context: str, deployment: str
    ) -> Dict[str, Any]:
        return {}


def format_context_text(text: str) -> str:
    # Add line breaks after long sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    formatted = "\n\n".join(sentence for sentence in sentences if sentence)
    
    # Optional: emphasize headings or keywords
    formatted = re.sub(r'(?<=\n\n)([A-Z][^\n:]{5,40})(?=\n\n)', r'**\1**', formatted)  # crude title detection
    
    return formatted

class FlaskRAGAssistantGPT:
    """Retrieval-Augmented Generation assistant with in-memory conversation history."""

    # Default system prompt
    DEFAULT_SYSTEM_PROMPT = """
   ### Task

Respond to the user's query using only the provided context. Your primary goal is to provide accurate, helpful answers that are strictly based on the supplied source documents. Use only Markdown for formatting. Provide inline citations in the format [id] when the <source> tag includes an id attribute (e.g., <source id="1">).

### Understanding the Query
- Before answering, briefly rephrase the user's query to confirm your understanding. Strive for a natural and conversational tone.
- If the query is ambiguous because it could apply to multiple systems or topics in the context (e.g., "how to add a user" when methods for multiple systems are present), your **only action** must be to ask the user for clarification.
- **Do not, under any circumstances, list all possible answers or summarize the different options.** Your sole purpose at this step is to resolve the ambiguity.
- **Example Clarification:** If the query is "how to add user" and context exists for OpenLAB and Linux, you must respond with something like: "I can help with that. To which system are you trying to add a user? Please specify either 'OpenLAB' or 'Red Hat Enterprise Linux'."
- Respond in the same language as the user's query.

### Use of Sources and Citations
- Your answer must be **directly and entirely supported** by the provided context.
- You should **synthesize information** from the context to form a coherent and direct answer to the user's question. **Do not use verbatim extracts** unless the source text is already a perfect, concise answer (e.g., a specific error message).
- After providing a piece of information, cite the source(s) it came from (e.g., [1] or [1][2]).
- For each answer, mention the **document title and relevant section** where the information was found to ensure transparency.

### Providing Further Information
- You may suggest further reading from the Knowledge Base if:
    a) it is highly relevant to the user's question,
    b) the URL provided in the context is valid,
    c) it is not a duplicate of a document you have already cited as a primary source.
- Hyperlink the resource title using Markdown format: `**[Resource Title](URL)**`.

### Answer Format and Style
- Be concise, focused, and helpful. Your tone should be professional and clear.
- For instructional or troubleshooting queries, **create clear, step-by-step instructions** based on the information in the context.
- If the answer is not available in the provided context, you must state this clearly. **Do not use external knowledge or make assumptions.** Your response should be: "I could not find an answer to your question in the provided knowledge base."
- If the provided context is unreadable or appears incomplete, inform the user of this limitation and provide the best possible answer based on the available information.
- Reference earlier parts of the conversation if it is necessary for providing a clear and continuous experience.

### Output Structure

<context>
{{CONTEXT}}
</context>

<user_query>
{{QUERY}}
</user_query>
    """

    # ───────────────────────── setup ─────────────────────────
    def __init__(self, settings=None) -> None:
        self._init_cfg()
        
        # Initialize the OpenAI service
        self.openai_service = OpenAIService(
            azure_endpoint=self.openai_endpoint,
            api_key=self.openai_key,
            api_version=self.openai_api_version or "2023-05-15",
            deployment_name=self.deployment_name
        )
        
        # Initialize the conversation manager with the system prompt
        self.conversation_manager = ConversationManager(self.DEFAULT_SYSTEM_PROMPT)
        
        # For backward compatibility
        self.openai_client = AzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            api_key=self.openai_key,
            api_version=self.openai_api_version or "2023-05-15",
        )
        
        self.fact_checker = FactCheckerStub()
        
        # Model parameters with defaults
        self.temperature = 0.3
        self.top_p = 1.0
        self.max_tokens = 1000
        self.presence_penalty = 0.6
        self.frequency_penalty = 0.6
        
        # Conversation history window size (in turns)
        self.max_history_turns = 5
        
        # Flag to track if history was trimmed in the most recent request
        self._history_trimmed = False
        
        # Load settings if provided
        self.settings = settings or {}
        self._load_settings()
        
        logger.info("FlaskRAGAssistantGPT initialized with conversation history")

    def _init_cfg(self) -> None:
        self.openai_endpoint      = OPENAI_ENDPOINT
        self.openai_key           = OPENAI_KEY
        self.openai_api_version   = OPENAI_API_VERSION
        self.embedding_deployment = EMBEDDING_DEPLOYMENT
        self.deployment_name      = CHAT_DEPLOYMENT
        self.search_endpoint      = SEARCH_ENDPOINT
        self.search_index         = SEARCH_INDEX
        self.search_key           = SEARCH_KEY
        self.vector_field         = VECTOR_FIELD
        
    def _load_settings(self) -> None:
        """Load settings from provided settings dict"""
        settings = self.settings
        
        # Update model parameters
        if "model" in settings:
            self.deployment_name = settings["model"]
            # Update the OpenAI service deployment name
            self.openai_service.deployment_name = self.deployment_name
            
        if "temperature" in settings:
            self.temperature = settings["temperature"]
        if "top_p" in settings:
            self.top_p = settings["top_p"]
        if "max_tokens" in settings:
            self.max_tokens = settings["max_tokens"]
        
        # Update search configuration
        if "search_index" in settings:
            self.search_index = settings["search_index"]
            
        # Update conversation history window size
        if "max_history_turns" in settings:
            self.max_history_turns = settings["max_history_turns"]
            logger.info(f"Setting max_history_turns to {self.max_history_turns}")
            
        # Update system prompt if provided
        if "system_prompt" in settings:
            system_prompt = settings.get("system_prompt", "")
            system_prompt_mode = settings.get("system_prompt_mode", "Append")
            
            if system_prompt_mode == "Override":
                # Replace the default system prompt
                self.conversation_manager.clear_history(preserve_system_message=False)
                self.conversation_manager.chat_history = [{"role": "system", "content": system_prompt}]
                logger.info(f"System prompt overridden with custom prompt")
            else:  # Append
                # Update the system message with combined prompt
                combined_prompt = f"{system_prompt}\n\n{self.DEFAULT_SYSTEM_PROMPT}"
                self.conversation_manager.clear_history(preserve_system_message=False)
                self.conversation_manager.chat_history = [{"role": "system", "content": combined_prompt}]
                logger.info(f"System prompt appended with custom prompt")

    # ───────────── embeddings ─────────────
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        if not text:
            return None
        try:
            request = {
                # Arguments for self.openai_client.embeddings.create
                'model': self.embedding_deployment,
                'input': text.strip(),
            }
            resp = self.openai_client.embeddings.create(**request)
            log_openai_call(request, resp)
            return resp.data[0].embedding
            
        
        except Exception as exc:
            logger.error("Embedding error: %s", exc)
            return None

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        mag = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
        return 0.0 if mag == 0 else dot / mag

    # ───────────── Azure Search ───────────
    def search_knowledge_base(self, query: str) -> List[Dict]:
        try:
            logger.info(f"Searching knowledge base for query: {query}")
            client = SearchClient(
                endpoint=f"https://{self.search_endpoint}.search.windows.net",
                index_name=self.search_index,
                credential=AzureKeyCredential(self.search_key),
            )
            q_vec = self.generate_embedding(query)
            if not q_vec:
                logger.error("Failed to generate embedding for query")
                return []

            logger.info(f"Executing vector search with fields: {self.vector_field}")
            vec_q = VectorizedQuery(
                vector=q_vec,
                k_nearest_neighbors=10,
                fields=self.vector_field,
            )
            
            # Log the search parameters
            logger.info(f"Search parameters: index={self.search_index}, vector_field={self.vector_field}, top=10")
            
            # Add parent_id to select fields
            results = client.search(
                search_text=query,
                vector_queries=[vec_q],
                select=["chunk", "title", "parent_id"],  # Added parent_id here
                top=10,
            )
            
            # Convert results to list and log count
            result_list = list(results)
            logger.info(f"Search returned {len(result_list)} results")
            
            # Debug log the first result if available
            if result_list and len(result_list) > 0:
                first_result = result_list[0]
                logger.debug(f"First result - title: {first_result.get('title', 'No title')}")
                logger.debug(f"First result - has parent_id: {'Yes' if 'parent_id' in first_result else 'No'}")
                if 'parent_id' in first_result:
                    logger.debug(f"First result - parent_id: {first_result.get('parent_id')[:30]}..." if first_result.get('parent_id') else "None")
            
            return [
                {
                    "chunk": r.get("chunk", ""),
                    "title": r.get("title", "Untitled"),
                    "parent_id": r.get("parent_id", ""),  # Include parent_id
                    "relevance": 1.0,
                }
                for r in result_list
            ]
        except Exception as exc:
            logger.error(f"Search error: {exc}", exc_info=True)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    # ───────── context & citations ────────
    def _trim_history(self, messages: List[Dict]) -> Tuple[List[Dict], bool]:
        """
        Trim conversation history to the last N turns while preserving the system message.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Tuple of (trimmed_messages, was_trimmed)
        """
        logger.info(
        f"TRIM_DEBUG: Called with {len(messages)} messages. Cap is {self.max_history_turns*2+1}"
    )   
        dropped = False
        if len(messages) > self.max_history_turns*2+1:  # +1 for system message
            dropped = True
            # Log before trimming
            logger.info(f"History size ({len(messages)}) exceeds limit ({self.max_history_turns*2+1}), trimming...")
            logger.info(f"Before trimming: {len(messages)} messages")
            
            # Keep system message + last N pairs
            messages = [messages[0]] + messages[-self.max_history_turns*2:]
            
            # Log after trimming
            logger.info(f"After trimming: {len(messages)} messages")
            logger.info(f"Trimmed conversation history to last {self.max_history_turns} turns")
            
            # Store trimming status for API to access
            self._history_trimmed = True
        else:
            self._history_trimmed = False
            logger.info(f"No trimming needed. History size: {len(messages)}, limit: {self.max_history_turns*2+1}")
            
        return messages, dropped
        
    def _prepare_context(self, results: List[Dict]) -> Tuple[str, Dict]:
        logger.debug(f"_prepare_context input results: {results[:3]}... total {len(results)}")
        logger.info(f"Preparing context from {len(results)} search results")
        entries, src_map = [], {}
        sid = 1
        valid_chunks = 0
        
        for res in results[:5]:
            chunk = res["chunk"].strip()
            if not chunk:
                logger.warning(f"Empty chunk found in result {sid}, skipping")
                continue

            valid_chunks += 1
            formatted_chunk = format_context_text(chunk)
            
            # Log parent_id if available
            parent_id = res.get("parent_id", "")
            if parent_id:
                logger.info(f"Source {sid} has parent_id: {parent_id[:30]}..." if len(parent_id) > 30 else parent_id)
            else:
                logger.warning(f"Source {sid} missing parent_id")

            entries.append(f'<source id="{sid}">{formatted_chunk}</source>')
            src_map[str(sid)] = {
                "title": res["title"],
                "content": formatted_chunk,
                "parent_id": parent_id  # Include parent_id in source map
            }
            sid += 1

        context_str = "\n\n".join(entries)
        if valid_chunks == 0:
            logger.warning("No valid chunks found in _prepare_context, returning fallback context")
            context_str = "[No context available from knowledge base]"

        logger.info(f"Prepared context with {valid_chunks} valid chunks and {len(src_map)} sources")
        return context_str, src_map

    def _chat_answer_with_history(self, query: str, context: str, src_map: Dict) -> str:
        """Generate a response using the conversation history"""
        logger.info("Generating response with conversation history")
        
        # Check if custom prompt is available in settings
        settings = self.settings
        custom_prompt = settings.get("custom_prompt", "")
        
        # Apply custom prompt to query if available
        if custom_prompt:
            query = f"{custom_prompt}\n\n{query}"
            logger.info(f"Applied custom prompt to query: {custom_prompt[:100]}...")
        
        # Create a context message
        context_message = f"<context>\n{context}\n</context>\n<user_query>\n{query}\n</user_query>"
        
        # Add the user message to conversation history (only once)
        logger.info(f"Adding user message to conversation history")
        self.conversation_manager.add_user_message(context_message)
        
        # Get the complete conversation history
        raw_messages = self.conversation_manager.get_history()
        # Enforce inline citation instructions in generation
        raw_messages.insert(0, {
            "role": "system",
            "content": (
                "When composing your response, include inline citations in the format [id] "
                "only for sources with <source id=\"...\"> in the context."
            )
        })
        
        # Trim history if needed
        messages, trimmed = self._trim_history(raw_messages)
        if trimmed:
            # Add a system notification at the end of history
            messages.append({"role": "system", "content": f"[History trimmed to last {self.max_history_turns} turns]"})
        
        # Log the conversation history
        logger.info(f"Conversation history has {len(messages)} messages (trimmed: {trimmed})")
        for i, msg in enumerate(messages):
            logger.info(f"Message {i} - Role: {msg['role']}")
            if i < 3 or i >= len(messages) - 2:  # Log first 3 and last 2 messages
                logger.info(f"Content: {msg['content'][:100]}...")
        
        # Get response from OpenAI service
        import json
        payload = {
            "model": self.deployment_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty
        }
        logger.info("========== OPENAI RAW PAYLOAD ==========")
        logger.info(json.dumps(payload, indent=2))
        response = self.openai_service.get_chat_response(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p
        )
        
        # Add the assistant's response to conversation history
        self.conversation_manager.add_assistant_message(response)
        
        return response

    def _filter_cited(self, answer: str, src_map: Dict) -> List[Dict]:
        logger.debug(f"_filter_cited received answer: {answer[:500]}...")
        logger.debug(f"src_map keys: {list(src_map.keys())}")
        logger.info("Filtering cited sources from answer")
        cited_sources = []
        
        for sid, sinfo in src_map.items():
            if f"[{sid}]" in answer:
                logger.info(f"Source {sid} is cited in the answer")
                
                # Check if parent_id exists
                parent_id = sinfo.get("parent_id", "")
                if parent_id:
                    logger.info(f"Source {sid} has parent_id: {parent_id[:30]}..." if len(parent_id) > 30 else parent_id)
                else:
                    logger.warning(f"Cited source {sid} missing parent_id")
                
                # Add source to cited sources
                cited_source = {
                    "id": sid,
                    "title": sinfo["title"],
                    "content": sinfo["content"],
                    "parent_id": parent_id  # Include parent_id
                }
                cited_sources.append(cited_source)
        
        logger.info(f"Found {len(cited_sources)} cited sources")
        return cited_sources

    # ─────────── public API ───────────────
    def generate_rag_response(
        self, query: str
    ) -> Tuple[str, List[Dict], List[Dict], Dict[str, Any], str]:
        """
        Generate a response using RAG with conversation history.
        
        Args:
            query: The user query
            
        Returns:
            answer, cited_sources, [], evaluation, context
        """
        try:
            kb_results = self.search_knowledge_base(query)
            if not kb_results:
                return (
                    "No relevant information found in the knowledge base.",
                    [],
                    [],
                    {},
                    "",
                )

            context, src_map = self._prepare_context(kb_results)
            
            # Use the conversation history to generate the answer
            answer = self._chat_answer_with_history(query, context, src_map)

            # Collect only the sources actually cited
            cited_raw = self._filter_cited(answer, src_map)

            # Renumber in cited order: 1, 2, 3…
            renumber_map = {}
            cited_sources = []
            for new_id, src in enumerate(cited_raw, 1):
                old_id = src["id"]
                renumber_map[old_id] = str(new_id)
                entry = {
                    "id": str(new_id), 
                    "title": src["title"], 
                    "content": src["content"],
                    "parent_id": src.get("parent_id", "")  # Include parent_id in cited sources
                }
                if "url" in src:
                    entry["url"] = src["url"]
                cited_sources.append(entry)
            for old, new in renumber_map.items():
                answer = re.sub(rf"\[{old}\]", f"[{new}]", answer)

            evaluation = self.fact_checker.evaluate_response(
                query=query,
                answer=answer,
                context=context,
                deployment=self.deployment_name,
            )
            
            # Log the query, response, and sources to the database
            try:
                # Get the SQL query used to retrieve the results (if available)
                sql_query = None
                # If you have access to the actual SQL query used, set it here
                
                # Log the query to the database
                DatabaseManager.log_rag_query(
                    query=query,
                    response=answer,
                    sources=cited_sources,
                    context=context,
                    sql_query=sql_query
                )
            except Exception as log_exc:
                logger.error(f"Error logging RAG query to database: {log_exc}")
                # Continue even if logging fails
            
            return answer, cited_sources, [], evaluation, context
        
        except Exception as exc:
            logger.error("RAG generation error: %s", exc)
            return (
                "I encountered an error while generating the response.",
                [],
                [],
                {},
                "",
            )
            
    def stream_rag_response(self, query: str) -> Generator[Union[str, Dict], None, None]:
        """
        Stream the RAG response generation with conversation history.
        
        Args:
            query: The user query
            
        Yields:
            Either string chunks of the answer or a dictionary with metadata
        """
        try:
            logger.info(f"========== STARTING STREAM RAG RESPONSE WITH HISTORY ==========")
            logger.info(f"Original query: {query}")
            
            kb_results = self.search_knowledge_base(query)
            if not kb_results:
                logger.info("No relevant information found in knowledge base")
                yield "No relevant information found in the knowledge base."
                yield {
                    "sources": [],
                    "evaluation": {}
                }
                return

            context, src_map = self._prepare_context(kb_results)
            logger.info(f"Retrieved {len(kb_results)} results from knowledge base")
            
            # Check if custom prompt is available in settings
            settings = self.settings
            custom_prompt = settings.get("custom_prompt", "")
            
            # Apply custom prompt to query if available
            if custom_prompt:
                query = f"{custom_prompt}\n\n{query}"
                logger.info(f"Applied custom prompt to query: {custom_prompt[:100]}...")
            
            # Create a context message
            context_message = f"<context>\n{context}\n</context>\n<user_query>\n{query}\n</user_query>"
            
            # Add the user message to conversation history
            self.conversation_manager.add_user_message(context_message)
            
            # Get the complete conversation history
            raw_messages = self.conversation_manager.get_history()
            
            # Trim history if needed
            messages, trimmed = self._trim_history(raw_messages)
            if trimmed:
                # Yield a notification about trimming
                yield {"trimmed": True, "dropped": len(raw_messages) - len(messages)}
            
            # Log the conversation history
            logger.info(f"Conversation history has {len(messages)} messages (trimmed: {trimmed})")
            for i, msg in enumerate(messages):
                logger.info(f"Message {i} - Role: {msg['role']}")
                if i < 3 or i >= len(messages) - 2:  # Log first 3 and last 2 messages
                    logger.info(f"Content: {msg['content'][:100]}...")
            
            # Stream the response
            collected_chunks = []
            collected_answer = ""
            
            # Use the OpenAI client directly for streaming since our OpenAIService doesn't support streaming yet
            request = {
                # Arguments for self.openai_client.chat.completions.create
                'model': self.deployment_name,
                'messages': messages,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'top_p': self.top_p,
                'presence_penalty': self.presence_penalty,
                'frequency_penalty': self.frequency_penalty,
                'stream': True
            }
            log_openai_call(request, {"type": "stream_started"})
            stream = self.openai_client.chat.completions.create(**request)
            
            # Process the streaming response
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    collected_chunks.append(content)
                    collected_answer += content
                    yield content
            
            logger.info("DEBUG - Collected answer: %s", collected_answer[:100])
            
            # Add the assistant's response to conversation history
            self.conversation_manager.add_assistant_message(collected_answer)
            
            # Filter cited sources
            cited_raw = self._filter_cited(collected_answer, src_map)
            
            # Renumber in cited order: 1, 2, 3…
            renumber_map = {}
            cited_sources = []
            for new_id, src in enumerate(cited_raw, 1):
                old_id = src["id"]
                renumber_map[old_id] = str(new_id)
                entry = {
                    "id": str(new_id), 
                    "title": src["title"], 
                    "content": src["content"],
                    "parent_id": src.get("parent_id", "")  # Include parent_id in cited sources
                }
                if "url" in src:
                    entry["url"] = src["url"]
                cited_sources.append(entry)
            
            # Apply renumbering to the answer
            for old, new in renumber_map.items():
                collected_answer = re.sub(rf"\[{old}\]", f"[{new}]", collected_answer)
            
            # Get evaluation
            evaluation = self.fact_checker.evaluate_response(
                query=query,
                answer=collected_answer,
                context=context,
                deployment=self.deployment_name,
            )
            
            # Log the query, response, and sources to the database
            try:
                # Get the SQL query used to retrieve the results (if available)
                sql_query = None
                # If you have access to the actual SQL query used, set it here
                
                # Log the query to the database
                DatabaseManager.log_rag_query(
                    query=query,
                    response=collected_answer,
                    sources=cited_sources,
                    context=context,
                    sql_query=sql_query
                )
            except Exception as log_exc:
                logger.error(f"Error logging RAG query to database: {log_exc}")
                # Continue even if logging fails
            
            # Yield the metadata
            yield {
                "sources": cited_sources,
                "evaluation": evaluation
            }
            
        except Exception as exc:
            logger.error("RAG streaming error: %s", exc)
            yield "I encountered an error while generating the response."
            yield {
                "sources": [],
                "evaluation": {},
                "error": str(exc)
            }
            
    def clear_conversation_history(self, preserve_system_message: bool = True) -> None:
        """
        Clear the conversation history.
        
        Args:
            preserve_system_message: Whether to preserve the initial system message
        """
        self.conversation_manager.clear_history(preserve_system_message)
        logger.info(f"Conversation history cleared (preserve_system_message={preserve_system_message})")
