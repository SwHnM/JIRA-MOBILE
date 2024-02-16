from jiraService import JIRAService
from dateParser import parse_date
from commentParser import extract_attachment_references, clean_comment
from directApiRequests import full_comment

class Ticket:
    def __init__(self, username, password, issue_key):
        self.username = username
        self.password = password
        self.issue_key = issue_key

    def load(self):
        jira = JIRAService(self.username, self.password, "https://servicedesk.isha.in")
        issue_key = self.issue_key
        issue = jira.get_issue(issue_key)
        # Gets status for routing in main.py

        status=issue.fields.status

        # Get all fields
        all_fields = jira.get_all_fields()
        field_map = {field['id']: field['name'] for field in all_fields}

        fields = {}
        # Replace field keys with their corresponding names
        for field_id in issue.raw['fields']:
            field_name = field_map.get(field_id, field_id)
            field_val = issue.raw['fields'][field_id]
            if field_val is not None and field_val != "Unresolved" and field_val != 0.0 and field_val != []:
                fields[field_name] = field_val

        # Transitions and workflow
        transitions = jira.get_transitions(issue_key)

        # Gets list of attachments
        attachments = jira.attachments(issue_key)

        # Gets participants, reporter, assignee
        try:
            participants = fields['Request participants']
        except:
            participants = {}
            print('ticket has no participants')

#####
        raw_comments_api_call = full_comment(issue_key, self.username, self.password)
       

#####
        
        # Comments
        comment_list = []
        comments = raw_comments_api_call['comments']
        for comment in comments:   
            
            author = comment['author']['displayName']
            date = comment['created']
            body = comment['body']
            comment_props= comment['properties']
            
            if comment_props:
                try:
                    internal = not comment_props[0]['value']['allow']
                except:
                    internal = comment_props[0]['value']['internal']
                    
            
            

            # Search for referenced attachments and download them
            referenced_attachments = extract_attachment_references(body)
            download_dict = {k: attachments[k] for k in referenced_attachments if k in attachments}
            filepaths = [jira.download_attachment(download) for download in download_dict.values()]

            comment_info = {
                'author': author,
                'date': parse_date(date),
                'body': clean_comment(body),
                'attachments': filepaths,
                'internal' : internal,
            }
            comment_list.append(comment_info)

        comment_list.reverse()

        ticket = {
            'fields': fields,
            'comments': comment_list,
            'transitions': transitions,
            'issue_key': issue_key,
            'status' : status,
            'participants' :participants,
        }

        return ticket
