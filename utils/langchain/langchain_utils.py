import json5
import regex
import re


def parse_agent_result_and_get_json(result):
    try:
        result_string = result
        # Parse the output and get JSON
        pattern = r'```json(.*?)```'
        match = re.search(pattern, result_string, re.DOTALL)
        if match:
            json_string = match.group(1)
            result_string = json5.loads(json_string)
        else:
            json_pattern = r'\{(?:[^{}]|(?R))*\}'
            match = regex.search(json_pattern, result_string)
            if match:
                json_string = match.group()
                result_string = json5.loads(json_string)
            else:
                print("No match found")

        return result_string
    except ValueError as error:
        print(result_string)
        raise error
