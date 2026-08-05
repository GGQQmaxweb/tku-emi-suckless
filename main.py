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

AUTH = False
API = False


class UI_Api:
    
    def auth_login(self):
        username = ""
        password = ""
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            username = data["username"]
            password = data["password"]
        try:
            AUTH = Authenticator(username=username,password=password)
        except:
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
        # Replace this with your database or API authentication check
        AUTH = Authenticator(username=username,password=password)
       
        
        if AUTH.perform_auth() != False:
            
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

if __name__ == '__main__':
    api = UI_Api()
    webview.create_window('TKU EMI Suckless', 'gui/index.html', js_api=api)
    try:
        webview.start()
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
