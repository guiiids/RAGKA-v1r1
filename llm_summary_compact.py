import json
from rag_assistant import FlaskRAGAssistant

# A more compact prompt that focuses only on the essential information
COMPACT_SUMMARY_PROMPT = """
You are an expert LLM analyst. Compare these two batches of LLM runs with different parameters and prompts:

QUERY: {query}

BATCH 1:
- System Prompt: {prompt1}
- Temperature: {temp1}
- Top P: {top_p1}
- Max Tokens: {max_tokens1}
- Number of runs: {n_runs1}

BATCH 1 SAMPLE RESPONSE:
{response1}

BATCH 2:
- System Prompt: {prompt2}
- Temperature: {temp2}
- Top P: {top_p2}
- Max Tokens: {max_tokens2}
- Number of runs: {n_runs2}

BATCH 2 SAMPLE RESPONSE:
{response2}

Provide:
1. Analysis of how the parameter differences affected the outputs
2. Which parameter settings worked better for this query and why
3. Recommendations for optimal parameters for similar queries
"""

def summarize_batch_comparison(results):
    """
    You are an expert LLM analyst tasked with evaluating two batches of LLM responses differing in both prompt instructions and model parameters. Your evaluation must directly reference the provided user query and explicitly analyze whether responses address the user's intent and specific details.

QUERY:
{query}

BATCH 1 SETTINGS:
- System Prompt: "{prompt1}"
- Temperature: {temp1}, Top P: {top_p1}, Max Tokens: {max_tokens1}, Runs: {n_runs1}

BATCH 1 SAMPLE RESPONSE:
{response1}

BATCH 2 SETTINGS:
- System Prompt: "{prompt2}"
- Temperature: {temp2}, Top P: {top_p2}, Max Tokens: {max_tokens2}, Runs: {n_runs2}

BATCH 2 SAMPLE RESPONSE:
{response2}

Provide your analysis structured explicitly as follows:

1. **Query Alignment and Intent Capture**:  
   Clearly state whether each batch's response accurately and fully addressed the specific user query ("{query}"). Provide concrete examples from each response indicating completeness, accuracy, relevance, and depth of information.

2. **Prompt Instruction Adherence**:  
   Analyze explicitly if each batch clearly followed its given custom instruction ("{prompt1}" vs "{prompt2}"). Provide evidence from each response demonstrating alignment or misalignment with these instructions.

3. **Parameter Effects on Response Quality**:  
   Evaluate how the specific parameter settings (temperature, top_p, max_tokens) affected the responses practically and noticeably, referencing clear examples from each batch.

4. **Overall Batch Effectiveness**:  
   Based on query alignment, prompt adherence, and parameter settings, clearly state which batch provided a superior response to the query, and justify your reasoning explicitly.

5. **Specific Actionable Recommendations**:  
   Provide explicit suggestions for how prompts and parameters can be concretely improved for similar future queries. Include practical rephrasing examples, ideal parameter adjustments, and clearly indicate how these recommendations directly address gaps observed in the current responses. Avoid generic suggestions—make your recommendations explicitly tied to examples from the provided responses and the original query.
    
    Args:
        results: dict containing batch comparison results
        
    Returns:
        str: LLM-generated analysis
    """
    # Extract the query
    query = results.get("query", "No query provided")
    
    # Extract batch 1 parameters, prompt, and sample response
    batch1 = results.get("batch_1", {})
    batch1_params = batch1.get("parameters", {})
    batch1_results = batch1.get("results", [])
    
    # Get system prompt from either location (for backward compatibility)
    system_prompt1 = batch1.get("system_prompt", batch1_params.get("system_prompt", "Default prompt"))
    if not system_prompt1:
        system_prompt1 = "Default prompt"
    
    temp1 = batch1_params.get("temperature", "N/A")
    top_p1 = batch1_params.get("top_p", "N/A")
    max_tokens1 = batch1_params.get("max_tokens", "N/A")
    n_runs1 = batch1_params.get("n_runs", 0)
    
    # Get first successful response from batch 1
    response1 = "No response available"
    for result in batch1_results:
        if "answer" in result and result["answer"]:
            response1 = result["answer"]
            break
    
    # Extract batch 2 parameters, prompt, and sample response
    batch2 = results.get("batch_2", {})
    batch2_params = batch2.get("parameters", {})
    batch2_results = batch2.get("results", [])
    
    # Get system prompt from either location (for backward compatibility)
    system_prompt2 = batch2.get("system_prompt", batch2_params.get("system_prompt", "Default prompt"))
    if not system_prompt2:
        system_prompt2 = "Default prompt"
    
    temp2 = batch2_params.get("temperature", "N/A")
    top_p2 = batch2_params.get("top_p", "N/A")
    max_tokens2 = batch2_params.get("max_tokens", "N/A")
    n_runs2 = batch2_params.get("n_runs", 0)
    
    # Get first successful response from batch 2
    response2 = "No response available"
    for result in batch2_results:
        if "answer" in result and result["answer"]:
            response2 = result["answer"]
            break
    
    # Format the prompt with extracted data
    prompt = COMPACT_SUMMARY_PROMPT.format(
        query=query,
        prompt1=system_prompt1[:300] + "..." if len(system_prompt1) > 300 else system_prompt1,
        temp1=temp1,
        top_p1=top_p1,
        max_tokens1=max_tokens1,
        n_runs1=n_runs1,
        response1=response1[:500] + "..." if len(response1) > 500 else response1,
        prompt2=system_prompt2[:300] + "..." if len(system_prompt2) > 300 else system_prompt2,
        temp2=temp2,
        top_p2=top_p2,
        max_tokens2=max_tokens2,
        n_runs2=n_runs2,
        response2=response2[:500] + "..." if len(response2) > 500 else response2
    )
    
    # Generate the analysis
    assistant = FlaskRAGAssistant(settings={
        "temperature": 0.3,
        "max_tokens": 1000
    })
    
    try:
        answer, *_ = assistant.generate_rag_response(prompt)
        return answer
    except Exception as e:
        return f"Error generating summary: {str(e)}"
 
                       