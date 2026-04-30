import pandas as pd

class CourseSection:
    def __init__(self, code, name, ch, section, instructor, category):
        self.code = str(code)
        self.name = str(name)
        self.ch = int(ch)
        self.section = str(section)
        self.instructor = str(instructor)
        self.category = category  # e.g., 'Computing Theory', 'Lab', 'MG', 'S&H'
        self.preferred_slots = []
        
        # Domain Adaptation: Credit Hour Logic
        # 1 credit = Lab (2:45), 2 credit = 1 session (1:45), 3 credit = 2 sessions (1:20)
        if "FYP" in self.name.upper():
            self.sessions_per_week = 0
            self.duration_minutes = 0
            self.is_lab = False
        elif self.ch == 1:
            self.sessions_per_week = 1
            self.duration_minutes = 165
            self.is_lab = True
        elif self.ch == 2:
            self.sessions_per_week = 1
            self.duration_minutes = 105
            self.is_lab = False
        else: # 3 Credits
            self.sessions_per_week = 2
            self.duration_minutes = 80
            self.is_lab = False

    def __repr__(self):
        return f"{self.code} - {self.section} ({self.instructor})"