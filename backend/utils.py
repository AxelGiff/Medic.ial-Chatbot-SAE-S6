import re

def simulate_token_count(text):
    """
    simulation token
    """
    if not text:
        return 0
    
    text = text.replace('\n', ' \n ')
    
    spaces_and_punct = sum(1 for c in text if c.isspace() or c in ',.;:!?()[]{}"\'`-_=+<>/@#$%^&*|\\')
    
    digits = sum(1 for c in text if c.isdigit())
    
    words = text.split()
    short_words = sum(1 for w in words if len(w) <= 2)
    
    code_blocks = len(re.findall(r'```[\s\S]*?```', text))
    urls = len(re.findall(r'https?://\S+', text))
    
    adjusted_length = len(text) - spaces_and_punct - digits - short_words
    
    token_count = (
        adjusted_length / 4 +
        spaces_and_punct * 0.25 +
        digits * 0.5 +
        short_words * 0.5 +
        code_blocks * 5 +
        urls * 4
    )
    
    return int(token_count * 1.1) + 1