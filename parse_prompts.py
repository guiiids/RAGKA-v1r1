import docx
import json
import re

def parse_uat_document(file_path):
    doc = docx.Document(file_path)
    
    test_cases = []
    current_category = None
    current_prompt = None
    current_expected = None
    
    # State machine flags
    parsing_prompt = False
    parsing_expected = False

    # Combine all paragraphs into a single string with markers for structure
    full_text = "\n".join([p.text for p in doc.paragraphs])

    # Split the text into major product sections
    section_titles = ["Genomics", "GC", "LC", "iLab", "OpenLab CDS", "Molecular Spectroscopy"]
    # Create a regex pattern to split the document by these titles
    split_pattern = r'\n(' + '|'.join(re.escape(title) for title in section_titles) + r')'
    
    sections = re.split(split_pattern, full_text)
    
    # The first element is usually the title, so we skip it.
    # We iterate over pairs of (delimiter, content)
    for i in range(1, len(sections), 2):
        category = sections[i]
        content = sections[i+1]
        
        # Split each section into prompt/follow-up blocks
        prompt_blocks = re.split(r'Follow-up prompt', content)
        
        # Process the first block (initial prompt)
        initial_block = prompt_blocks[0]
        
        try:
            prompt_match = re.search(r'Prompt\n(.*?)\nExpected Answer', initial_block, re.DOTALL)
            expected_match = re.search(r'Expected Answer(?: and Citations)?\n(.*?)(?=\nSources Utilized|\Z)', initial_block, re.DOTALL)

            if not prompt_match or not expected_match:
                continue

            initial_prompt = prompt_match.group(1).strip()
            initial_expected = expected_match.group(1).strip().replace("SAGE AI Agent", "").strip()

            # Process subsequent blocks (follow-ups)
            if len(prompt_blocks) > 1:
                for follow_up_block in prompt_blocks[1:]:
                    # The follow-up prompt is the first line of the block
                    follow_up_lines = follow_up_block.strip().split('\n')
                    follow_up_prompt = follow_up_lines[0].strip()
                    
                    follow_up_expected_match = re.search(r'Expected Answer(?: and Citations)?\n(.*?)(?=\nSources Utilized|\Z)', follow_up_block, re.DOTALL)
                    
                    follow_up_expected = ""
                    if follow_up_expected_match:
                        follow_up_expected = follow_up_expected_match.group(1).strip().replace("SAGE AI Agent", "").strip()

                    # Add the pair to our test cases
                    test_cases.append({
                        "category": category,
                        "prompt": initial_prompt,
                        "expected_answer": initial_expected,
                        "follow_up_prompt": follow_up_prompt,
                        "follow_up_expected_answer": follow_up_expected
                    })
                    
                    # The current follow-up becomes the "initial" for the next iteration in the document's logic
                    initial_prompt = follow_up_prompt
                    initial_expected = follow_up_expected
            else:
                 # Add test cases that only have an initial prompt
                 test_cases.append({
                        "category": category,
                        "prompt": initial_prompt,
                        "expected_answer": initial_expected,
                        "follow_up_prompt": "",
                        "follow_up_expected_answer": ""
                    })

        except Exception as e:
            print(f"Error processing block in category {category}: {e}")

    return test_cases

if __name__ == '__main__':
    file_path = '/Users/vieirama/Downloads/UAT prompts and answers.docx'
    parsed_data = parse_uat_document(file_path)
    
    with open('prompts.json', 'w') as f:
        json.dump(parsed_data, f, indent=2)
        
    print(f"Successfully parsed {len(parsed_data)} test cases and saved to prompts.json")
