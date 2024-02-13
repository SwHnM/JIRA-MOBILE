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

    
    # Remove everything between ! and |thumbnail! and also remove |thumbnail!
    cleaned_comment = re.sub(r'!(.*?)\|thumbnail!', '', comment_names)
    
    return cleaned_comment



    

    