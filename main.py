import os
import sys

# Ensure PyInstaller runtime loads bundled GTK/WebKit typelibs or system libraries
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    typelib_path = os.path.join(bundle_dir, 'gi_typelibs')
    
    paths = []
    if os.path.exists(typelib_path):
        paths.append(typelib_path)
    
    # Common system typelib paths on different Linux distributions (e.g. Fedora, Debian/Ubuntu, Arch)
    system_paths = [
        "/usr/lib64/girepository-1.0",
        "/usr/lib/girepository-1.0",
        "/usr/lib/x86_64-linux-gnu/girepository-1.0",
        "/usr/lib/i386-linux-gnu/girepository-1.0"
    ]
    for p in system_paths:
        if os.path.exists(p) and p not in paths:
            paths.append(p)
            
    existing = os.environ.get('GI_TYPELIB_PATH')
    if existing:
        paths.append(existing)
        
    os.environ['GI_TYPELIB_PATH'] = os.pathsep.join(paths)

import platform
import subprocess
import webview
import json
from functools import wraps
import re

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
        "get_courses_we_have_this_semester": (
            "courses.json",
            "get_courses_we_have_this_semester",
        )
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
        self.courses_we_have_this_semester(withUpdate=True)

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
    
    def courses_we_have_this_semester(self, withUpdate=False):
        return self._data(
            "courses.json",
            "get_courses_we_have_this_semester",
            withUpdate
        )

    def schedule_my_class(self, schedule_data=None):
        """
        this function allow user add or remove class from their planing schedule
        schedule_data should be a dict with keys: "options" (add/remove), "course_code" (for add), "course_id" (for remove)
        example: {"options": "remove", "course_id": "12345"}
        """
        data = get_storage_data("my_class.json")
        if data is None:
            data = {}

        if schedule_data is None:
            return data
        
        if "options" in schedule_data:
            # Process the schedule data
            if  schedule_data["options"] == "add":
                modified_class = self.find_class_by_course_code(schedule_data["course_id"])
                if modified_class:
                    data.append(modified_class)

            elif schedule_data["options"] == "remove":
                data = [cls for cls in data if cls["course_id"] != schedule_data["course_id"]]
            elif schedule_data["options"] == "clear":
                data = []
            elif schedule_data["options"] == "load":
                data = self.course_selection_by_course_code()
                
            save_storage_data("my_class.json", data)
            return data
        else:
            return data

    def find_class_by_course_code(self, course_code):
        """
        Find a course by course code and map it to the normalized format.
        """
        data = get_storage_data("courses.json")

        for course in data:
            if course.get("seq") == course_code:
                return {
                    "course_id": course.get("seq", ""),
                    "dept": (
                        course.get("dept_block", "").split("－")[0]
                        if course.get("dept_block")
                        else ""
                    ),
                    "grade": course.get("grade", ""),
                    "course_name": course.get("title", "").strip(),
                    "course_code": course.get("seq", ""),
                    "credits": str(course.get("credits", "")),
                    "teachers": (
                        [course["teacher"]]
                        if course.get("teacher")
                        else []
                    ),
                    "schedule": normalize_schedule(course.get("times", [])),
                    "seat_numbers": [],  # Source data doesn't contain seat information.
                }

        return None
    
    def search_courses(self, options):

        title = options.get("title", "").lower()
        times = options.get("times", "").replace(" ", "")
        required = options.get("required", "")
        dept = options.get("dept_block", "").lower()

        result = []

        for course in self.courses:

            if title:
                if title not in course["title"].lower():
                    continue

            if required:
                if course["required"] != required:
                    continue

            if dept:
                if dept not in course["dept_block"].lower():
                    continue

            if times:
                course_time = "".join(course["times"]).replace(" ", "")
                if times not in course_time:
                    continue

            result.append(course)

        return result

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


def normalize_schedule(schedule):
    normalized = []

    for item in schedule:
        parts = [p.strip() for p in item.split("/")]

        if len(parts) >= 3:
            day, periods, room = parts[:3]

            # Pad every period to 2 digits
            periods = ",".join(f"{int(p):02d}" for p in periods.split(","))

            # Normalize room spacing
            room = re.sub(r"([A-Z])\s+(\d+)", r"\1  \2", room)

            item = f"{day} / {periods} / {room}"

        normalized.append(item)

    return normalized

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
    if os.path.exists(".userData/"+fileName):
        with open(".userData/"+fileName, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data

def save_storage_data(fileName:str,data):
    if not os.path.exists(".userData"):
        os.mkdir(".userData")
    
    with open(".userData/"+fileName, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def show_native_error_dialog(message):
    # Clean env so subprocesses use system libraries instead of PyInstaller's bundled libssl/libssh
    clean_env = os.environ.copy()
    clean_env.pop("LD_LIBRARY_PATH", None)

    # 1. Try zenity
    try:
        subprocess.run([
            "zenity", "--error", 
            "--title=Dependency Missing", 
            f"--text={message}"
        ], check=True, env=clean_env)
        return
    except Exception:
        pass

    # 2. Try kdialog
    try:
        subprocess.run([
            "kdialog", "--error", message, 
            "--title", "Dependency Missing"
        ], check=True, env=clean_env)
        return
    except Exception:
        pass


if __name__ == '__main__':
    api = UI_Api()
    webview.create_window('TKU EMI Suckless', 'gui/index.html', js_api=api)
    try:
        webview.start()
    except Exception as e:
        if platform.system() == "Linux":
            show_native_error_dialog(
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
