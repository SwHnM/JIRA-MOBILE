from jiraService import JIRAService
from dateParser import parse_date
from commentParser import extract_attachment_references, clean_comment

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
            if field_val is not None and field_val != "Unresolved" and field_val != 0.0:
                fields[field_name] = field_val

        # Transitions and workflow
        transitions = jira.get_transitions(issue_key)

        # Gets list of attachments
        attachments = jira.attachments(issue_key)

        # Comments
        comment_list = []
        comments = jira.get_comments(issue_key)
        for comment in comments:
            author = comment.author
            date = comment.created
            body = comment.body

            # Search for referenced attachments and download them
            referenced_attachments = extract_attachment_references(body)
            download_dict = {k: attachments[k] for k in referenced_attachments if k in attachments}
            filepaths = [jira.download_attachment(download) for download in download_dict.values()]

            comment_info = {
                'author': author,
                'date': parse_date(date),
                'body': clean_comment(body),
                'attachments': filepaths
            }
            comment_list.append(comment_info)

        comment_list.reverse()

        ticket = {
            'fields': fields,
            'comments': comment_list,
            'transitions': transitions,
            'issue_key': issue_key,
            'status' : status,
        }

        return ticket
