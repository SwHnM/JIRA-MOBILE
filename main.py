from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
from jiraService import JIRAService
import datetime
from dateParser import parse_date, parse_due_date
from loadTicket import Ticket
from directApiRequests import raw_search
import json
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
        username = request.form.get("usern")
        password = request.form.get("passw")
        session["username"] = username
        session["password"] = password
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=60)

## for user configs
        remove_dots= username.replace('.', '-')
        config_filename=f'{remove_dots}.json'
        config_path = f"static/users/{config_filename}"

        session['config_path'] = config_path

        if os.path.isfile(config_path):
            return redirect('/dashboard')
        else:
            return render_template('newuser.html', username=username)

    except:

        return redirect("/login")
    
@app.route("/newuser", methods=('GET', 'POST'))

def newuser():

    username = session.get('username')
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    config_path = session.get('config_path')

    default_decks = [
         {
                "name": "My Tickets",
                "jql": "assignee = currentUser() AND status not in ('text delivered','EngPub Review', closed, Canceled, cancelled, DONE, Resolved, 'Pending Requester Review', 'Pending Requester Clarification', 'W/Cust-Clar (Text)', 'W/Cust-Review (Text)', 'Text Under Review')",
                "color": "red",
                "icon": "fa-ghost"
            },
    ]


    user = {
        "username":username,
        "firstname":firstname,
        "lastname":lastname,
        "decks": default_decks
        }
    
    user_json_object = json.dumps(user, indent=4)

    with open(config_path, "w") as outfile:
        outfile.write(user_json_object)

    return redirect('/dashboard')
    
@app.route("/logout", methods=('GET', 'POST'))

def logout():
    session.clear()
    return redirect("/login")

    
@app.route("/jql", methods=["GET", "POST"])
def jql():
    jql = request.form.get("jql")
    
    hide_closed_checkbox = request.form.get('hide_closed_tickets')

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

@app.route("/privatecomment", methods=["GET", "POST"])
def privatecomment():
    username = session.get("username")
    password = session.get("password")
    issue = session.get('issue_key')
    comment = request.form.get("comment")
    path = '/search/' + issue

    jira= JIRAService(username, password, "https://servicedesk.isha.in")

    jira.makePrivateComment(issue, comment)
    
    print(comment)

    return redirect(path)


@app.route("/newdeck", methods=('GET', 'POST'))

def newdeck():
    name= request.form.get('deck-name')
    jql= request.form.get('deck-jql')
    color= request.form.get('deck-color')
    icon= request.form.get('deck-icon')


    config_path = session.get("config_path")

    with open(config_path, 'r') as userdata:
        user = json.load(userdata)
        decks = user['decks']

        decks.append({
            "name": name,
            "jql": jql,
            "color": color,
            "icon": icon
        })

    # Write the updated user data back to the file
    with open(config_path, 'w') as userdata:
        json.dump(user, userdata)

    return redirect('/dashboard')
    
    
@app.route("/queue", methods=('GET', 'POST'))

def queue():

    if not session.get('queued_tickets'):
        tickets_form = request.form.items()
        session['queued_tickets'] = [key for key, _ in tickets_form]
        session['queue_mode_active'] = True

    if session['queued_tickets']:
        current_ticket = session['queued_tickets'].pop(0)
        return redirect(f'/search/{current_ticket}')
    else:
        session['queue_mode_active'] = False
        return redirect('/queue_complete')





    


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
def display_issue(issue_key):
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

        queue_mode_active=False

        if session.get('queue_mode_active'):
            queue_mode_active=True


        if "OCD" in issue_key:
            whitelist_file = open("static/OCD_whitelist.txt", "r") 
            data = whitelist_file.read() 
            whitelist = data.split("\n") 
            whitelist_file.close()
            
            raw_fields = ticket["fields"]
            fields = {key: raw_fields[key] for key in whitelist if key in raw_fields}

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

        return render_template(template, last_comment=last_comment, fields=fields, comments=ticket['comments'], transitions=ticket['transitions'], issue_key=issue_key, queue_mode_active=queue_mode_active)
    
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
    
    if username:
        return render_template('settings.html', user=username)
    else:
        return redirect('/login')

@app.route("/dashboard")
def dashboard():
    try:
        username = session.get("username")
        password = session.get("password")
        config_path = session.get("config_path")

## loads info from config file
        userdata = open(config_path)
        user = json.load(userdata)
        
        decks = user['decks']

### decks is refering to the horizontal display of cards.
        
        social_media_account = "customfield_108529"
        all_languages = "customfield_12301"
        
        fields = ["summary", "assignee", "status", "duedate", "reporter", all_languages, social_media_account]

        for deck in decks:
            jql = deck['jql']
            tickets = raw_search(jql, fields, username, password)
            deck['tickets'] = tickets
            
            for ticket in tickets:
                try:
                    due_date = ticket['fields']['duedate']
                    parsed_due_date = parse_due_date(due_date)
                except:
                    parsed_due_date = 'No Due Date'
                
                ticket['fields']['duedate'] = parsed_due_date


#### Langs
                language_list = []

                if type(ticket['fields']["customfield_12301"]) == list:
                    if all(len(language_dict) >= 2 for language_dict in ticket['fields']["customfield_12301"]):
                        
                        for language_dict in ticket['fields']["customfield_12301"]:
                            language = language_dict['value']
                            language_list.append(language)
                    else:
                        language_list = ticket['fields']["customfield_12301"]['value']
                        
                ticket['fields']['languages'] = language_list
        

                print(language_list)

###### This if to replace ticket platform with appropriate icon. It returns a filepath.
                
                try:
                    sm_act = ticket['fields']['customfield_108529']['value']

                    if sm_act == 'Adiyogi':
                        icon = '/static/assets/icons/Adiyogi.svg'
                    elif sm_act == 'Conscious Planet':
                        icon = '/static/assets/icons/earth.png'
                    elif sm_act == 'Linga Bhairavi':
                        icon = '/static/assets/icons/Devi.svg'
                    elif sm_act == 'Isha Foundation':
                        icon = '/static/assets/icons/ishalogo.png'
                    elif sm_act == 'Sadhguru':
                        icon = '/static/assets/icons/sadhguru.svg'

                    ticket['platform_icon'] = icon
                        
                except:
                    print('no icon')


                



            
            
                

            

        icons_file = open("static/icons.txt", "r") 
        data = icons_file.read() 
        icons = data.split("\n") 
        icons_file.close()


    except Exception as e:
        print(e)
        traceback.print_exc()
        return redirect('/login')
        
    return render_template('dashboard.html', decks = decks, icons=icons, last_jql=jql, username=username)

@app.route("/queue_complete")
def queue_complete():
    return render_template('queue_complete.html')

