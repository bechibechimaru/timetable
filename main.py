from datetime import datetime

class Teacher:
    def __init__(self, name, subjects, available_schedule):
        self.name = name
        self.subjects = subjects
        self.available_schedule = available_schedule

class Student:
    def __init__(self, name, grade, is_exam_candidate, subjects, available_schedule):
        self.name = name
        self.grade = grade
        self.is_exam_candidate = is_exam_candidate
        # subjects is a dictionary of {subject: {"required_slots": int, "regular_teacher": str}}
        self.subjects = subjects
        self.available_schedule = available_schedule
        self.assigned_lessons = {subject: 0 for subject in subjects}

class Schedule:
    def __init__(self, booth_count, time_slots):
        self.booth_count = booth_count
        self.time_slots = time_slots
        self.schedule = {}

    def can_assign(self, date, slot, teacher, student, subject):
        if date in self.schedule and slot in self.schedule[date]:
            for assignment in self.schedule[date][slot]:
                if assignment:
                    # 同じ日・同じ時間帯で別の科目を受けていないかをチェック
                    if assignment[1].name == student.name and assignment[2] != subject:
                        return False  # 同じ時間帯で違う科目は不可
                    
                    # 他の条件（生徒・教師の重複など）をチェック
                    if assignment[1].name == student.name or (assignment[3] and assignment[3].name == student.name):
                        return False
                    if assignment[0].name == teacher.name:
                        return False
        return True

    def assign(self, date, slot, booth, teacher, student1, subject, student2=None):
        if date not in self.schedule:
            self.schedule[date] = {}
        if slot not in self.schedule[date]:
            self.schedule[date][slot] = [None] * self.booth_count

        # 同じ時間帯、同じ生徒が重複しないかをチェック
        if self.schedule[date][slot][booth] is None and self.can_assign(date, slot, teacher, student1, subject):
            self.schedule[date][slot][booth] = (teacher, student1, subject, student2)
            return True
        elif (self.schedule[date][slot][booth] and self.schedule[date][slot][booth][0] == teacher
              and self.schedule[date][slot][booth][3] is None and self.can_assign(date, slot, teacher, student1, subject)):
            self.schedule[date][slot][booth] = (teacher, self.schedule[date][slot][booth][1], subject, student1)
            return True
        return False


    def allocate_schedule(self, students, teachers):
        for student in students:
            for subject, info in student.subjects.items():
                required_slots = info["required_slots"]
                assigned_slots = 0
                regular_teacher = info["regular_teacher"]

                # Try to assign slots with the regular teacher first
                for teacher in teachers:
                    if teacher.name == regular_teacher and subject in teacher.subjects:
                        assigned_slots = self.try_assign_subject(student, teacher, subject, required_slots, assigned_slots)
                        if assigned_slots >= required_slots:
                            break

                # If not enough slots are assigned, try other teachers for the same subject
                if assigned_slots < required_slots:
                    for teacher in teachers:
                        if teacher.name != regular_teacher and subject in teacher.subjects:
                            assigned_slots = self.try_assign_subject(student, teacher, subject, required_slots, assigned_slots)
                            if assigned_slots >= required_slots:
                                break

                # If the required slots cannot be assigned, attempt to fallback to other available slots
                if assigned_slots < required_slots:                    
                    self.attempt_fallback(student, subject, required_slots, assigned_slots)

    def attempt_fallback(self, student, subject, required_slots, assigned_slots):
        # If required slots are still not assigned, try other available slots across other days
        for teacher in teachers:
            if subject in teacher.subjects:
                for date in sorted(student.available_schedule.keys()):
                    if assigned_slots >= required_slots:
                        break
                    for slot in student.available_schedule[date]:
                        # Try assigning again with the fallback logic
                        for booth in range(self.booth_count):
                            if self.assign(date, slot, booth, teacher, student, subject):
                                assigned_slots += 1
                                student.assigned_lessons[subject] += 1
                                break

    def try_assign_subject(self, student, teacher, subject, required_slots, assigned_slots):
        for date in sorted(set(student.available_schedule.keys()) & set(teacher.available_schedule.keys())):
            available_slots = sorted(set(student.available_schedule[date]) & set(teacher.available_schedule[date]))
            for slot in available_slots:
                if assigned_slots < required_slots:
                    booth_assigned = False
                    for booth in range(self.booth_count):
                        if self.assign(date, slot, booth, teacher, student, subject):
                            assigned_slots += 1
                            student.assigned_lessons[subject] += 1
                            booth_assigned = True
                            break
                    if not booth_assigned:
                        for booth in range(self.booth_count):
                            current_assignment = self.schedule[date][slot][booth]
                            if current_assignment and current_assignment[0] == teacher and current_assignment[3] is None:
                                self.schedule[date][slot][booth] = (teacher, current_assignment[1], subject, student)
                                assigned_slots += 1
                                student.assigned_lessons[subject] += 1
                                break
                if assigned_slots >= required_slots:
                    break
            if assigned_slots >= required_slots:
                break
        return assigned_slots

    def check_unassigned_lessons(self, students):
        unassigned_lessons = []
        for student in students:
            for subject, info in student.subjects.items():
                required_slots = info["required_slots"]
                assigned_slots = student.assigned_lessons[subject]
                if assigned_slots < required_slots:
                    unassigned_lessons.append((student.name, subject, required_slots - assigned_slots))
        return unassigned_lessons

# Sample data setup
teachers = [
    Teacher("講師氏名", ["担当可能科目"], {"出勤可能日": ["出勤可能コマ"], })
]

students = [
    Student("生徒氏名", "学年", False, {"受講科目": {"required_slots": 必要授業数, "regular_teacher": "レギュラー講師"},  {"通塾可能日": ["通塾可能コマ"]})
]

# Schedule generation and assignment
schedule = Schedule(booth_count=12, time_slots=["12:30", "14:00", "15:30", "17:00", "18:30", "20:00"])
schedule.allocate_schedule(students, teachers)

# 結果を表示する
for date in sorted(schedule.schedule.keys()):
    slots = schedule.schedule[date]
    for slot in sorted(slots.keys()):
        booths = slots[slot]
        for booth, assignment in enumerate(booths):
            if assignment:
                teacher, student1, subject, student2 = assignment
                print(f"授業日: {date}, 授業コマ: {slot}, 担当講師: {teacher.name}, 生徒1: {student1.name} ({subject}), 生徒2: {student2.name} ({subject})" if student2 else f"授業日: {date}, 授業コマ: {slot}, 担当講師: {teacher.name}, 生徒1: {student1.name} ({subject}), 生徒2: なし")

# Check for unassigned lessons
unassigned_lessons = schedule.check_unassigned_lessons(students)
if unassigned_lessons:
    print("\n日程が足りないため組めませんでした")
    for student_name, subject, shortage in unassigned_lessons:
        print(f"生徒名: {student_name}, 科目: {subject}, 不足コマ数: {shortage}")
else:
    print("\nすべての生徒の必要コマ数が満たされました")
