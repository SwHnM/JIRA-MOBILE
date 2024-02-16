import re

# Function to extract attachment references from comment body
def extract_attachment_references(comment_body):
    # Regular expression pattern to match attachment references
    pattern = r'!(.*?)\|thumbnail!'
    attachment_references = re.findall(pattern, comment_body)
    return attachment_references

def clean_comment(comment):
    # Remove [~ and ] from the mention
    comment_names = re.sub(r'\[\~(.*?)\]', r'\1', comment)
    
    # Parse links and make them clickable
    comment_with_links = re.sub(r'\b(https?://\S+)\b', r'<a href="\1">\1</a>', comment_names)
    
    # Replace italic formatting
    comment_with_italics = re.sub(r'_(.*?)_', r'<i>\1</i>', comment_with_links)
    
    # Replace bold formatting
    comment_with_bold = re.sub(r'\*(.*?)\*', r'<b>\1</b>', comment_with_italics)
    
    # Replace underline formatting
    comment_with_underline = re.sub(r'\+(.*?)\+', r'<u>\1</u>', comment_with_bold)

    comment_remove_attachments = re.sub(r'!(.*?)\|thumbnail!', r'', comment_with_underline)
    
    # Replace red text formatting
    cleaned_comment = re.sub(r'{color:#de350b}(.*?){color}', r'<span style="color:#de350b;">\1</span>', comment_remove_attachments)
    
    return cleaned_comment




    

    