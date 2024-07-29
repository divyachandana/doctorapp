def summarise_recent_health_info(json_data):
    return f"Provide a summary of the patient's recent health information first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_info(json_data):
    return f"Provide a summary of the patient's general information. Data:\n\n{json_data}"

def summarise_patient_allergies(json_data):
    return f"Provide a summary of the patient's allergy information first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_careplans(json_data):
    return f"Provide a summary of the patient's care plans first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_conditions(json_data):
    return f"Provide a summary of the patient's medical conditions first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_encounters(json_data):
    return f"Provide a summary of the patient's medical encounters first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_immunizations(json_data):
    return f"Provide a summary of the patient's immunization history first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_medications(json_data):
    return f"Provide a summary of the patient's medication history first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_observations(json_data):
    return f"Provide a summary of the patient's medical observations first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def summarise_patient_procedures(json_data):
    return f"Provide a summary of the patient's medical procedures first. Then, identify patterns, make predictions, and suggest care plans. Data:\n\n{json_data}"

def Augment(json_data, category):
    category_function_mapping = {
        "recent_health_info": summarise_recent_health_info,
        "patient_info": summarise_patient_info,
        "allergies": summarise_patient_allergies,
        "careplans": summarise_patient_careplans,
        "conditions": summarise_patient_conditions,
        "encounters": summarise_patient_encounters,
        "immunizations": summarise_patient_immunizations,
        "medications": summarise_patient_medications,
        "observations": summarise_patient_observations,
        "procedures": summarise_patient_procedures
    }
    if category in category_function_mapping:
        print(category)
        return category_function_mapping[category](json_data)
    else:
        raise ValueError(f"Unknown category: {category}")
