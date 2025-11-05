UPDATE grading_jobs
SET rubric = $$
    {
        "name": "Rubric Name",
        "description": "Rubric Description",
        "criteria": [
            {
                "criterionid": "1",
                "criterion": "Correctness",
                "levels": [
                    {"id": "1", "definition": "little to no documentation", "score": 0},
                    {"id": "2", "definition": "good documentation", "score": 25}
                ]
            },
            {
                "criterionid": "2",
                "criterion": "Logic",
                "levels": [
                    {"id": "3", "definition": "partial functionality", "score": 15},
                    {"id": "4", "definition": "fully functional", "score": 25}
                ]
            },
               {
                "criterionid": "3",
                "criterion": "Style",
                "levels": [
                    {"id": "3", "definition": "partial functionality", "score": 15},
                    {"id": "4", "definition": "fully functional", "score": 25}
                ]
            },
               {
                "criterionid": "4",
                "criterion": "Naming",
                "levels": [
                    {"id": "3", "definition": "partial functionality", "score": 15},
                    {"id": "4", "definition": "fully functional", "score": 25}
                ]
            },
               {
                "criterionid": "5",
                "criterion": "Test Cases",
                "levels": [
                    {"id": "3", "definition": "partial functionality", "score": 15},
                    {"id": "4", "definition": "fully functional", "score": 25}
                ]
            },
               {
                "criterionid": "6",
                "criterion": "Error Handling",
                "levels": [
                    {"id": "3", "definition": "partial functionality", "score": 15},
                    {"id": "4", "definition": "fully functional", "score": 25}
                ]
            },
               {
                "criterionid": "7",
                "criterion": "Efficiency",
                "levels": [
                    {"id": "3", "definition": "partial functionality", "score": 15},
                    {"id": "4", "definition": "fully functional", "score": 25}
                ]
            },
                 {
                "criterionid": "8",
                "criterion": "Documentation/Docstring",
                "levels": [
                    {"id": "3", "definition": "partial functionality", "score": 15},
                    {"id": "4", "definition": "fully functional", "score": 25}
                ]
            }
        ]
    }
$$::jsonb
WHERE id=1;