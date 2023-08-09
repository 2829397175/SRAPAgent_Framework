summary_prompt="""Progressively summarize new lines provided, adding onto the previous summary returning a new summary.

EXAMPLE
Current summary:
You think community_1 have inconvenient facilities. And you didn't make a choce.

New lines:
Thought: Community_2 is close to my wife's workplace and my child's school.
Output: My choice is community_2.

New summary:
You think community_2 is ideal for your family members, better than community_1. And you choose community_2.
END OF EXAMPLE

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:"""