
import frappe
from frappe import _
from datetime import datetime, timedelta
from statistics import mean

BATCH_SIZE = 20  # Define the number of students to process per batch

@frappe.whitelist(allow_guest=True)
def update_students_earned_points():
    main_skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    main_skills = [skill['name'] for skill in main_skills]
    
    # Get settings from NUCTA Settings doctype
    settings = frappe.get_doc('NUCTA Settings')
    current_semester = settings.current_semester
    last_semester = settings.last_semester

    # Get all enrollments
    academic_courses_enrollments = frappe.get_all('Academic Course Enrollment', filters={'status_type': 'Completed'}, fields=['name', 'student_id', 'enrollment_to', 'semester'])
    extra_courses_enrollments = frappe.get_all('Extra Course Enrollment', filters={'status_type': 'Completed'}, fields=['name', 'student_id', 'enrollment_to', 'semester'])
    clubs_enrollments = frappe.get_all('Club Enrollment', filters={'status_type': 'Completed'}, fields=['name', 'student_id', 'enrollment_to', 'semester'])

    # Attach sub_skill contributions to each enrollment
    for enrollment in academic_courses_enrollments:
        enrollment['sub_skill'] = frappe.get_all('Academic Course Enrollment Contribution Table', filters={'parent': enrollment['name']}, fields=['sub_skill', 'sub_skill_contribution'])
    for enrollment in extra_courses_enrollments:
        enrollment['sub_skill'] = frappe.get_all('Extra Course Enrollment Contribution Table', filters={'parent': enrollment['name']}, fields=['sub_skill', 'sub_skill_contribution'])
    for enrollment in clubs_enrollments:
        enrollment['sub_skill'] = frappe.get_all('Club Enrollment Contribution Table', filters={'parent': enrollment['name']}, fields=['sub_skill', 'sub_skill_contribution'])

    enrollments = academic_courses_enrollments + extra_courses_enrollments + clubs_enrollments

    # Get all students
    students = frappe.get_all('Student', fields=['name'])
    total_students = len(students)

    # Process students in batches
    for i in range(0, total_students, BATCH_SIZE):
        batch_students = students[i:i + BATCH_SIZE]

        for student in batch_students:
            student_doc = frappe.get_doc('Student', student['name'])
            student_doc.skills_points = []  # Clear existing skill points
            student_doc.save(ignore_permissions=True)

        # Update skills_points for students
        for enrollment in enrollments:
            if enrollment['student_id'] in [student['name'] for student in batch_students]:
                student = frappe.get_doc('Student', enrollment['student_id'])
                for sub_skill in enrollment['sub_skill']:
                    student.append('skills_points', {
                        'semester': enrollment['semester'],
                        'sub_skill': sub_skill['sub_skill'],
                        'role': enrollment['enrollment_to'],
                        'points': sub_skill['sub_skill_contribution']
                    })
                student.save(ignore_permissions=True)

        # Commit after processing each batch to avoid keeping too many writes in a single transaction
        frappe.db.commit()

    # Continue with other calculations (skills_totals, normalization, etc.)
    for i in range(0, total_students, BATCH_SIZE):
        batch_students = students[i:i + BATCH_SIZE]

        # Reset skills_totals for each batch
        for student in batch_students:
            student_doc = frappe.get_doc('Student', student['name'])
            student_doc.skills_totals = []
            student_doc.save(ignore_permissions=True)

            # Calculate totals for skills_points
            sub_skill_totals = {}
            previous_sub_skill_totals = {}

            # Calculate totals for current and previous semesters separately
            for sub_skill in student_doc.skills_points:
                if sub_skill.sub_skill not in sub_skill_totals:
                    sub_skill_totals[sub_skill.sub_skill] = {
                        'total_points': 0,
                        'number_of_appearances': 0,
                        'diminishing_return_factor': frappe.get_doc('Sub-Skill', sub_skill.sub_skill).diminishing_return_factor
                    }
                sub_skill_totals[sub_skill.sub_skill]['total_points'] += sub_skill.points
                sub_skill_totals[sub_skill.sub_skill]['number_of_appearances'] += 1
                if sub_skill.semester != current_semester:
                    # For previous semesters
                    if sub_skill.sub_skill not in previous_sub_skill_totals:
                        previous_sub_skill_totals[sub_skill.sub_skill] = {
                            'total_points': 0,
                            'number_of_appearances': 0,
                            'diminishing_return_factor': frappe.get_doc('Sub-Skill', sub_skill.sub_skill).diminishing_return_factor
                        }
                    previous_sub_skill_totals[sub_skill.sub_skill]['total_points'] += sub_skill.points
                    previous_sub_skill_totals[sub_skill.sub_skill]['number_of_appearances'] += 1

            # Update skills_totals with both current and previous calculations
            for sub_skill, totals in sub_skill_totals.items():
                total_points = totals['total_points']
                number_of_appearances = totals['number_of_appearances']
                diminishing_return_factor = totals['diminishing_return_factor']
                if diminishing_return_factor == 0:
                    current_diminished_points = total_points
                else:
                    current_diminished_points = (float(total_points) / float(number_of_appearances)) + \
                                                ((float(number_of_appearances) - 1) * (1 - float(diminishing_return_factor)) *
                                                (float(total_points) / float(number_of_appearances)))
                if current_diminished_points > 1:
                    current_diminished_points = 1
                
                # Calculate previous_points if data is available for previous semesters
                if sub_skill in previous_sub_skill_totals:
                    previous_totals = previous_sub_skill_totals[sub_skill]
                    previous_total_points = previous_totals['total_points']
                    previous_number_of_appearances = previous_totals['number_of_appearances']
                    previous_diminishing_return_factor = previous_totals['diminishing_return_factor']
                    if previous_diminishing_return_factor == 0:
                        previous_points = previous_total_points
                    else:
                        previous_points = (float(previous_total_points) / float(previous_number_of_appearances)) + \
                                        ((float(previous_number_of_appearances) - 1) * (1 - float(previous_diminishing_return_factor)) *
                                        (float(previous_total_points) / float(previous_number_of_appearances)))
                    if previous_points > 1:
                        previous_points = 1
                else:
                    # If no data for previous semesters, set to 0
                    previous_points = 0  

                # Append the calculated values to the student's skills_totals table
                student_doc.append('skills_totals', {
                    'sub_skill': sub_skill,
                    'current_points': total_points,
                    'current_diminished_points': current_diminished_points,
                    'previous_points': previous_points
                })

            student_doc.save(ignore_permissions=True)

        # Commit after each batch
        frappe.db.commit()

    return 'Students updated successfully'

@frappe.whitelist(allow_guest=True)
def student_update_background_jobs():
    job = frappe.enqueue(update_students_earned_points, queue='long', timeout=0)
    return {"message": "Task has been started. It may take some time."}
