"""Lab 3.1 - Design an Embedded Document Schema
Course enrollment with embedded students, JSON Schema validation.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner, print_json


COURSES = [
    {
        "course_name": "Introduction to Machine Learning",
        "course_code": "AIML101",
        "instructor": "Dr. Priya Sharma",
        "credits": 4,
        "schedule": {"days": ["Monday", "Wednesday"], "time": "10:00-11:30", "room": "LH-201"},
        "enrolled_students": [
            {"name": "Arjun Mehta", "email": "arjun@college.edu", "grade": "A"},
            {"name": "Sneha Reddy", "email": "sneha@college.edu", "grade": "B+"},
            {"name": "Rahul Kumar", "email": "rahul@college.edu", "grade": "A-"},
            {"name": "Divya Patel", "email": "divya@college.edu", "grade": "B"},
        ]
    },
    {
        "course_name": "Deep Learning with PyTorch",
        "course_code": "AIML301",
        "instructor": "Dr. Anil Gupta",
        "credits": 3,
        "schedule": {"days": ["Tuesday", "Thursday"], "time": "14:00-15:30", "room": "LH-305"},
        "enrolled_students": [
            {"name": "Arjun Mehta", "email": "arjun@college.edu", "grade": None},
            {"name": "Kavya Nair", "email": "kavya@college.edu", "grade": "A"},
            {"name": "Vikram Singh", "email": "vikram@college.edu", "grade": "A+"},
        ]
    },
    {
        "course_name": "Natural Language Processing",
        "course_code": "AIML201",
        "instructor": "Dr. Meera Joshi",
        "credits": 3,
        "schedule": {"days": ["Monday", "Wednesday", "Friday"], "time": "09:00-10:00", "room": "LH-102"},
        "enrolled_students": [
            {"name": "Sneha Reddy", "email": "sneha@college.edu", "grade": "B+"},
            {"name": "Rahul Kumar", "email": "rahul@college.edu", "grade": None},
            {"name": "Priya Das", "email": "priya.d@college.edu", "grade": "A-"},
            {"name": "Arjun Mehta", "email": "arjun@college.edu", "grade": None},
            {"name": "Neha Gupta", "email": "neha@college.edu", "grade": "B"},
        ]
    },
]

# JSON Schema for validation
COURSE_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["course_name", "course_code", "instructor", "schedule", "enrolled_students"],
        "properties": {
            "course_name": {"bsonType": "string", "description": "Course name is required"},
            "course_code": {"bsonType": "string", "pattern": r"^[A-Z]{4}\d{3}$", "description": "Format: XXXX000"},
            "instructor": {"bsonType": "string", "description": "Instructor name is required"},
            "credits": {"bsonType": "int", "minimum": 1, "maximum": 6},
            "schedule": {
                "bsonType": "object",
                "required": ["days", "time", "room"],
                "properties": {
                    "days": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "time": {"bsonType": "string"},
                    "room": {"bsonType": "string"},
                }
            },
            "enrolled_students": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"bsonType": "string"},
                        "email": {"bsonType": "string"},
                        "grade": {"bsonType": ["string", "null"]},
                    }
                }
            },
        }
    }
}


def main():
    banner("Lab 3.1: Embedded Document Schema Design")

    db = get_db("nosql_labs")

    # Drop and recreate with validation
    if "courses" in db.list_collection_names():
        db.drop_collection("courses")
    db.create_collection("courses", validator=COURSE_VALIDATOR)
    col = db["courses"]
    print("[OK] Created 'courses' collection with JSON Schema validation.\n")

    # Insert courses
    col.insert_many(COURSES)
    print(f"[OK] Inserted {len(COURSES)} courses.\n")

    # Query: courses on Monday
    print("=== Courses on Monday ===")
    monday_courses = col.find({"schedule.days": "Monday"}, {"course_name": 1, "schedule.days": 1, "_id": 0})
    for c in monday_courses:
        print(f"  {c['course_name']} ({', '.join(c['schedule']['days'])})")

    # Query: by instructor
    print("\n=== Courses by Dr. Priya Sharma ===")
    priya_courses = col.find({"instructor": "Dr. Priya Sharma"}, {"course_name": 1, "enrolled_students": 1, "_id": 0})
    for c in priya_courses:
        names = [s["name"] for s in c["enrolled_students"]]
        print(f"  {c['course_name']}: {len(names)} students - {', '.join(names)}")

    # Add a new student using $push
    print("\n=== Add new student to NLP course ===")
    new_student = {"name": "Amit Verma", "email": "amit@college.edu", "grade": None}
    col.update_one(
        {"course_code": "AIML201"},
        {"$push": {"enrolled_students": new_student}}
    )
    updated = col.find_one({"course_code": "AIML201"})
    print(f"  Students in NLP now: {len(updated['enrolled_students'])}")

    # Test validation: try invalid document
    print("\n=== Testing Validation ===")
    try:
        col.insert_one({"course_name": "Invalid Course", "instructor": "Nobody"})
        print("  [ERROR] Validation should have failed!")
    except Exception as e:
        print(f"  [OK] Validation caught error: {e.details['errmsg'][:80]}...")

    # Student enrolled across multiple courses (Arjun Mehta)
    print("\n=== Arjun Mehta's Courses ===")
    arjun_courses = col.find({"enrolled_students.email": "arjun@college.edu"},
                             {"course_name": 1, "course_code": 1, "schedule.time": 1, "_id": 0})
    for c in arjun_courses:
        print(f"  {c['course_code']}: {c['course_name']} ({c['schedule']['time']})")

    banner("Lab 3.1 Complete")


if __name__ == "__main__":
    main()