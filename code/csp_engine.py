import random
import copy

class CSPScheduler:
    def __init__(self, course_list, rooms, comp_labs, digital_lab, english_labs):
        self.course_list = course_list
        self.rooms = rooms
        self.comp_labs = comp_labs
        self.digital_lab = digital_lab
        self.english_labs = english_labs
        
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.theory_slots = ["08:30-09:50", "10:00-11:20", "11:30-12:50", "01:00-02:20", "02:30-03:50", "04:00-05:15"]
        self.lab_slots = ["08:30-11:15", "11:30-02:15", "02:30-05:15"]

    def get_correct_room_pool(self, course):
        if not course.is_lab: return self.rooms
        name = course.name.upper()
        if "DIGITAL LOGIC DESIGN" in name: return self.digital_lab
        elif any(word in name for word in ["EXPO", "ENGLISH", "FSM", "COMMUNICATION"]): return self.english_labs
        return self.comp_labs

    def is_consistent(self, assignment, current_entry):
        """
        Hard Constraint Checker (No overlaps for Room, Instructor, or Section)
        """
        c1 = current_entry['course']
        r1, d1, s1 = current_entry['room'], current_entry['day'], current_entry['slot']
        is_lab1 = current_entry['is_lab']

        # Get sub-slots for lab/theory overlap checking
        def get_blocked(slot, is_lab):
            if not is_lab: return [slot]
            if slot == "08:30-11:15": return ["08:30-09:50", "10:00-11:20"]
            if slot == "11:30-02:15": return ["11:30-12:50", "01:00-02:20"]
            return ["02:30-03:50", "04:00-05:15"]

        blocked1 = get_blocked(s1, is_lab1)

        for existing in assignment:
            c2 = existing['course']
            r2, d2, s2 = existing['room'], existing['day'], existing['slot']
            blocked2 = get_blocked(s2, existing['is_lab'])

            if d1 == d2:
                # Check if any sub-slots overlap
                if any(b in blocked2 for b in blocked1):
                    # Hard Constraints: Room, Instructor, and Section Clashes
                    if r1 == r2: return False
                    if c1.instructor == c2.instructor: return False
                    if c1.section == c2.section: return False
        return True

    def backtrack(self, assignment, course_index, session_index):
        """
        Recursive Backtracking Search (The core CSP Technique)
        """
        # Success condition: All courses and their sessions are assigned
        if course_index == len(self.course_list):
            return assignment

        course = self.course_list[course_index]
        room_pool = self.get_correct_room_pool(course)
        slots = self.lab_slots if course.is_lab else self.theory_slots

        # Try all possible combinations (Domain) for the current variable
        # To mimic CSP 'Pruning', we exit the loop early if a branch fails
        for d in self.days:
            for s in slots:
                for r in room_pool:
                    new_entry = {
                        'course': course, 'room': r, 'day': d, 
                        'slot': s, 'is_lab': course.is_lab
                    }

                    if self.is_consistent(assignment, new_entry):
                        assignment.append(new_entry)
                        
                        # Move to next session or next course
                        next_c, next_s = (course_index, session_index + 1) if session_index + 1 < course.sessions_per_week else (course_index + 1, 0)
                        
                        result = self.backtrack(assignment, next_c, next_s)
                        if result is not None: return result
                        
                        # Backtrack: Undo choice
                        assignment.pop()
        
        return None # Trigger backtracking to previous level

    def solve(self):
        return self.backtrack([], 0, 0)