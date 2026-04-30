import random
import copy
from constraints import ConstraintEvaluator

class GeneticScheduler:
    def __init__(self, course_list, rooms, comp_labs, digital_lab, english_labs, pop_size=100):
        self.course_list = course_list
        self.rooms = rooms
        self.comp_labs = comp_labs
        self.digital_lab = digital_lab
        self.english_labs = english_labs
        self.pop_size = pop_size
        self.fitness_cache = {}
        self.fitness_cache_limit = 10000
        
        self.mirror_days = {"Monday": "Wednesday", "Tuesday": "Thursday"}
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        self.theory_slots = ["08:30-09:50", "10:00-11:20", "11:30-12:50", "01:00-02:20", "02:30-03:50", "04:00-05:15"]
        self.lab_slots = ["08:30-11:15", "11:30-02:15", "02:30-05:15"]

        self.evaluator = ConstraintEvaluator(
            self.course_list,
            self.rooms,
            self.theory_slots,
            self.lab_slots,
            self.mirror_days
        )

    def schedule_signature(self, schedule):
        # Order-independent signature for caching fitness scores
        items = []
        for entry in schedule:
            c = entry['course']
            items.append((c.code, c.section, entry['day'], entry['slot'], entry['room'], entry['is_lab']))
        return tuple(sorted(items))

    def is_fyp(self, course):
        return "FYP" in course.name.upper()

    def get_correct_room_pool(self, course):
        if not course.is_lab:
            return self.rooms
        name = course.name.upper()
        if "DIGITAL LOGIC DESIGN" in name or "DIGITAL" in name:
            return self.digital_lab
        if any(word in name for word in ["EXPO", "ENGLISH", "FSM", "COMMUNICATION"]):
            return self.english_labs
        return self.comp_labs

    def get_room_geo(self, room_name):
        try:
            num = int(room_name.split()[-1])
            if 1 <= num <= 10: return "C", 3
            if 11 <= num <= 20: return "C", 4
            if 21 <= num <= 35: return "D", 3
            if 36 <= num <= 50: return "D", 4
        except: pass
        return "X", 0

    def blocked_slots(self, slot, is_lab):
        if not is_lab:
            return [slot]
        if slot == "08:30-11:15":
            return ["08:30-09:50", "10:00-11:20"]
        if slot == "11:30-02:15":
            return ["11:30-12:50", "01:00-02:20"]
        return ["02:30-03:50", "04:00-05:15"]

    def has_hard_conflict(self, schedule, entry):
        c1 = entry['course']
        r1, d1, s1 = entry['room'], entry['day'], entry['slot']
        blocked1 = self.blocked_slots(s1, entry['is_lab'])

        for existing in schedule:
            c2 = existing['course']
            r2, d2, s2 = existing['room'], existing['day'], existing['slot']
            if d1 != d2:
                continue
            blocked2 = self.blocked_slots(s2, existing['is_lab'])
            if any(b in blocked2 for b in blocked1):
                if r1 == r2:
                    return True
                if c1.instructor == c2.instructor:
                    return True
                if c1.section == c2.section:
                    return True
        return False

    def generate_random_schedule(self):
        """Mandatory: Every course in course_list is assigned to ensure credit hours are met."""
        schedule = []
        for course in self.course_list:
            if course.sessions_per_week == 0:
                continue
            room_pool = self.get_correct_room_pool(course)
            selected_room = random.choice(room_pool)
            valid_days = ["Friday"] if self.is_fyp(course) else self.days[:4]

            # MANDATORY 48-HOUR RULE: Linked Gene Construction
            if course.sessions_per_week == 2 and not course.is_lab:
                placed = False
                for _ in range(40):
                    day1 = random.choice(["Monday", "Tuesday"])
                    day2 = self.mirror_days[day1]
                    slot = random.choice(self.theory_slots)
                    selected_room = random.choice(room_pool)
                    e1 = {'course': course, 'room': selected_room, 'day': day1, 'slot': slot, 'is_lab': False}
                    e2 = {'course': course, 'room': selected_room, 'day': day2, 'slot': slot, 'is_lab': False}
                    if not self.has_hard_conflict(schedule, e1) and not self.has_hard_conflict(schedule, e2):
                        schedule.extend([e1, e2])
                        placed = True
                        break
                if not placed:
                    schedule.append({'course': course, 'room': selected_room, 'day': day1, 'slot': slot, 'is_lab': False})
                    schedule.append({'course': course, 'room': selected_room, 'day': day2, 'slot': slot, 'is_lab': False})
            else:
                for _ in range(course.sessions_per_week):
                    placed = False
                    for _ in range(40):
                        entry = {
                            'course': course,
                            'room': random.choice(room_pool),
                            'day': random.choice(valid_days),
                            'slot': random.choice(self.lab_slots if course.is_lab else self.theory_slots),
                            'is_lab': course.is_lab
                        }
                        if not self.has_hard_conflict(schedule, entry):
                            schedule.append(entry)
                            placed = True
                            break
                    if not placed:
                        schedule.append({
                            'course': course,
                            'room': selected_room,
                            'day': random.choice(valid_days),
                            'slot': random.choice(self.lab_slots if course.is_lab else self.theory_slots),
                            'is_lab': course.is_lab
                        })
        return schedule

    def calculate_fitness(self, schedule):
        sig = self.schedule_signature(schedule)
        cached = self.fitness_cache.get(sig)
        if cached is not None:
            return cached
        result = self.evaluator.evaluate(schedule)
        # Fitness Calculation: Hard conflicts must be 0 for high fitness
        fitness = 1 / (1 + result['total_cost'])
        if len(self.fitness_cache) >= self.fitness_cache_limit:
            self.fitness_cache.clear()
        self.fitness_cache[sig] = fitness
        return fitness

    def mutate(self, schedule):
        """Mutate while preserving mirroring and room persistence"""
        child = copy.deepcopy(schedule)
        idx = random.randint(0, len(child)-1)
        target = child[idx]['course']

        new_room = random.choice(self.get_correct_room_pool(target))
        new_slot = random.choice(self.theory_slots if not target.is_lab else self.lab_slots)
        new_day1 = "Friday" if self.is_fyp(target) else random.choice(["Monday", "Tuesday"])

        session_idx = 0
        for entry in child:
            if entry['course'] == target:
                entry['room'] = new_room
                if target.sessions_per_week == 2 and not entry['is_lab']:
                    entry['day'] = new_day1 if session_idx == 0 else self.mirror_days[new_day1]
                    entry['slot'] = new_slot
                    session_idx += 1
                else:
                    entry['day'] = "Friday" if self.is_fyp(target) else random.choice(self.days[:4])
                    entry['slot'] = new_slot
        return child

    def evolve(self, generations=100, stagnation_limit=20):
        population = [self.generate_random_schedule() for _ in range(self.pop_size)]
        best_fitness = None
        stagnation = 0

        for gen in range(generations):
            scored = [(self.calculate_fitness(s), s) for s in population]
            scored.sort(key=lambda x: x[0], reverse=True)
            population = [s for _, s in scored]
            current_best = population[0]
            current_best_fitness = scored[0][0]

            if best_fitness is None or current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                stagnation = 0
            else:
                stagnation += 1
            
            # Break if we find a valid (0 hard conflict) and well-optimized schedule
            if self.evaluator.is_valid(current_best):
                break
            if stagnation_limit is not None and stagnation >= stagnation_limit:
                break

            new_pop = population[:15] # Elitism
            while len(new_pop) < self.pop_size:
                p1, p2 = random.sample(population[:30], 2)
                # Course-level crossover to keep sessions together
                split = random.randint(0, len(p1)-1)
                child = p1[:split] + p2[split:]
                if random.random() < 0.4: child = self.mutate(child)
                new_pop.append(child)
            population = new_pop
            
        return sorted(population, key=lambda x: self.calculate_fitness(x), reverse=True)[0]