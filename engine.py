import random
import copy

class GeneticScheduler:
    def __init__(self, course_list, rooms, comp_labs, digital_lab, english_labs, pop_size=50):
        self.course_list = course_list
        self.rooms = rooms
        self.comp_labs = comp_labs
        self.digital_lab = digital_lab
        self.english_labs = english_labs
        self.pop_size = pop_size
        
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        # Theory Slots (1:20h with 10m gap)
        self.theory_slots = [
            "08:30-09:50", "10:00-11:20", "11:30-12:50", 
            "01:00-02:20", "02:30-03:50", "04:00-05:15"
        ]
        
        # Lab Slots (2:45h)
        self.lab_slots = [
            "08:30-11:15", "11:30-02:15", "02:30-05:15"
        ]

    def get_time_overlap(self, slot1, slot2):
        """
        Helper to check if a Lab slot and a Theory slot overlap.
        Required for Hc2: Room Conflict check.
        """
        # Mapping labs to the theory slots they block
        overlaps = {
            "08:30-11:15": ["08:30-09:50", "10:00-11:20"],
            "11:30-02:15": ["11:30-12:50", "01:00-02:20"],
            "02:30-05:15": ["02:30-03:50", "04:00-05:15"]
        }
        
        # If one is a lab and one is theory, check the map
        if slot1 in overlaps and slot2 in self.theory_slots:
            return slot2 in overlaps[slot1]
        if slot2 in overlaps and slot1 in self.theory_slots:
            return slot1 in overlaps[slot2]
            
        return slot1 == slot2 # Same slot always overlaps

    def get_correct_room_pool(self, course):
        """
        DOMAIN ADAPTATION: Logic to ensure courses are placed in appropriate facilities.
        """
        if not course.is_lab:
            return self.rooms  # Theory classes go to 50 general rooms
        
        name = course.name.upper()
        # Logic for B-Digital (DLD)
        if "DIGITAL LOGIC DESIGN" in name:
            return self.digital_lab
        # Logic for English/S&H Labs
        elif any(word in name for word in ["EXPO", "ENGLISH", "FSM", "COMMUNICATION"]):
            return self.english_labs
        # Default for Computing Labs (OOP, DB, OS, PF, etc.)
        else:
            return self.comp_labs

    def generate_random_schedule(self):
        schedule = []
        for course in self.course_list:
            room_pool = self.get_correct_room_pool(course)
            
            for session_num in range(course.sessions_per_week):
                # Domain Adaptation: Select from Lab slots or Theory slots
                slots_to_use = self.lab_slots if course.is_lab else self.theory_slots
                
                assignment = {
                    'course': course,
                    'room': random.choice(room_pool),
                    'day': random.choice(self.days),
                    'slot': random.choice(slots_to_use),
                    'is_lab': course.is_lab
                }
                schedule.append(assignment)
        return schedule
    
    def calculate_fitness(self, schedule):
        hard_conflicts = 0
        instructor_busy = {} # (instructor, day, slot)
        room_busy = {}       # (room, day, slot)
        section_busy = {}    # (section, day, slot)

        for entry in schedule:
            c = entry['course']
            r = entry['room']
            d = entry['day']
            s = entry['slot']
            is_lab = entry['is_lab']

            # Create a list of 'Blocked' sub-slots to check for Lab/Theory overlaps
            # A lab from 8:30-11:15 blocks TWO theory slots.
            blocked_slots = [s]
            if is_lab:
                if s == "08:30-11:15": blocked_slots = ["08:30-09:50", "10:00-11:20"]
                elif s == "11:30-02:15": blocked_slots = ["11:30-12:50", "01:00-02:20"]
                elif s == "02:30-05:15": blocked_slots = ["02:30-03:50", "04:00-05:15"]

            for b_slot in blocked_slots:
                # Check Instructor
                if (c.instructor, d, b_slot) in instructor_busy:
                    hard_conflicts += 1
                instructor_busy[(c.instructor, d, b_slot)] = True

                # Check Room
                if (r, d, b_slot) in room_busy:
                    hard_conflicts += 1
                room_busy[(r, d, b_slot)] = True

                # Check Section
                if (c.section, d, b_slot) in section_busy:
                    hard_conflicts += 1
                section_busy[(c.section, d, b_slot)] = True

        return 1 / (1 + hard_conflicts)

    def mutate(self, schedule):
        """
        DOMAIN ADAPTATION: Smart Mutation.
        Fixes the AttributeError by selecting from the correct time pool (Lab vs Theory).
        """
        child = copy.deepcopy(schedule)
        idx = random.randint(0, len(child) - 1)
        
        # Identify if the gene we are mutating is a Lab or Theory class
        is_lab = child[idx]['is_lab']
        
        # Change either the room or the slot
        if random.random() > 0.5:
            # Use the correct pool based on the course type
            if is_lab:
                child[idx]['slot'] = random.choice(self.lab_slots)
            else:
                child[idx]['slot'] = random.choice(self.theory_slots)
        else:
            # Similarly for rooms, use the helper we created earlier
            room_pool = self.get_correct_room_pool(child[idx]['course'])
            child[idx]['room'] = random.choice(room_pool)
            
        return child

    def crossover(self, parent1, parent2):
        """
        Uniform Crossover: Combines two parent schedules.
        """
        child = []
        for gene1, gene2 in zip(parent1, parent2):
            child.append(copy.deepcopy(gene1 if random.random() > 0.5 else gene2))
        return child

    def evolve(self, generations=100):
        """
        The Main Search Loop: Evolution through Selection, Crossover, and Mutation.
        """
        # 1. Initialize Population
        population = [self.generate_random_schedule() for _ in range(self.pop_size)]
        
        for gen in range(generations):
            # Sort by Fitness (Informed Guidance)
            population = sorted(population, key=lambda x: self.calculate_fitness(x), reverse=True)
            
            current_best_fitness = self.calculate_fitness(population[0])
            
            # Success condition: Perfect schedule
            if current_best_fitness == 1.0:
                print(f"Optimal Solution Found at Generation {gen}!")
                return population[0]

            # 2. Selection: Keep the top 20% (Elitism)
            new_population = population[:int(self.pop_size * 0.2)]

            # 3. Reproduction: Fill the rest with offspring
            while len(new_population) < self.pop_size:
                p1, p2 = random.sample(population[:20], 2)
                child = self.crossover(p1, p2)
                if random.random() < 0.3: # 30% Mutation Rate
                    child = self.mutate(child)
                new_population.append(child)
            
            population = new_population

        return population[0] # Return the best found so far