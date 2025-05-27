import json
from rag_assistant import FlaskRAGAssistant

DEFAULT_SUMMARY_PROMPT = """
You are an expert LLM analyst. Given the following results from one or more batches of LLM runs (with different parameters), provide:
- A concise summary of the overall findings
- Key differences between the batches (if present)
- Notable patterns, anomalies, or trends
- Actionable suggestions for the user

Results JSON:
{results_json}
"""
MODEL_NAME = "https://guilh-m7uwrx85-eastus2.openai.azure.com/openai/deployments/o4-mini/chat/completions?api-version=2025-01-01-preview"
DEVELOPER_EVAL_PROMPT = """
You are an expert LLM prompt engineer and system optimizer. Given the following:

- Query: {query}
- Prompt: {prompt}
- Parameters: temperature={temperature}, top_p={top_p}, max_tokens={max_tokens}
- Result: {result}

Analyze the above and provide actionable suggestions for:
- Improving the prompt for clarity, specificity, or effectiveness
- Adjusting parameters for optimal results
- Identifying any issues or gaps in the source data
- Recommending further experiments or next steps

Respond in a concise, bullet-pointed format for developers.
"""

def summarize_results(results, system_prompt=None, llm_settings=None):
    """
    Summarize and interpret batch results using an LLM.

    Args:
        results: dict or str (the results from the batch jobs)
        system_prompt: Optional custom summary prompt (str)
        llm_settings: Optional dict of settings for the LLM (model, temperature, etc.)

    Returns:
        summary: str (LLM-generated summary/insights)
    """
    if not isinstance(results, str):
        results_json = json.dumps(results, indent=2, ensure_ascii=False)
    else:
        results_json = results

    prompt = (system_prompt or DEFAULT_SUMMARY_PROMPT).format(results_json=results_json)

    assistant = FlaskRAGAssistant(settings=llm_settings or {})
    answer, *_ = assistant.generate_rag_response(prompt)
    return answer

def developer_evaluate_job(query, prompt, parameters, result, llm_settings=None):
    """
    Developer-focused LLM evaluation for prompt/parameter/source optimization.

    Args:
        query: str
        prompt: str
        parameters: dict (should include temperature, top_p, max_tokens)
        result: str

    Returns:
        suggestions: str (LLM-generated actionable suggestions)
    """
    meta_prompt = DEVELOPER_EVAL_PROMPT.format(
        query=query,
        prompt=prompt,
        temperature=parameters.get("temperature"),
        top_p=parameters.get("top_p"),
        max_tokens=parameters.get("max_tokens"),
        result=result
    )
    assistant = FlaskRAGAssistant(settings=llm_settings or {})
    suggestions, *_ = assistant.generate_rag_response(meta_prompt)
    return suggestions

def generate_markdown_report(data):
    """
    Generate a markdown report from the evaluation results.
    
    Args:
        data: dict containing evaluation data
            - query: str
            - prompt: str
            - parameters: dict
            - result: str
            - sources: list
            - developer_evaluation: str
            
    Returns:
        str: Markdown formatted report
    """
    from datetime import datetime
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Start building the markdown report
    md = []
    md.append("# Developer Evaluation Report")
    md.append(f"\n*Generated on: {timestamp}*\n")
    
    # Query section
    md.append("## Query")
    md.append(f"```\n{data['query']}\n```\n")
    
    # Parameters section
    md.append("## Parameters")
    params = data.get('parameters', {})
    md.append(f"- **Temperature:** {params.get('temperature', 'N/A')}")
    md.append(f"- **Top P:** {params.get('top_p', 'N/A')}")
    md.append(f"- **Max Tokens:** {params.get('max_tokens', 'N/A')}\n")
    
    # Custom prompt section (if provided)
    if data.get('prompt'):
        md.append("## Custom Prompt")
        md.append(f"```\n{data['prompt']}\n```\n")
    
    # LLM output section
    md.append("## LLM Output")
    md.append(f"```\n{data['result']}\n```\n")
    
    # Sources section (if provided)
    if data.get('sources') and len(data['sources']) > 0:
        md.append("## Sources")
        for i, source in enumerate(data['sources'], 1):
            if isinstance(source, dict):
                title = source.get('title', source.get('name', source.get('id', f"Source {i}")))
                url = source.get('url', '')
                if url:
                    md.append(f"{i}. [{title}]({url})")
                else:
                    md.append(f"{i}. {title}")
            else:
                md.append(f"{i}. {source}")
        md.append("")
    
    # Developer evaluation section
    md.append("## Developer Evaluation")
    md.append(data['developer_evaluation'])
    
    # Join all sections with newlines
    return "\n".join(md)
