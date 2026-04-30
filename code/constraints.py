import collections

class ConstraintEvaluator:
    def __init__(self, course_list, rooms, theory_slots, lab_slots, mirror_days, whard=1.0, wsoft=0.1):
        self.course_list = course_list
        self.rooms = rooms
        self.theory_slots = theory_slots
        self.lab_slots = lab_slots
        self.mirror_days = mirror_days
        self.whard = whard
        self.wsoft = wsoft
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.slot_index = {s: i for i, s in enumerate(self.theory_slots)}
        self.section_credit_hours = collections.Counter()

        for course in self.course_list:
            if not self.is_fyp(course):
                self.section_credit_hours[course.section] += course.ch

    def is_fyp(self, course):
        return "FYP" in course.name.upper()

    def blocked_slots(self, slot, is_lab):
        if not is_lab:
            return [slot]
        if slot == "08:30-11:15":
            return ["08:30-09:50", "10:00-11:20"]
        if slot == "11:30-02:15":
            return ["11:30-12:50", "01:00-02:20"]
        return ["02:30-03:50", "04:00-05:15"]

    def get_room_geo(self, room_name):
        try:
            num = int(room_name.split()[-1])
            if 1 <= num <= 10:
                return "C", 3
            if 11 <= num <= 20:
                return "C", 4
            if 21 <= num <= 35:
                return "D", 3
            if 36 <= num <= 50:
                return "D", 4
        except Exception:
            return "X", 0
        return "X", 0

    def evaluate(self, schedule):
        hard_conflicts = 0
        soft_penalty = 0
        violations = []

        ins_busy = {}
        room_busy = {}
        section_busy = {}

        course_sessions = collections.Counter()
        course_day_counts = collections.Counter()
        section_day_slots = collections.defaultdict(list)
        instructor_day_slots = collections.defaultdict(list)

        for entry in schedule:
            c = entry['course']
            day = entry['day']
            slot = entry['slot']
            room = entry['room']
            is_lab = entry['is_lab']
            key = (c.code, c.section)

            course_sessions[key] += 1
            course_day_counts[(key, day)] += 1

            blocked = self.blocked_slots(slot, is_lab)
            for b in blocked:
                if (c.instructor, day, b) in ins_busy:
                    hard_conflicts += 1
                    violations.append(f"Instructor overlap: {c.instructor} {day} {b}")
                if (room, day, b) in room_busy:
                    hard_conflicts += 1
                    violations.append(f"Room conflict: {room} {day} {b}")
                if (c.section, day, b) in section_busy:
                    hard_conflicts += 1
                    violations.append(f"Section overlap: {c.section} {day} {b}")
                ins_busy[(c.instructor, day, b)] = True
                room_busy[(room, day, b)] = True
                section_busy[(c.section, day, b)] = True

                if b in self.slot_index:
                    idx = self.slot_index[b]
                    section_day_slots[(c.section, day)].append((idx, room))
                    instructor_day_slots[(c.instructor, day)].append(idx)

        # Hard: credit-hour integrity
        for course in self.course_list:
            key = (course.code, course.section)
            expected = course.sessions_per_week
            actual = course_sessions.get(key, 0)

            if actual != expected:
                hard_conflicts += 1
                violations.append(
                    f"Credit-hour integrity failed: {course.code} {course.section} expected {expected}, got {actual}"
                )

            if course.sessions_per_week == 2 and not course.is_lab:
                entries = [e for e in schedule if e['course'] == course]
                if len(entries) != 2:
                    hard_conflicts += 1
                    violations.append(f"3CH credit-hour integrity failed: {course.code} {course.section}")

        # Soft: room persistence and consecutive load checks
        for (section, day), classes in section_day_slots.items():
            classes.sort()
            consecutive_streak = 1
            max_streak = 1

            for i in range(len(classes) - 1):
                curr_s, curr_r = classes[i]
                next_s, next_r = classes[i + 1]
                if next_s == curr_s + 1:
                    consecutive_streak += 1
                    if curr_r != next_r:
                        soft_penalty += 10
                        b1, f1 = self.get_room_geo(curr_r)
                        b2, f2 = self.get_room_geo(next_r)
                        if b1 != b2 or f1 != f2:
                            soft_penalty += 15
                else:
                    consecutive_streak = 1
                max_streak = max(max_streak, consecutive_streak)

            if max_streak > 3:
                soft_penalty += (max_streak - 3) * 10

        # Soft: instructor load balancing
        for (instructor, day), slots in instructor_day_slots.items():
            slots = sorted(set(slots))
            streak = 1
            max_streak = 1
            for i in range(len(slots) - 1):
                if slots[i + 1] == slots[i] + 1:
                    streak += 1
                else:
                    streak = 1
                max_streak = max(max_streak, streak)
            if max_streak > 3:
                soft_penalty += (max_streak - 3) * 10

        # Soft: 12-CH (4 sessions) rule, only Mon/Wed or Tue/Thu
        section_total_sessions = collections.Counter()
        section_day_counts = collections.defaultdict(collections.Counter)
        for entry in schedule:
            if self.is_fyp(entry['course']):
                continue
            section_total_sessions[entry['course'].section] += 1
            section_day_counts[entry['course'].section][entry['day']] += 1

        for section, total_sessions in section_total_sessions.items():
            if total_sessions == 4:
                days_used = set(section_day_counts[section].keys())
                if days_used not in [{"Monday", "Wednesday"}, {"Tuesday", "Thursday"}]:
                    soft_penalty += 25
                if len(days_used) != 2:
                    soft_penalty += 25
                if any(count != 2 for count in section_day_counts[section].values()):
                    soft_penalty += 25

        # Soft: 12-CH (non-FYP) sections should be on two days only
        for section, ch_total in self.section_credit_hours.items():
            if ch_total == 12:
                days_used = set(section_day_counts[section].keys())
                if days_used not in [{"Monday", "Wednesday"}, {"Tuesday", "Thursday"}]:
                    soft_penalty += 25
                if len(days_used) != 2:
                    soft_penalty += 25

        # Soft: teacher preference if available
        for entry in schedule:
            course = entry['course']
            preferred = getattr(course, 'preferred_slots', None)
            if preferred and entry['slot'] not in preferred:
                soft_penalty += 5

        total_cost = (hard_conflicts * self.whard) + (soft_penalty * self.wsoft)
        return {
            'hard_conflicts': hard_conflicts,
            'soft_penalty': soft_penalty,
            'total_cost': total_cost,
            'violations': violations
        }

    def is_valid(self, schedule):
        return self.evaluate(schedule)['hard_conflicts'] == 0
