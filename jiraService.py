from jira import JIRA
import os

class JIRAService:
    def __init__(self, username, password, server_url):
        self.username = username
        self.password = password
        self.server_url = server_url
        self.jira = JIRA(basic_auth=(username, password), options={'server': server_url})

    def get_all_fields(self):
        #gets all the fields in JIRA
        return self.jira.fields()

    def get_issue(self, issue_key):
        return self.jira.issue(issue_key)

    def get_issues_from_jql(self, jql_str):
        # Execute the JQL query
        issues = self.jira.search_issues(jql_str)

        # Convert found issues to a list of dicts for easier manipulation
        issue_list = [{'issue_key': i.key, 'summary': i.fields.summary, 'status': i.fields.status} for i in issues]
        return issue_list    

    def get_summary(self, issue_key):
        issue = self.get_issue(issue_key)
        return issue.fields.summary
    
    def get_platform(self, issue_key):
        issue = self.get_issue(issue_key)
        
        return issue.fields.customfield_12207
    
    def get_sm_page(self, issue_key):
        issue = self.get_issue(issue_key)
        
        return issue.fields.customfield_108529
    
    def get_fields(self, issue_key):
        issue = self.get_issue(issue_key)
        return issue.raw['fields']
    
    def get_comments(self, issue_key):
        issue = self.get_issue(issue_key)
        return issue.fields.comment.comments
    
    def assign(self, issue, assignee):
        self.jira.assign_issue(issue, assignee)

    def makeComment(self, issue, comment):
        self.jira.add_comment(issue, comment)

    def makePrivateComment(self, issue, comment):
        self.jira.add_comment(issue, comment, is_internal=True)

    def get_transitions(self, issue_key):
        transitions = self.jira.transitions(issue_key)
        return {t['id']: t['name'] for t in transitions}
    
    def transition_issue(self, issue_key, transition_id):
        try:
            self.jira.transition_issue(issue_key, transition_id)
            return True, "Issue transitioned successfully."
        except Exception as e:
            return False, f"Failed to transition issue: {str(e)}"
        
    def attachments(self, issue_key):
        issue = self.get_issue(issue_key)
        attachments = issue.fields.attachment

        attachment_dict = {}
        
        for attachment in attachments:
            try:
                    attachment_dict[attachment.filename] = attachment.id
            except:
                 print('Attachment Deleted')
        
        return attachment_dict


 
    def download_attachment(self, attachment_id):
        
        attached_file = self.jira.attachment(attachment_id)
        
        save_directory = 'static/attachments/'
        file_path = save_directory + attached_file.filename


        if os.path.isfile(file_path):
            #added this so that images display properly. othewise it tries to get it from the wrong directory
            file_path_for_html = '/'+file_path
            return file_path_for_html
        else:
            # putting this download variable here as it seems like python gets it anway it's its initialized.
            download = attached_file.get()
            with open(file_path, 'wb') as f:
                f.write(download)
                file_path_for_html = '/'+file_path
                return file_path_for_html
                
        

        

