import random
import math
import copy

class SAScheduler:
    def __init__(self, course_list, rooms, comp_labs, digital_lab, english_labs, initial_temp=100.0, cooling_rate=0.95):
        self.course_list = course_list
        self.rooms = rooms
        self.comp_labs = comp_labs
        self.digital_lab = digital_lab
        self.english_labs = english_labs
        
        # SA Hyperparameters
        self.temp = initial_temp
        self.cooling_rate = cooling_rate
        
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.theory_slots = ["08:30-09:50", "10:00-11:20", "11:30-12:50", "01:00-02:20", "02:30-03:50", "04:00-05:15"]
        self.lab_slots = ["08:30-11:15", "11:30-02:15", "02:30-05:15"]

    def get_correct_room_pool(self, course):
        if not course.is_lab: return self.rooms
        name = course.name.upper()
        if "DIGITAL LOGIC DESIGN" in name: return self.digital_lab
        elif any(word in name for word in ["EXPO", "ENGLISH", "FSM", "COMMUNICATION"]): return self.english_labs
        return self.comp_labs

    def calculate_conflicts(self, schedule):
        """
        Energy Function: Measures the 'heat' or badness of a schedule.
        Goal: Minimize this value.
        """
        hard_conflicts = 0
        instructor_busy = {}
        room_busy = {}
        section_busy = {}

        for entry in schedule:
            c, r, d, s, is_lab = entry['course'], entry['room'], entry['day'], entry['slot'], entry['is_lab']
            
            # Map slots to sub-slots for overlap checking
            blocked = [s]
            if is_lab:
                if s == "08:30-11:15": blocked = ["08:30-09:50", "10:00-11:20"]
                elif s == "11:30-02:15": blocked = ["11:30-12:50", "01:00-02:20"]
                elif s == "02:30-05:15": blocked = ["02:30-03:50", "04:00-05:15"]

            for b_slot in blocked:
                # Conflict checks
                for key in [(c.instructor, d, b_slot), (r, d, b_slot), (c.section, d, b_slot)]:
                    if key in instructor_busy or key in room_busy or key in section_busy:
                        hard_conflicts += 1
                instructor_busy[(c.instructor, d, b_slot)] = True
                room_busy[(r, d, b_slot)] = True
                section_busy[(c.section, d, b_slot)] = True
        
        return hard_conflicts

    def generate_neighbor(self, current_schedule):
        """
        Perturbation Step: Randomly change one class assignment.
        """
        neighbor = copy.deepcopy(current_schedule)
        idx = random.randint(0, len(neighbor) - 1)
        
        # Randomly change either Room, Day, or Slot
        choice = random.choice(['room', 'day', 'slot'])
        course = neighbor[idx]['course']
        
        if choice == 'room':
            neighbor[idx]['room'] = random.choice(self.get_correct_room_pool(course))
        elif choice == 'day':
            neighbor[idx]['day'] = random.choice(self.days)
        else:
            slots = self.lab_slots if course.is_lab else self.theory_slots
            neighbor[idx]['slot'] = random.choice(slots)
            
        return neighbor

    def solve(self, iterations=1000):
        # 1. Start with a random initial state (Trajectory Start)
        current_schedule = []
        for course in self.course_list:
            for _ in range(course.sessions_per_week):
                current_schedule.append({
                    'course': course, 'day': random.choice(self.days),
                    'room': random.choice(self.get_correct_room_pool(course)),
                    'slot': random.choice(self.lab_slots if course.is_lab else self.theory_slots),
                    'is_lab': course.is_lab
                })

        current_energy = self.calculate_conflicts(current_schedule)
        best_schedule = current_schedule
        best_energy = current_energy

        for i in range(iterations):
            # 2. Temperature Check
            if current_energy == 0 or self.temp < 0.01:
                break

            # 3. Explore Neighbor
            neighbor = self.generate_neighbor(current_schedule)
            neighbor_energy = self.calculate_conflicts(neighbor)
            
            # 4. Acceptance Probability
            energy_diff = neighbor_energy - current_energy
            
            # If neighbor is better, always accept . 
            # If worse, accept with a probability that decreases as temperature cools.
            if energy_diff < 0 or random.random() < math.exp(-energy_diff / self.temp):
                current_schedule = neighbor
                current_energy = neighbor_energy
                
                if current_energy < best_energy:
                    best_schedule = current_schedule
                    best_energy = current_energy

            # 5. Cool Down
            self.temp *= self.cooling_rate

        return best_schedule, best_energy
