"""
Flask-compatible version of the RAG assistant without Streamlit dependencies
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
from conversation_manager import ConversationManager

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

class FlaskRAGAssistant:
    """Retrieval-Augmented Generation assistant for Azure OpenAI + Search."""

    # Default system prompt
    DEFAULT_SYSTEM_PROMPT = """
    ### Task:

    Respond to the user query using the provided context, incorporating inline citations in the format [id] **only when the <source> tag includes an explicit id attribute** (e.g., <source id="1">).
    
    ### Guidelines:

    - If you don't know the answer, clearly state that.
    - If uncertain, ask the user for clarification.
    - Respond in the same language as the user's query.
    - If the context is unreadable or of poor quality, inform the user and provide the best possible answer.
    - If the answer isn't present in the context but you possess the knowledge, explain this to the user and provide the answer using your own understanding.
    - **Only include inline citations using [id] (e.g., [1], [2]) when the <source> tag includes an id attribute.**
    - Do not cite if the <source> tag does not contain an id attribute.
    - Do not use XML tags in your response.
    - Ensure citations are concise and directly related to the information provided.
    
    ### Example of Citation:

    If the user asks about a specific topic and the information is found in a source with a provided id attribute, the response should include the citation like in the following example:

    * "According to the study, the proposed method increases efficiency by 20% [1]."
    
    ### Output:

    Provide a clear and direct response to the user's query, including inline citations in the format [id] only when the <source> tag with id attribute is present in the context.
    
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
        self.openai_client = AzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            api_key=self.openai_key,
            api_version=self.openai_api_version or "2023-05-15",
        )
        
        # Initialize the conversation manager with the system prompt
        self.conversation_manager = ConversationManager(self.DEFAULT_SYSTEM_PROMPT)
        
        self.fact_checker = FactCheckerStub()
        
        # Model parameters with defaults
        self.temperature = 0.3
        self.top_p = 1.0
        self.max_tokens = 1000
        self.presence_penalty = 0.6
        self.frequency_penalty = 0.6
        
        # Load settings if provided
        self.settings = settings or {}
        self._load_settings()
        
        logger.info("FlaskRAGAssistant initialized with conversation history")

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
        if "temperature" in settings:
            self.temperature = settings["temperature"]
        if "top_p" in settings:
            self.top_p = settings["top_p"]
        if "max_tokens" in settings:
            self.max_tokens = settings["max_tokens"]
        
        # Update search configuration
        if "search_index" in settings:
            self.search_index = settings["search_index"]
            
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
    def _prepare_context(self, results: List[Dict]) -> Tuple[str, Dict]:
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


    def _chat_answer(self, query: str, context: str, src_map: Dict) -> str:
        """Generate a response using the conversation history"""
        logger.info("Generating response with conversation history")
        
        # Check if custom prompt is available in settings
        settings = self.settings
        custom_prompt = settings.get("custom_prompt", "")
        
        # Apply custom prompt to query if available
        if custom_prompt:
            query = f"{custom_prompt}\n\n{query}"
            logger.info(f"DEBUG - Applied custom prompt to query: {custom_prompt[:100]}...")
        
        # Create a context message
        context_message = f"<context>\n{context}\n</context>\n<user_query>\n{query}\n</user_query>"
        
        # Add the user message to conversation history
        self.conversation_manager.add_user_message(context_message)
        
        # Get the complete conversation history
        messages = self.conversation_manager.get_history()
        
        # Log detailed payload information
        logger.info("========== OPENAI API REQUEST DETAILS ==========")
        logger.info(f"Model deployment: {self.deployment_name}")
        logger.info(f"Temperature: {self.temperature}")
        logger.info(f"Max tokens: {self.max_tokens}")
        logger.info(f"Top P: {self.top_p}")
        logger.info(f"Presence penalty: {self.presence_penalty}")
        logger.info(f"Frequency penalty: {self.frequency_penalty}")
        
        # Log the conversation history
        logger.info(f"Conversation history has {len(messages)} messages")
        for i, msg in enumerate(messages):
            logger.info(f"Message {i} - Role: {msg['role']}")
            if i < 3 or i >= len(messages) - 2:  # Log first 3 and last 2 messages
                logger.info(f"Content: {msg['content'][:100]}...")
        
        # Log the exact JSON payload sent to OpenAI
        import json
        payload = {
            "model": self.deployment_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        logger.info("========== OPENAI RAW PAYLOAD ==========")
        logger.info(json.dumps(payload, indent=2))
        
        request = {
            # Arguments for self.openai_client.chat.completions.create
            'model': self.deployment_name,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'presence_penalty': self.presence_penalty,
            'frequency_penalty': self.frequency_penalty
        }
        resp = self.openai_client.chat.completions.create(**request)
        log_openai_call(request, resp)
        
        answer = resp.choices[0].message.content
        logger.info("DEBUG - OpenAI response content: %s", answer)
        
        # Add the assistant's response to conversation history
        self.conversation_manager.add_assistant_message(answer)
        
        return answer

    def _filter_cited(self, answer: str, src_map: Dict) -> List[Dict]:
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
            answer = self._chat_answer(query, context, src_map)

            # collect only the sources actually cited
            cited_raw = self._filter_cited(answer, src_map)

            # renumber in cited order: 1, 2, 3…
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
                logger.info(f"DEBUG - Applied custom prompt to query: {custom_prompt[:100]}...")
            
            # Create a context message
            context_message = f"<context>\n{context}\n</context>\n<user_query>\n{query}\n</user_query>"
            
            # Add the user message to conversation history
            self.conversation_manager.add_user_message(context_message)
            
            # Get the complete conversation history
            messages = self.conversation_manager.get_history()
            
            # Log the conversation history
            logger.info(f"Conversation history has {len(messages)} messages")
            for i, msg in enumerate(messages):
                logger.info(f"Message {i} - Role: {msg['role']}")
                if i < 3 or i >= len(messages) - 2:  # Log first 3 and last 2 messages
                    logger.info(f"Content: {msg['content'][:100]}...")
            
            # Log detailed payload information
            logger.info("========== OPENAI API STREAM REQUEST DETAILS ==========")
            logger.info(f"Model deployment: {self.deployment_name}")
            logger.info(f"Temperature: {self.temperature}")
            logger.info(f"Max tokens: {self.max_tokens}")
            logger.info(f"Top P: {self.top_p}")
            logger.info(f"Presence penalty: {self.presence_penalty}")
            logger.info(f"Frequency penalty: {self.frequency_penalty}")
            
            # Stream the response
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
            
            collected_chunks = []
            collected_answer = ""
            
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
            yield "[RAG3] I encountered an error while generating the response."
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
