import json5
import regex
import re

def parse_agent_result_and_get_json(result):
    try:
        # Convert result to string or extract its `content` field
        if isinstance(result, dict) and 'content' in result:
            result_string = result['content']
        elif hasattr(result, 'content'):
            result_string = result.content
        else:
            result_string = str(result)

        result_string = result_string.strip()

        # Extract JSON from code block
        pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(pattern, result_string, re.DOTALL)
        if match:
            json_string = match.group(1).strip()
        else:
            # Fallback regex for standalone JSON object
            json_pattern = r'\{(?:[^{}]|(?R))*\}'
            match = regex.search(json_pattern, result_string)
            if match:
                json_string = match.group().strip()
            else:
                print("No valid JSON match found")
                return None

        # Clean the JSON string and parse it
        json_string = json_string.replace('\n', '').replace('\r', '').strip()
        parsed_json = json5.loads(json_string)

        return parsed_json

    except Exception as error:
        print(f"Error parsing JSON: {error}")
        print("Raw Result String:", result_string)
        raise
