import sys
import platform
import subprocess
import webview
import os
import json
from functools import wraps

from emis_api.emis_api import EMISStudentAPI
from emis_api.emis_auth_module import Authenticator

SESSION_FILE = ".env"

AUTH = None
API = None

USERSTORAGE = ".userData"

class UI_Api:

    API_MAP = {
        "student_info": (
            "student_info.json",
            "get_student_info",
        ),
        "study_progress": (
            "study_progress.json",
            "get_study_progress_info",
        ),
        "required_courses": (
            "requiredCourses.json",
            "get_required_courses_and_graduation_credits",
        ),
        "all_grades": (
            "AllGrades.json",
            "get_all_years_course_grades",
        ),
        "missing_required_courses": (
            "get_missing_required_courses.json",
            "get_missing_required_courses",
        ),
        "course_selection": (
            "get_course_selection_by_course_code.json",
            "get_course_selection_by_course_code",
        ),
    }

    def _get_api(self):
        global AUTH, API
        if AUTH is None or API is None:
            self.auth_login()
        try:
            return API
        except Exception:
            self.auth_login()
            return API

    def _data(self, filename, api_method, withUpdate=False):
        if withUpdate:
            api = self._get_api()
            data = getattr(api, api_method)()
            save_storage_data(filename, data)
            return data

        return get_storage_data(filename)
    
    def progress_on_graduation(self):
        """
        it return a dict with percentage of graduation progress
        """
        data = self.get_score()
        return {"total_percent": round(data["total_credit"]/data["required_total"]*100,2)}
        

    def get_score(self):
        department = self.student_info()["department"]

        AllGrades  = self.all_years_course_grades()
        requiredCourses = self.required_courses_and_graduation_credits()
        if AllGrades is None or requiredCourses is None:
            AllGrades  = self.all_years_course_grades(withUpdate=True)
            requiredCourses = self.required_courses_and_graduation_credits(withUpdate=True)

        courses = AllGrades["courses"]
        electiveScore = 0

        for course in courses:
            if course["status"] == "passed" and course["requirement_type"] == "選修Elective" and department in course["specialization"]:
                electiveScore += course["credits_up"]

        requiredScore = 0
        for course in courses:
            if course["status"] == "passed" and course["requirement_type"] == "必修Required":
                requiredScore += course["credits_up"]

        score_pe_class = 0
        for course in courses:
            if course["status"] == "passed" and "體育" in course["specialization"]: #體育不計入學分
                score_pe_class += course["credits_up"]

        

        credits = requiredCourses["credits"]
        total_credit = credits["total"]
        required = credits["required"]
        elective_min = credits["elective_min"]

        real_creadit = AllGrades["total_earned_credits"]-score_pe_class #看需求加入

        return {"total_credit": real_creadit,
                "required_credit": requiredScore,
                "elective_credit": electiveScore,
                "total_need": total_credit-real_creadit,
                "required_need": required-requiredScore, 
                "elective_need": elective_min-electiveScore,
                "required_total": total_credit,
                }
    
    def update_all_user_data(self):
        self.student_info(withUpdate=True)
        self.all_years_course_grades(withUpdate=True)
        self.required_courses_and_graduation_credits(withUpdate=True)
        self.missing_required_courses(withUpdate=True)
        self.course_selection_by_course_code(withUpdate=True)
        return {"done": True}
        
    def student_info(self, withUpdate=False):
        return self._data(
            "student_info.json",
            "get_student_info",
            withUpdate
        )
    
    def study_progress_info(self, withUpdate=False):
        return self._data(
            "study_progress.json",
            "get_study_progress_info",
            withUpdate
        )
    
    def required_courses_and_graduation_credits(self, withUpdate=False):
        return self._data(
            "requiredCourses.json",
            "get_required_courses_and_graduation_credits",
            withUpdate
        )
        
    def all_years_course_grades(self, withUpdate=False):
        return self._data(
            "AllGrades.json",
            "get_all_years_course_grades",
            withUpdate
        )

    def missing_required_courses(self, withUpdate=False):
        return self._data(
            "get_missing_required_courses.json",
            "get_missing_required_courses",
            withUpdate
        )

    def course_selection_by_course_code(self, withUpdate=False):
        return self._data(
            "get_course_selection_by_course_code.json",
            "get_course_selection_by_course_code",
            withUpdate
        )

    def auth_login(self):
        global AUTH, API
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            username = data["username"]
            password = data["password"]
        try:
            AUTH = Authenticator(username=username, password=password)
            if AUTH.perform_auth() == False:
                raise RuntimeError("Authentication failed")
            API = EMISStudentAPI(AUTH.session)
            return API
        except Exception:
            self.logout()
            sys.exit(0)

    def check_saved_session(self):
            """Called automatically on app launch to check if user is logged in."""
            if os.path.exists(SESSION_FILE):
                try:
                    with open(SESSION_FILE, "r") as f:
                        data = json.load(f)
                        if data["loginPass"] == True:
                            return {"logged_in": True, "username": data["username"]}
                except Exception:
                    pass
            return {"logged_in": False}

    def authenticate(self, username, password):
        """Validates credentials and saves session if valid."""
        global AUTH, API
        auth = Authenticator(username=username, password=password)

        if auth.perform_auth() != False:
            AUTH = auth
            API = EMISStudentAPI(AUTH.session)
            session_data = {
                "loginPass": True,
                "username": username,
                "password": password,
            }

            # Save session to file
            with open(SESSION_FILE, "w") as f:
                json.dump(session_data, f)
            return True
        return False

    def logout(self):
        """Deletes saved session file on logout."""
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        return True

def notify_user_and_exit(title, message, win_url=None):
    os_type = platform.system()

    if os_type == "Linux":
        for cmd in [["zenity", "--error", f"--title={title}", f"--text={message}"],
                    ["kdialog", "--error", message, "--title", title]]:
            try:
                subprocess.run(cmd, check=True)
                break
            except Exception:
                pass

    elif os_type == "Windows":
        ps_script = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms]::MessageBox::Show("{message}", "{title}")'
        subprocess.run(["powershell", "-Command", ps_script])
        if win_url:
            import webbrowser
            webbrowser.open(win_url)

    sys.exit(1)

def get_storage_data(fileName:str):
    data = {}
    with open(".userData/"+fileName, "r", encoding="utf-8") as f:
        data = json.load(f)      
    return data

def save_storage_data(fileName:str,data):
    with open(".userData/"+fileName, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
            
if __name__ == '__main__':
    api = UI_Api()
    webview.create_window('TKU EMI Suckless', 'gui/index.html', js_api=api)
    try:
        webview.start(debug=True)
    except Exception as e:
        if platform.system() == "Linux":
            notify_user_and_exit(
                "Failed to start application window!",
                "This app requires WebKitGTK or Qt to run.\n"
                "Please install it using your system package manager:\n\n"
                "• Ubuntu/Debian: sudo apt install libwebkit2gtk-4.0-0\n"
                "• Fedora: sudo dnf install webkit2gtk3\n"
                "• Arch Linux: sudo pacman -S webkit2gtk"
            )
        elif platform.system() == "Windows":
            notify_user_and_exit(
                "WebView2 Required",
                "Microsoft Edge WebView2 is required to run this application.",
                win_url="https://developer.microsoft.com/en-us/microsoft-edge/webview2/"
            )
        else:
            notify_user_and_exit("Startup Error", f"Failed to start app: {e}")
