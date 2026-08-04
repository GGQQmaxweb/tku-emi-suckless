import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

class EMISStudentAPI:
    Group_TableOfField = {
    "Scientific Fields": {
        "U": "自然科學",
        "Z": "全球科技革命",
    },
    "Social Fields": {
        "N": "學習與發展",
        "S": "公民社會及參與",
        "T": "全球視野",
        "W": "社會分析",
        "R": "未來學",
    },
    "Humanities Fields": {
        "L": "文學經典",
        "M": "藝術欣賞與創作",
        "P": "歷史與文化",
        "V": "哲學與宗教",
    },
    "General Education": {
        "K": "課外活動與團隊發展",
    },
    "Language": {
        "Q": "外語",
    }
}

    def __init__(self, session):
        self.session = session
        #basic info set up
        try:
            url = "https://sso.tku.edu.tw/aissinfo/emis/TMWS080.aspx"
            html = self.session.get(url).text
            soup = BeautifulSoup(html, 'html.parser')
            self.student_id = soup.find(id="Label2").text.split("：")[1].strip()
            self.student_name = soup.find(id="Label3").text.split("：")[1].strip()
            self.student_grade = soup.find(id="Label1").text.split("：")[1].strip()

            parsed = parse_grade_field(self.student_grade)
            self.student_department = parsed['department']
            self.student_year = parsed['year']      # this is the grade/year part
            self.student_class_ = parsed['class']            # use class_ to avoid clashing with keyword

            if self.student_id == None or self.student_name == None or self.student_grade == None:
                raise RuntimeError("Not login")

        except:
                pass

    def whatClassWeHaveThisSemester(self):
        url = "https://raw.githubusercontent.com/tkuitocc/azquerysucks/main/courses.json"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                raise RuntimeError(f"Failed to fetch data. Status code: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"An error occurred while fetching data: {e}")
    
    def __extract_sub_notes(self, td):
        """
        從第三欄 td 中：
        - 把 sub-table 的 (1)(2)(3) 拆成 list
        - 同時保留純文字 note
        """
        notes = []

        # Find sub-table
        sub_table = td.find("table")
        if sub_table:
            for tr in sub_table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    notes.append(" ".join(tds[1].stripped_strings))

            # 移除 sub-table，避免重複
            sub_table.decompose()

        # 剩下的純文字
        text = " ".join(td.stripped_strings)
        if text:
            notes.insert(0, text)

        return notes

    def __baseRequest(self, url):
        try:
            response = self.session.get(url)

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the table (first table on page)
            table = soup.find("table")
            if not table:
                raise RuntimeError("Table not found")

            rows = table.find_all("tr")
            return rows, soup

        except:
                pass

    def __getNextYrSem(self):
        # 取得目前日期
        now = datetime.now()
        year = now.year
        month = now.month

        # 計算 ROC 年
        roc_year = year - 1911

        # 6月 到 11月 為第 1 學期
        if 6 <= month <= 11:
            semester = 1
            school_year = roc_year

        # 12月 為第 2 學期（尚未跨西元年）
        elif month == 12:
            semester = 2
            school_year = roc_year

        # 1月 到 5月 為第 2 學期（已跨西元年，學年減 1）
        else:
            semester = 2
            school_year = roc_year - 1

        return f"{school_year}{semester}"

    def __getCurrentYrSem(self):
        now = datetime.now()
        year = now.year
        month = now.month

        # ROC year
        roc_year = year - 1911

        # 6 ~ 11 : first semester
        if 6 <= month <= 11:
            semester = 1
            school_year = roc_year

        # 12 : second semester (same school year)
        elif month == 12:
            semester = 2
            school_year = roc_year

        # 1 ~ 5 : second semester (next school year)
        else:
            semester = 2
            school_year = roc_year - 1

        return f"{school_year}{semester}"

    def __clean_text(self,el):
        """取得 element 的可讀文字（包含巢狀 table）"""
        if not el:
            return ""
        return " ".join(el.stripped_strings)

    def get_student_info(self):
        return {"id":self.student_id,"grade":self.student_grade,"name":self.student_name,"department_":self.student_department,"year_":self.student_year,"class_":self.student_class_}

    # 查詢學生基本資料
    def get_student_basic_info(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWS020.aspx"
        #too detail don't use it
        raise Exception("Do not support: Too detail don't use it on api")
        pass

    # 查詢修業相關資訊
    def get_study_progress_info(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWS080.aspx"
        rows = self.__baseRequest(url)
        data = []
        for row in rows[1:]:  # skip header
            tds = row.find_all("td", recursive=False)
            if len(tds) < 2:
                continue

            item = " ".join(tds[0].stripped_strings)
            value = " ".join(tds[1].stripped_strings)

            notes = []
            if len(tds) >= 3:
                notes = self.__extract_sub_notes(tds[2])

            data.append({
                "item": item,
                "value": value,
                "note": notes
            })
        return data


    # 查詢必修科目及畢業學分
    def get_required_courses_and_graduation_credits(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWC120.aspx"
        rows,soup = self.__baseRequest(url)
        data = []
        soup
        COLUMNS = [
            "grade",
            "course_name",
            "course_code",
            "specialization",
            "group",
            "credits_up",
            "credits_down",
            "note",
        ]
        rows = soup.select("table tr")[3:]  # skip header rows

        data = []
        text = soup.find("font", color="red").get_text(strip=True)
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\u3000", " ")
        pattern = re.compile(
            r"畢業審核學年度：(?P<year>\d+)\s+"
            r"專業科目組別：(?P<group>.*?)\s+"
            r"畢業學分數：(?P<total>\d+)\s+"
            r"必修學分數：(?P<required>\d+)\s+"
            r"本系選修課最低學分：(?P<elective>\d+)"
        )

        m = pattern.search(text)

        for tr in rows:
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(tds) != 8:
                continue  # skip malformed rows

            row = dict(zip(COLUMNS, tds))
            data.append(row)

        result = {
            "audit_year": int(m.group("year")),
            "specialization_group": m.group("group") or None,
            "credits": {
                "total": int(m.group("total")),
                "required": int(m.group("required")),
                "elective_min": int(m.group("elective")),
                },
            "courses":data,
            }

        return result


    # 查詢歷年各科成績
    def get_all_years_course_grades(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWS100.aspx"
        rows, soup = self.__baseRequest(url)
        course_table = soup.find("table", border="1")
        rows = course_table.find_all("tr")
        credit_b = soup.find(
            "b",
            string=re.compile(r"累計實得學分")
        )

        summary_text = credit_b.get_text(strip=True)
        total_credits = int(summary_text.split("：")[1])

        data = []

        for tr in rows[1:]:
            tds = tr.find_all("td")
            if len(tds) != 11:
                continue

            specialization = tds[3].get_text(strip=True)
            course_code = tds[4].get_text(strip=True)
            course_name = tds[5].get_text(separator="\n").split("\n")[0].strip()
            group = tds[7].get_text(strip=True)
            credits = int(tds[9].get_text(strip=True))
            raw_grade = tds[10].get_text(strip=True)

            # 必修 / 選修 (Chinese only)
            requirement_type = tds[8].get_text(strip=True).split()[0]

            grade, credits_up, credits_down, status = \
                parse_grade_and_credits(raw_grade, credits)

            row = {
                "grade": grade,
                "course_name": course_name,
                "course_code": course_code,
                "specialization": specialization,
                "group": group,
                "credits_up": credits_up,
                "credits_down": credits_down,
                "requirement_type": requirement_type,
                "status": status,
            }

            data.append(row)
        result = {
            "total_earned_credits":total_credits,
            "courses":data,
        }
        return result

    def get_missing_required_courses(self,debug=False):
        """
        Returns a list of required courses that have not been passed yet.
        A course is treated as satisfied when either:
        1. the exact same course code was passed, or
        2. a passed course belongs to the same field group defined in Group_TableOfField.
        """
        # Just a exmaple code

        all_grades = self.get_all_years_course_grades()['courses']
        required_courses = self.get_required_courses_and_graduation_credits()['courses']
        

        if debug:
            print (f"All grades: {all_grades}")
            print (f"Required courses: {required_courses}")

        def resolve_field_group(group_value):
            if not group_value:
                return None

            group_value = str(group_value).strip()
            for field_name, field_codes in self.Group_TableOfField.items():
                if (
                    group_value in field_codes
                    or group_value in field_codes.values()
                    or group_value == field_name
                ):
                    return field_name
            return None

        passed_courses = set()
        passed_field_groups = set()

        for c in all_grades:
            status = str(c.get('status', '')).lower()
            grade = c.get('grade')
            is_pass = status in {"pass", "passed"}

            if not is_pass:
                try:
                    if int(grade) >= 60:
                        is_pass = True
                except (TypeError, ValueError):
                    pass

            if is_pass:
                course_code = c.get('course_code')
                if course_code:
                    passed_courses.add(course_code)

                field_group = resolve_field_group(c.get('group'))
                if field_group:
                    passed_field_groups.add(field_group)

        missing_courses = []
        for c in required_courses:
            course_code = c.get('course_code')
            if course_code in passed_courses:
                continue

            required_group = resolve_field_group(c.get('group'))
            if required_group and required_group in passed_field_groups:
                continue

            missing_courses.append(c)

        return missing_courses


    # 查詢各學期成績
    def get_semester_grades(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWS030.aspx"
        pass

    # 查詢課程資料(含歷年)
    def get_course_data_all_years(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWC010_result.aspx?YrSem=1142&TeachNo=&Kind=1&Grade=0&TeachName=&ChCosName=&Week=*&SessStr=*&SessEnd=*"
        pass

    # 查詢選課資料(依科目代號排列)
    def get_course_selection_by_course_code(self,en=False):
        YrSem = self.__getCurrentYrSem()

        mainUrl = "https://sso.tku.edu.tw/aissinfo/emis/TMWC020.aspx"
        searchUrl = f"https://sso.tku.edu.tw/aissinfo/emis/TMWC020_result.aspx?YrSem={YrSem}"
        if en:
            mainUrl = "https://sso.tku.edu.tw/aissinfo/emis/eTMWC020.aspx" #yes it like this
            searchUrl = f"https://sso.tku.edu.tw/aissinfo/emis/eTMWC020_result.aspx?YrSem={YrSem}"
        get_resp = self.session.get(mainUrl)
        soup = BeautifulSoup(get_resp.text, "html.parser")

        # Extract hidden form fields
        viewstate = soup.find("input", {"id": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"id": "__EVENTVALIDATION"})["value"]
        viewstategenerator = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})["value"]

        # Step 2: Prepare POST data
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "DropDownList1": YrSem,
            "Button1": "開始查詢",
        }

        # Step 3: POST the form
        post_resp = self.session.post(mainUrl, data=data)

        # Step 4 Start the dam requests
        rows, soup = self.__baseRequest(searchUrl)

        table = soup.find("table", {"id": "DataGrid1"})
        rows = table.find_all("tr")

        courses = []
        current = None

        # skip header row
        for tr in rows[1:]:
            tds = [td.get_text(strip=True).replace("\u3000", " ") for td in tr.find_all("td")]

            # start of a new course
            if tds and tds[0]:
                if current:
                    # deduplicate lists
                    current["teachers"] = list(dict.fromkeys(current["teachers"]))
                    current["schedule"] = list(dict.fromkeys(current["schedule"]))
                    current["seat_numbers"] = list(dict.fromkeys(current["seat_numbers"]))
                    courses.append(current)

                course_name, course_code = None, None
                if tds[3]:
                    parts = tds[3].split()
                    course_name = parts[0]
                    course_code = parts[-1]

                current = {
                    "course_id": tds[0],
                    "dept": tds[1],
                    "grade": tds[2],
                    "course_name": course_name,
                    "course_code": course_code,
                    "credits": tds[8],
                    "required": tds[7],
                    "teachers": [],
                    "schedule": [],
                    "seat_numbers": []
                }

            # continuation rows or additional info
            if current:
                teacher = tds[10] if len(tds) > 10 else ""
                time = tds[11] if len(tds) > 11 else ""
                seat = tds[12] if len(tds) > 12 else ""

                if teacher:
                    current["teachers"].append(teacher)
                if time:
                    current["schedule"].append(time)
                if seat:
                    current["seat_numbers"]=seat

        # append last course
        if current:
            current["teachers"] = list(dict.fromkeys(current["teachers"]))
            current["schedule"] = list(dict.fromkeys(current["schedule"]))
            current["seat_numbers"] = list(dict.fromkeys(current["seat_numbers"]))
            courses.append(current)
        return courses
    def get_course_selection_by_course_codeAsIlifeAPI(self):
        courses = self.get_course_selection_by_course_code()



        pass
    # 查詢選課/考試資料(依上課星期、節次列表)
    def get_course_and_exam_schedule(self, YrSem, stu_no):
        url = f"https://sso.tku.edu.tw/aissinfo/emis/TMWC090_result.aspx?YrSem={YrSem}"
        pass

    # 查詢考試資料
    def get_exam_info(self):
        #N/A
        pass

    # 查詢考試小表
    def get_exam_summary_table(self):
        #N/A
        pass

    # 查詢扣考資料
    def get_exam_disqualification_info(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWC071.aspx"
        pass

    # 查詢本學期期中成績
    def get_current_semester_midterm_grades(self):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWC071.aspx"
        pass

    # 查詢本學期學期成績
    def get_current_semester_final_grades(self):

        pass

    # 畢業班缺修學分資訊查詢
    def get_graduating_student_missing_credits(self, debug=False):
        url = "https://sso.tku.edu.tw/aissinfo/emis/TMWS040.htm" #yea htm very nice and yes only for graduating students
        pass

    def whatTimeNow(self):
        self.__getCurrentYrSem()
        return f"Current Year Semester: {self.__getCurrentYrSem()}"
        


def parse_grade_and_credits(raw_grade, credits):
    raw_grade = raw_grade.strip()

    if raw_grade == "通過":
        return "pass", credits, credits, "pass"

    if raw_grade.startswith("*"):
        return int(raw_grade[1:]), 0, credits, "failed"

    score = int(raw_grade)
    if score >= 60:
        return score, credits, credits, "passed"
    else:
        return score, 0, credits, "failed"

def parse_grade_field(grade_str):
    """
    Parse a string like '資管三Ｃ' into department, year, and class.
    Returns a dict: {'department': ..., 'year': ..., 'class': ...}
    """
    # Match: 1+ Chinese chars (department) + 1 Chinese numeral (year) + optional letter (class)
    match = re.match(r"([\u4e00-\u9fff]+)([一二三四五六七八九十]+)([A-Z]?)", grade_str)
    if match:
        department, year, class_letter = match.groups()
        return {
            'department': department,
            'year': year,
            'class': class_letter or None
        }
    else:
        # fallback if format unexpected
        return {
            'department': None,
            'year': None,
            'class': None
        }
    
