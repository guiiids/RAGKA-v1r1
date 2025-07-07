from flask import Flask, render_template, request, jsonify
from rag_assistant_with_history_copy import FlaskRAGAssistantWithHistory
import os
import json

app = Flask(__name__)

# Ensure the 'templates' directory exists
if not os.path.exists('templates'):
    os.makedirs('templates')

# Ensure the 'static/js' directory exists
if not os.path.exists('static/js'):
    os.makedirs('static/js', exist_ok=True)

# Initialize the RAG assistant
assistant = FlaskRAGAssistantWithHistory()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_prompts')
def get_prompts():
    try:
        with open('prompts.json', 'r') as f:
            prompts = json.load(f)
        return jsonify(prompts)
    except FileNotFoundError:
        return jsonify([])


@app.route('/run_automation', methods=['POST'])
def run_automation():
    data = request.get_json()
    initial_question = data.get('initial_question')
    follow_up_question = data.get('follow_up_question')
    repetitions = data.get('repetitions', 1)

    if not all([initial_question, follow_up_question]):
        return jsonify({'error': 'Missing required questions'}), 400

    full_log = []
    for i in range(repetitions):
        # Create a new assistant for each cycle to ensure isolation
        assistant = FlaskRAGAssistantWithHistory()
        
        # Initial question
        answer1, sources1, _, _, _ = assistant.generate_rag_response(initial_question)
        
        # Follow-up question
        answer2, sources2, _, _, _ = assistant.generate_rag_response(follow_up_question)

        full_log.append({
            'cycle': i + 1,
            'initial_question': {
                'question': initial_question,
                'answer': answer1,
                'sources': sources1
            },
            'follow_up_question': {
                'question': follow_up_question,
                'answer': answer2,
                'sources': sources2
            }
        })
    
    return jsonify({'results': full_log})


@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    data = request.get_json()
    conversation = data.get('conversation')
    if not conversation:
        return jsonify({'error': 'No conversation provided'}), 400

    try:
        with open('conversation_log.txt', 'w', encoding='utf-8') as f:
            f.write(conversation)
        return jsonify({'message': 'Conversation saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)
