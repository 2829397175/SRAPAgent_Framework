summary_prompt="""Progressively summarize new lines provided, adding onto the previous summary returning a new summary.


Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:"""