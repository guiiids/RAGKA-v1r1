import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime
from db_manager import DatabaseManager

def make_filter_bar(sel):
    return f"""
    <div class="max-w-5xl min-w-[800px] mx-auto flex justify-end mb-4">
      <select class="px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-gray-700 bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
        <option {"selected" if sel=="All Votes" else ""}>All Votes</option>
        <option {"selected" if sel=="Positive Votes" else ""}>Positive Votes</option>
        <option {"selected" if sel=="Negative Votes" else ""}>Negative Votes</option>
        <option {"selected" if sel=="With Comments" else ""}>With Comments</option>
      </select>
    </div>
    """

def make_pager(page, total):
    prev_disabled = page <= 1
    next_disabled = page >= total
    return f"""
    <div class="max-w-5xl min-w-[800px] mx-auto flex items-center justify-center space-x-6 my-8">
      <button class="px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm text-gray-700 font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 {'opacity-50 cursor-not-allowed' if prev_disabled else 'hover:bg-gray-100'}" {'disabled' if prev_disabled else ''}>
        ← Previous
      </button>
      <span class="text-sm font-medium text-gray-700">Page {page} of {total}</span>
      <button class="px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm text-gray-700 font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 {'opacity-50 cursor-not-allowed' if next_disabled else 'hover:bg-gray-100'}" {'disabled' if next_disabled else ''}>
        Next →
      </button>
    </div>
    """ 

def make_table(rows):
    """
    Render a Tailwind-styled table for the given list of feedback dicts.
    """
    cells = ""
    for item in rows:
        vote = "POSITIVE" if "Looks Good / Accurate & Clear" in item["feedback_tags"] else "NEGATIVE"
        color = "green" if vote == "POSITIVE" else "red"
        pill = (
            f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full '
            f'text-xs font-medium bg-{color}-100 text-{color}-800">{vote}</span>'
        )
        cells += f"""
        <tr class="hover:bg-gray-50 transition-colors duration-150">
          <td class="px-4 py-3 border-l-4 border-{color}-500">{item['vote_id']}</td>
          <td class="px-4 py-3">{pill}</td>
          <td class="px-4 py-3">
            {item['question'][:30]}{"…" if len(item['question']) > 30 else ""}
          </td>
          <td class="px-4 py-3">
            {'; '.join(item['feedback_tags'])[:30]}
            {"…" if len(item['feedback_tags']) > 3 else ""}
          </td>
          <td class="px-4 py-3">{item['timestamp']}</td>
          <td class="px-4 py-3">
            <button class="px-3 py-1.5 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
              Details
            </button>
          </td>
        </tr>
        """

    return f"""
    <script src="https://cdn.tailwindcss.com"></script>
    <div class="max-w-5xl min-w-[800px] mx-auto overflow-hidden rounded-lg shadow-lg border border-gray-200">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vote</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Query</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comment</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {cells}
        </tbody>
      </table>
    </div>
    """


def make_card(title, value, extra=""):
    return f"""
    <div class="px-6 py-6 bg-white shadow-lg rounded-xl text-center border border-gray-100 hover:shadow-xl transition-shadow duration-300">
      <dt class="text-sm font-medium text-gray-500 truncate">{title}</dt>
      <dd class="mt-2 text-3xl font-bold text-gray-900">{value}</dd>
      {f'<dd class="mt-2 text-sm font-medium text-gray-500">{extra}</dd>' if extra else ""}
    </div>
    """

def display_feedback_dashboard():
    data = get_feedback_data()

    # 1) stats
    total = len(data)
    pos   = sum(1 for i in data if "Looks Good / Accurate & Clear" in i["feedback_tags"])
    neg   = total - pos
    com   = sum(1 for i in data if i["comment"].strip())
    pos_pct = f"{pos/total*100:.1f}%" if total else "0%"
    neg_pct = f"{neg/total*100:.1f}%" if total else "0%"
    com_pct = f"{com/total*100:.1f}%" if total else "0%"

    cards = f"""
    <div class="max-w-5xl min-w-[800px] mx-auto py-10">
      <h1 class="text-4xl font-extrabold text-gray-900 text-center">Feedback Analytics Dashboard</h1>
      <p class="mt-3 text-lg text-gray-600 text-center">Summary Statistics</p>
      <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {make_card("Total Votes", total)}
        {make_card("Positive Feedback", pos, pos_pct)}
        {make_card("Negative Feedback", neg, neg_pct)}
        {make_card("With Comments", com, com_pct)}
      </div>
    </div>
    """

    # 2) filter + pagination data
    filter_option = st.session_state.get("filter_option", "All Votes")
    filtered = filter_feedback_data(data, filter_option)
    items_per_page = 10
    total_pages = (len(filtered) - 1)//items_per_page + 1
    page = st.session_state.get("current_page", 1)
    start = (page - 1)*items_per_page
    page_data = filtered[start : start + items_per_page]

    # 3) assemble the final HTML
    html = "<script src='https://cdn.tailwindcss.com'></script>"
    html += cards
    html += make_filter_bar(filter_option)
    html += make_table(page_data)
    html += make_pager(page, total_pages)

    # 4) render everything in one go
    components.html(html, height=800, scrolling=True)
def display_feedback_details(item):
    """
    Display the detailed view for a single feedback item.
    """
    st.subheader(f"Details for Feedback ID: {item.get('vote_id', 'N/A')}")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.selected_feedback_id = None
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Query:**")
    st.text(item.get("question", "N/A"))

    st.markdown(f"**Timestamp:**")
    timestamp = item.get("timestamp", "")
    formatted_time = timestamp # Default to raw if formatting fails
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception as e:
            print(f"Timestamp formatting error: {e}") # Log error
            formatted_time = timestamp # Keep original if error
    elif isinstance(timestamp, datetime):
         formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")

    st.text(formatted_time)

    st.markdown(f"**Feedback Tags:**")
    st.write(", ".join(item.get("feedback_tags", [])))

    st.markdown(f"**Comment:**")
    st.text(item.get("comment", "N/A"))

    st.markdown("---")
    st.markdown("**Full Interaction:**")
    st.warning("Full interaction data (User/Bot messages) is not currently available in the data.")
    # Placeholder for future interaction display
    st.text_area("Interaction Log (Placeholder)", "User: ...\nBot: ...", height=150, disabled=True)

    st.markdown("---")
    st.markdown("**LLM Evaluation:**")
    # Placeholder for future LLM evaluation rendering
    st.info("LLM evaluation rendering area (to be implemented).")
    if st.button("Generate LLM Evaluation (Placeholder)"):
        st.info("LLM evaluation generation would be triggered here.")




def display_feedback_table(feedback_data):
    import streamlit.components.v1 as components

    rows = ""
    for item in feedback_data:
        vote = "POSITIVE" if "Looks Good / Accurate & Clear" in item["feedback_tags"] else "NEGATIVE"
        color = "green" if vote == "POSITIVE" else "red"
        pill = (
            f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full '
            f'text-xs font-medium bg-{color}-100 text-{color}-800">{vote}</span>'
        )
        rows += f"""
        <tr class="hover:bg-gray-50 transition-colors duration-150">
          <td class="px-4 py-3 border-l-4 border-{color}-500">{item['vote_id']}</td>
          <td class="px-4 py-3">{pill}</td>
          <td class="px-4 py-3">{item['question'][:30]}{"…" if len(item['question'])>30 else ""}</td>
          <td class="px-4 py-3">{'; '.join(item['feedback_tags'])[:30]}{"…" if len(item['feedback_tags'])>3 else ""}</td>
          <td class="px-4 py-3">{item['timestamp']}</td>
          <td class="px-4 py-3">
            <button class="px-3 py-1.5 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
              Details
            </button>
          </td>
        </tr>
        """

    html = f"""
    <script src="https://cdn.tailwindcss.com"></script>
    <div class="max-w-5xl mx-auto overflow-hidden rounded-lg shadow-lg border border-gray-200">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vote</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Query</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comment</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {rows}
        </tbody>
      </table>
    </div>
    """
    components.html(html, height=400, scrolling=True)


def get_feedback_data():
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT vote_id,
                       user_query AS question,
                       feedback_tags,
                       comment,
                       timestamp      
                FROM votes
                ORDER BY timestamp DESC
            """)
            feedback_data = []
            colnames = [desc[0] for desc in cursor.description]
            feedback_data = []
            for row in cursor.fetchall():
                item = dict(zip(colnames, row))
                item.setdefault("vote_id", None)
                item.setdefault("question", "")
                item.setdefault("feedback_tags", [])
                item.setdefault("comment", "")
                item.setdefault("timestamp", "")
                feedback_data.append(item)
            return feedback_data
    except Exception as e:
        print(f"Error fetching feedback data: {e}")
        return get_sample_feedback_data()
    finally:
        if conn:
            conn.close()


def filter_feedback_data(feedback_data, filter_option):
    if filter_option == "All Votes":
        return feedback_data
    if filter_option == "Positive Votes":
        return [item for item in feedback_data if "Looks Good / Accurate & Clear" in item["feedback_tags"]]
    if filter_option == "Negative Votes":
        return [item for item in feedback_data if "Looks Good / Accurate & Clear" not in item["feedback_tags"]]
    if filter_option == "With Comments":
        return [item for item in feedback_data if item["comment"].strip()]
    return feedback_data


def get_sample_feedback_data():
    return [
        {
            "vote_id": 21,
            "question": "what is test?",
            "feedback_tags": ["factualError", "irrelevant", "formatting"],
            "comment": "eberythmng",
            "timestamp": "2025-04-24T16:41:22Z"
        },
        {
            "vote_id": 20,
            "question": "what is an sandbox?",
            "feedback_tags": ["factualError", "missingInfo", "irrelevant", "tooVerbose"],
            "comment": "Details…",
            "timestamp": "2025-04-24T16:15:22Z"
        },
        {
            "vote_id": 12,
            "question": "is the crosslab test gated for registered sandboxes?",
            "feedback_tags": ["factualError", "missingInfo"],
            "comment": "investigate mismatch sources",
            "timestamp": "2025-04-17T22:44:19Z"
        }
    ]
if __name__ == "__main__":
    display_feedback_dashboard()
