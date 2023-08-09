import re
def choose_community_extract_info(input_string):
    input_string = input_string.strip()
    action = ''
    community_name = ''
    house_type = ''
    reason = ''

    # Define the patterns for the two expected formats
    choose_pattern = r".*?Action: Choose\s*Result:\s*'?.*?My choice is (?:the )?\[?((?:large|middle|small)\s?\w+)\]? in (?:the )?\[?(\w+)\]?.*?'?\s*Reason: (.+)$"
    not_choose_pattern = r".*?Action: Not Choose\s*Result: (.+)\s*Reason：(.+)$"

    # Try to match the input_string with the first format
    match = re.search(choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
    if match:
        action = 'Choose'
        house_type = match.group(1).replace(" ", "_")  # replace the space with an underscore
        community_name = match.group(2)
        reason = match.group(3)
        return True, action, community_name, house_type, reason

    # Try to match the input_string with the second format
    match = re.search(not_choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
    if match:
        action = 'Not Choose'
        reason = match.group(2)
        return True, action, community_name, house_type, reason

    # If the input_string does not match any of the expected formats
    return False, action, community_name, house_type, reason

# Modifying the function to handle optional underscore between 'house' and the id

# def choose_house_extract_info(input_string):
#     input_string = input_string.strip()
#     action = ''
#     house_id = ''
#     reason = ''
#
#     # Define the patterns for the two expected formats
#     choose_pattern = r".*?Action: Choose\s*Result:\s*'?.*My choice is the house\s?_?(\d+).*'?\s*Reason: (.+)$"
#     not_choose_pattern = r".*?Action: Not Choose\s*Result: (.+)\s*Reason：(.+)$"
#
#     # Try to match the input_string with the first format
#     match = re.search(choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
#     if match:
#         action = 'Choose'
#         house_id = 'house_' + match.group(1)
#         reason = match.group(2)
#         return True, action, house_id, reason
#
#     # Try to match the input_string with the second format
#     match = re.search(not_choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
#     if match:
#         action = 'Not Choose'
#         reason = match.group(2)
#         return True, action, house_id, reason
#
#     # If the input_string does not match any of the expected formats
#     return False, action, house_id, reason

def choose_house_extract_info(input_string):
    input_string = input_string.strip()
    print(input_string)
    house_id = ''
    reason = ''

    # Define the patterns for the two expected formats
    choose_pattern = r".*?Action: Choose\s*Result:\s*'?.*My choice is(?: the)? house\s?_?(\d+).*'?\s*Reason: (.+)$"
    not_choose_pattern = r".*?Action: Not Choose\s*Result: (.+)\s*Reason：(.+)$"

    # Try to match the input_string with the first format
    match = re.search(choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
    if match:
        house_id = 'house_' + match.group(1)
        reason = match.group(2)
        return True, True, house_id, reason

    # Try to match the input_string with the second format
    match = re.search(not_choose_pattern, input_string, re.MULTILINE | re.IGNORECASE)
    if match:
        reason = match.group(2)
        return True, False, house_id, reason
    return False, False, house_id, reason
str2 = """
Action: Choose
Result: My choice is the house_3.
Reason: House 3 has a good location, good elevator access and the lowest rent of all the options. The sound insulation is not the best, but it is acceptable.
"""
str3 = """
Action: Choose
Result: My choice is house_3.
Reason: House 3 has a good location, good elevator access and the lowest rent of all the options. The sound insulation is not the best, but it is acceptable.
"""

print(choose_house_extract_info(str2))
print(choose_house_extract_info(str3))


