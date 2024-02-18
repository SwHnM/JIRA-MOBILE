from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
from jiraService import JIRAService
import datetime
from dateParser import parse_date
from commentParser import extract_attachment_references, clean_comment
from loadTicket import Ticket
from directApiRequests import raw_search

import traceback

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
    try:
        session["issue_key"] = issue_key
        username = session.get("username")
        password = session.get("password")
        
        issue_key = session.get("issue_key")
        ticket = Ticket(username, password, issue_key).load()
        status = str(ticket["status"])

        comments = ticket["comments"]
        if comments:
            last_comment = comments[0]
        else:
            last_comment = {}

        if "OCD" in issue_key:
            if status == 'w/Publ- Proofing':
                template = 'OCD/ocd_proofing.html'
            else:
                template = 'OCD/ocd.html'
        elif "EPSD" in issue_key:
            whitelist_file = open("static/whitelist.txt", "r") 
            data = whitelist_file.read() 
            whitelist = data.split("\n") 
            whitelist_file.close()

            raw_fields = ticket["fields"]
            fields = {key: raw_fields[key] for key in whitelist if key in raw_fields}

            if status == 'Pending Requester Clarification':
                template = 'EPSD/epsd_proofing.html'
            else:
                template = 'EPSD/epsd.html'
        else:
            template = 'basic.html'

        return render_template(template, last_comment=last_comment, fields=ticket['fields'], comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key)
    
    except Exception as e:
        error_message = str(e)
        traceback_details = traceback.format_exc()
        print(f"An error occurred: {error_message}")
        print(f"Traceback: {traceback_details}")
        return redirect('/dashboard')

    
# This route only exists for the navbar- it routes to the ticket saved in state
@app.route("/ticket")
def ticket():
    
    try:
        issue_key = session.get("issue_key")
        path = "/search/" + issue_key
    
        return redirect(path)
    except:
        try:
            return redirect('/search')
        except:
            return redirect('/login')
    
   




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

### decks is refering to the horizontal display of cards.
        
        social_media_account = "customfield_108529"
        
        fields = ["summary", "description", "assignee", "status", social_media_account]
        
        deck_db = [
            {'name':"My Tickets",
             'jql': f'assignee = currentUser() AND status not in ("text delivered","EngPub Review", closed, Canceled, cancelled, DONE, Resolved, "Pending Requester Review", "Pending Requester Clarification", "W/Cust-Clar (Text)", "W/Cust-Review (Text)", "Text Under Review")',
             'color': 'red',
             'icon': 'fa-ghost'},
            
            {'name':"Klemen's Tickets",
             'jql': 'assignee = klemen.b AND status not in ("text delivered", "EngPub Review", closed, Canceled, cancelled, DONE, Resolved, "Pending Requester Review", "Pending Requester Clarification", "W/Cust-Clar (Text)", "W/Cust-Review (Text)", "Text Under Review")',
             'color': 'green',
             'icon': 'fa-dragon'},

            {'name':"Recent Tickets",
             'jql': 'issueKey in issueHistory() order by lastViewed DESC',
             'color': 'green',
             'icon': 'fa-chess-pawn'},
        ]

        for deck in deck_db:
            jql = deck['jql']
            tickets = raw_search(jql, fields, username, password)
            deck['tickets'] = tickets

    
        # jql= 'assignee =' + username + ' AND type != "Imp New Content" AND type != "Imp Proofing" AND status not in ("text delivered", "EngPub Review", closed, Canceled, cancelled, DONE, Resolved, "Pending Requester Review", "Pending Requester Clarification", "W/Cust-Clar (Text)", "W/Cust-Review (Text)", "Text Under Review")'

    except:
        return redirect("/login")
        
    return render_template('dashboard.html', decks = deck_db, last_jql=jql, username=username)