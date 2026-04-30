import pandas as pd
import streamlit as st


def _blocked_slots(slot, is_lab):
    if not is_lab:
        return [slot]
    if slot == "08:30-11:15":
        return ["08:30-09:50", "10:00-11:20"]
    if slot == "11:30-02:15":
        return ["11:30-12:50", "01:00-02:20"]
    return ["02:30-03:50", "04:00-05:15"]


def _selected_slot_blocks(slot, theory_slots, lab_slots):
    if slot in lab_slots:
        return _blocked_slots(slot, True)
    return [slot]


def _room_capacity_map(rooms, labs):
    capacities = {}
    for room in rooms:
        try:
            num = int(room.split()[-1])
            if 1 <= num <= 20:
                capacities[room] = 60
            elif 21 <= num <= 35:
                capacities[room] = 50
            else:
                capacities[room] = 40
        except Exception:
            capacities[room] = 40
    for lab in labs:
        capacities[lab] = 30
    return capacities


def render_availability(schedule, rooms, labs, theory_slots, lab_slots):
    st.subheader("Real-Time Availability Spotlight")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    all_slots = theory_slots + lab_slots
    sel_day = st.selectbox("Day", days, key="avail_day")
    sel_slot = st.selectbox("Time Slot", all_slots, key="avail_slot")

    capacities = _room_capacity_map(rooms, labs)
    min_cap = st.slider("Minimum capacity", 20, 80, 40, key="min_capacity")

    blocked = _selected_slot_blocks(sel_slot, theory_slots, lab_slots)
    occupied_rooms = set()

    for entry in schedule:
        if entry['day'] != sel_day:
            continue
        entry_blocks = _blocked_slots(entry['slot'], entry['is_lab'])
        if any(b in entry_blocks for b in blocked):
            occupied_rooms.add(entry['room'])

    available_rooms = [r for r in rooms if r not in occupied_rooms and capacities.get(r, 0) >= min_cap]
    occupied_room_list = [r for r in rooms if r in occupied_rooms and capacities.get(r, 0) >= min_cap]

    st.caption(f"Available rooms: {len(available_rooms)} | Occupied rooms: {len(occupied_room_list)}")

    def render_room_cards(room_list, color):
        cols = st.columns(4)
        for i, room in enumerate(room_list):
            card = (
                f"<div class='room-card {color}'>"
                f"<div class='room-title'>{room}</div>"
                f"<div class='room-cap'>Capacity {capacities.get(room, 0)}</div>"
                f"</div>"
            )
            cols[i % 4].markdown(card, unsafe_allow_html=True)

    st.markdown("**Available**")
    render_room_cards(available_rooms, "available")

    st.markdown("**Occupied**")
    render_room_cards(occupied_room_list, "occupied")


def render_smart_booker(schedule, courses, sections, teachers, theory_slots, lab_slots):
    st.subheader("Smart-Booker (Conflict Validator)")

    col_a, col_b = st.columns(2)
    section = col_a.selectbox("Section", sections, key="sb_section")
    teacher = col_b.selectbox("Teacher", teachers, key="sb_teacher")

    teaches_section = any(
        c.section == section and c.instructor == teacher for c in courses
    )
    if not teaches_section:
        st.warning("This teacher does not teach the selected section. Show availability anyway?")
        allow = st.checkbox("Yes, show availability", key="sb_override")
        if not allow:
            return

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    grid = pd.DataFrame("Free", index=theory_slots + lab_slots, columns=days)

    section_busy = {day: set() for day in days}
    teacher_busy = {day: set() for day in days}

    for entry in schedule:
        blocked = _blocked_slots(entry['slot'], entry['is_lab'])
        if entry['course'].section == section:
            section_busy[entry['day']].update(blocked)
            if entry['is_lab']:
                section_busy[entry['day']].add(entry['slot'])
        if entry['course'].instructor == teacher:
            teacher_busy[entry['day']].update(blocked)
            if entry['is_lab']:
                teacher_busy[entry['day']].add(entry['slot'])

    for day in days:
        for slot in theory_slots + lab_slots:
            busy = slot in section_busy[day] or slot in teacher_busy[day]
            grid.at[slot, day] = "Busy" if busy else "Mutual Free"

    def highlight_cells(val):
        if val == "Mutual Free":
            return "background-color: #D1FAE5; color: #065F46;"
        return "background-color: #FDE2E2; color: #7F1D1D;"

    st.dataframe(grid.style.applymap(highlight_cells), use_container_width=True, height=420)

    if (grid == "Mutual Free").sum().sum() == 0:
        suggestion = None
        for entry in schedule:
            if entry['course'].section != section or not entry['is_lab']:
                continue
            current_room = entry['room']
            day = entry['day']
            slot = entry['slot']
            lab_rooms = sorted({e['room'] for e in schedule if e['is_lab']})
            blocked = _blocked_slots(slot, True)
            for room in lab_rooms:
                if room == current_room:
                    continue
                conflict = False
                for e2 in schedule:
                    if e2['day'] != day or e2['room'] != room:
                        continue
                    if any(b in _blocked_slots(e2['slot'], e2['is_lab']) for b in blocked):
                        conflict = True
                        break
                if not conflict:
                    suggestion = f"Try moving {entry['course'].code} lab from {current_room} to {room} on {day} {slot}."
                    break
            if suggestion:
                break

        if suggestion:
            st.info(suggestion)
        else:
            st.warning("No mutual free slot found. Try adjusting other classes or increasing room options.")


def render_student_path(schedule, courses):
    st.subheader("Student Personal Path View")

    course_codes = sorted({c.code for c in courses})
    code = st.selectbox("Course code", course_codes, key="sp_code")
    sections = sorted({c.section for c in courses if c.code == code})
    section = st.selectbox("Section", sections, key="sp_section")

    rows = []
    for entry in schedule:
        if entry['course'].code == code and entry['course'].section == section:
            rows.append({
                "Day": entry['day'],
                "Slot": entry['slot'],
                "Room": entry['room'],
                "Instructor": entry['course'].instructor,
                "Type": "Lab" if entry['is_lab'] else "Theory"
            })

    if rows:
        st.dataframe(pd.DataFrame(rows).sort_values(["Day", "Slot"]), use_container_width=True)
    else:
        st.warning("No schedule found for this course/section.")


def render_substitution(schedule, courses, theory_slots, lab_slots):
    st.subheader("Automatic Substitution Finder")

    class_options = []
    for entry in schedule:
        label = f"{entry['course'].code} | {entry['course'].section} | {entry['day']} {entry['slot']} | {entry['room']}"
        class_options.append((label, entry))

    selected = st.selectbox("Scheduled class", [c[0] for c in class_options], key="sub_class")
    entry = next(item for label, item in class_options if label == selected)

    max_daily = st.slider("Max daily teaching slots", 2, 8, 4, key="sub_max_daily")

    target_code = entry['course'].code
    target_category = entry['course'].category
    day = entry['day']
    blocked = _blocked_slots(entry['slot'], entry['is_lab'])

    instructor_busy = {}
    instructor_daily = {}
    for e in schedule:
        blocks = _blocked_slots(e['slot'], e['is_lab'])
        instructor_busy.setdefault(e['course'].instructor, {}).setdefault(e['day'], set()).update(blocks)
        instructor_daily.setdefault(e['course'].instructor, {}).setdefault(e['day'], 0)
        instructor_daily[e['course'].instructor][e['day']] += len(blocks)

    candidates = []
    for c in courses:
        if c.code != target_code and c.category != target_category:
            continue
        busy = instructor_busy.get(c.instructor, {}).get(day, set())
        if any(b in busy for b in blocked):
            continue
        if instructor_daily.get(c.instructor, {}).get(day, 0) >= max_daily:
            continue
        candidates.append(c.instructor)

    candidates = sorted(set(candidates))
    if candidates:
        st.success(f"Suggested substitutes: {', '.join(candidates[:15])}")
    else:
        st.warning("No qualified, available substitute found with the current limits.")


def render_analytics(schedule, rooms, labs, theory_slots, lab_slots):
    st.subheader("Room Utilization Analytics")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    room_usage = {r: 0 for r in rooms}
    lab_usage = {l: 0 for l in labs}

    for entry in schedule:
        blocks = _blocked_slots(entry['slot'], entry['is_lab'])
        if entry['room'] in room_usage:
            room_usage[entry['room']] += len(blocks)
        if entry['room'] in lab_usage:
            lab_usage[entry['room']] += 1

    room_total = len(theory_slots) * len(days)
    lab_total = len(lab_slots) * len(days)

    room_util = {k: (v / room_total) * 100 for k, v in room_usage.items()}
    lab_util = {k: (v / lab_total) * 100 for k, v in lab_usage.items()}

    under_util = dict(sorted(room_util.items(), key=lambda x: x[1])[:10])
    if under_util:
        st.markdown("**Most under-utilized theory rooms**")
        st.bar_chart(pd.Series(under_util))

    if lab_util:
        st.markdown("**Lab utilization**")
        st.bar_chart(pd.Series(dict(sorted(lab_util.items(), key=lambda x: x[1]))))

    peak = {slot: 0 for slot in theory_slots}
    for entry in schedule:
        for b in _blocked_slots(entry['slot'], entry['is_lab']):
            if b in peak:
                peak[b] += 1

    st.markdown("**Peak hours**")
    st.bar_chart(pd.Series(peak))
