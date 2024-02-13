from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
from jiraService import JIRAService
import datetime
from dateParser import parse_date
from commentParser import extract_attachment_references, clean_comment
from loadTicket import Ticket

#####
#for testing speed of functions
#####

# import time

# start = time.time()
# end = time.time()
# print(end - start)

#####


app = Flask(__name__)
app.secret_key = os.urandom(24)  # set a secret key for sessions

@app.route("/", methods=('GET', 'POST'))
@app.route("/login", methods=('GET', 'POST'))
def login():
    

    return render_template('login.html')

@app.route("/auth", methods=('GET', 'POST'))

def auth():
    try:
        session["username"] = request.form.get("usern")
        session["password"] = request.form.get("passw")
        
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=30)



        return redirect('/dashboard')

        

    
    except:

        return redirect("/login")
    
@app.route("/logout", methods=('GET', 'POST'))

def logout():
    session.clear()
    return redirect("/login")

    
@app.route("/jql", methods=["GET", "POST"])
def jql():
    jql = request.form.get("jql")
    jql_checkbox = request.form.get("jql_checkbox")
    hide_closed_checkbox = request.form.get('hide_closed_tickets')


    if jql_checkbox != "checked":
        jql = "key = " + jql

    if hide_closed_checkbox == 'checked':
        jql = jql + ' AND status not in (delivered, closed, Canceled, cancelled, DONE, Resolved, "Text Delivered")'




    if jql == "":
        print('No JQL')
    else:
        session["jql"] = jql
    return redirect("/search")

@app.route("/comment", methods=["GET", "POST"])
def comment():
    username = session.get("username")
    password = session.get("password")
    issue = session.get('issue_key')
    comment = request.form.get("comment")
    path = '/search/' + issue

    jira= JIRAService(username, password, "https://servicedesk.isha.in")

    jira.makeComment(issue, comment)
    
    print(comment)

    return redirect(path)
    
    



@app.route("/search")
def search():
    try:
        username = session.get("username")
        password = session.get("password")
        jql = session.get("jql")

        jira= JIRAService(username, password, "https://servicedesk.isha.in")

        print(jql)
        
        # if jira.get_issues_from_jql sends an empty request, it will return all tickets. This prevents that from showing
        # Not sure this is the best logic buy it works.


        if jql == None:
            tickets = []
    

        else:
            try:
                #for a succesful api request
                tickets = jira.get_issues_from_jql(jql)

#### This section is under construction
                
                # for ticket in tickets:
                #     sm_page = jira.get_sm_page(ticket['issue_key'])
                #     platform = jira.get_platform(ticket['issue_key'])

                #     if sm_page == 'Adiyogi':
                #         ticket['sm_icon'] = '/static/assets/icons/adiyogi.webp' # insert filepath here

                #     # ticket['platform_icon'] = 'filepath' # insert filepath here


                #     # print(sm_page)
                #     # print(platform)
                #     print(tickets)

            except:
                try:
                    #if api request fails, checks if user is logged in. If they are, it assumes the jql had incorrect formatting. 
                    jira.get_issue('OCD-203')
                    tickets=[]

                except:
                    return redirect("/login")
    except:
        return redirect("/login")
        
        


    return render_template('search.html', tickets=tickets, last_jql=jql)

# This gets the issue key and saves it in state.
@app.route("/search/<issue_key>")
def save_issue(issue_key):
    session["issue_key"] = issue_key
    username = session.get("username")
    password = session.get("password")

    try:
        issue_key = session.get("issue_key")
        ticket = Ticket(username, password, issue_key).load()

        status = str(ticket["status"])


        if "OCD" in issue_key:
            try:
                if status == 'w/Publ- Proofing':
                    # print(str(ticket['transitions']))
                    comments = ticket["comments"]
                    last_comment = comments[0]
                    print(last_comment['attachments'])

                    transitions= ticket["transitions"]
                    print(transitions)

                    return render_template('OCd/ocd_proofing.html', last_comment=last_comment, fields=ticket['fields'], comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key)
                else:
                    return render_template('OCD/ocd.html', fields=ticket['fields'], comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key)
            except:
                return render_template('basic.html', fields=ticket['fields'], comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key)
        elif "EPSD" in issue_key:
            try:
                if status == 'Pending Requester Clarification':

                    # 'Creative under Proofing'

                    comments = ticket["comments"]
                    last_comment = comments[0]
                    print(last_comment)

                    return render_template('EPSD/epsd_proofing.html', last_comment=last_comment, fields=ticket['fields'], comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key)
            
                else:
                    return render_template('EPSD/epsd.html', username=username, fields=ticket['fields'], comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key)
            except:
                return render_template('basic.html')
        else:

            return render_template('OCD/epsd.html', username=username, fields=ticket['fields'], comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key)
    except:
        return redirect('/login')
    
# This route only exists for the navbar- it routes to the ticket saved in state
@app.route("/ticket")
def ticket():
    issue_key = session.get("issue_key")
    path = "/search/" + issue_key
    try:
    
        return redirect(path)
    except:
        return redirect('/search')
    
   




@app.route("/transition/<id>")
def transition(id):
    transition = id
    username = session.get("username")
    password = session.get("password")
    issue_key = session.get("issue_key")


    jira= JIRAService(username, password, "https://servicedesk.isha.in")

    jira.transition_issue(issue_key, transition)
    return redirect('/ticket')
        
    

        

@app.route("/settings")
def settings():
    username = session.get("username")
    password = session.get("password")
    
    if username:
        return render_template('settings.html', user=username)
    else:
        return redirect('/login')

@app.route("/dashboard")
def dashboard():
    try:
        username = session.get("username")
        password = session.get("password")

        jira= JIRAService(username, password, "https://servicedesk.isha.in")
        
        jql= 'assignee =' + username + ' AND type != "Imp New Content" AND type != "Imp Proofing" AND status not in ("text delivered", "EngPub Review", closed, Canceled, cancelled, DONE, Resolved, "Pending Requester Review", "Pending Requester Clarification", "W/Cust-Clar (Text)", "W/Cust-Review (Text)", "Text Under Review")'
        
        tickets = jira.get_issues_from_jql(jql)

    except:
        return redirect("/login")
        
    return render_template('dashboard.html', tickets=tickets, last_jql=jql, username=username)