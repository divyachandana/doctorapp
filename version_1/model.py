from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import sessionmaker
import re


DATABASE = 'sqlite:///patients.db'
engine = create_engine(DATABASE)
metadata = MetaData()
metadata.reflect(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

# Define the tables
patients = Table('patients', metadata, autoload=True)
allergies = Table('allergies', metadata, autoload=True)
careplans = Table('careplans', metadata, autoload=True)
conditions = Table('conditions', metadata, autoload=True)
encounters = Table('encounters', metadata, autoload=True)
immunizations = Table('immunizations', metadata, autoload=True)
medications = Table('medications', metadata, autoload=True)
observations = Table('observations', metadata, autoload=True)
procedures = Table('procedures', metadata, autoload=True)

def fetch_all_patient_ids():
    result = session.execute(text("SELECT Id FROM patients"))
    return [row[0] for row in result]

def clean_name(name):
    if isinstance(name, str):
        return re.sub(r'\d+', '', name)
    return name

def fetch_related_data(query, params):
        result = session.execute(query, params).fetchall()
        return [dict(row._mapping) for row in result]


def fetch_patient_data(patient_id):
    patient_data = {}
    
    patient_info = session.execute(
        text("""SELECT BIRTHDATE, DEATHDATE, PREFIX, FIRST, LAST, MARITAL, ETHNICITY, GENDER, BIRTHPLACE, ADDRESS 
             FROM patients WHERE Id=:patient_id
        """),
        {"patient_id": patient_id}
    ).fetchone()

    patient_data['info'] = dict(patient_info._mapping)
    
    patient_data['allergies'] = fetch_related_data(
        text("""SELECT START, STOP,  DESCRIPTION 
             FROM allergies 
             WHERE PATIENT=:patient_id and STOP IS NULL ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )

    if not len(patient_data['allergies']):
        patient_data['allergies'] = fetch_related_data(
            text("""
                SELECT START, STOP, DESCRIPTION 
                FROM allergies 
                WHERE PATIENT=:patient_id 
                AND STOP = (SELECT MAX(STOP) FROM allergies WHERE PATIENT=:patient_id)
            """),
            {"patient_id": patient_id}
        )
    

    patient_data['medications'] = fetch_related_data(
        text("""SELECT START, STOP, DESCRIPTION, REASONDESCRIPTION 
             FROM medications 
             WHERE PATIENT=:patient_id and STOP IS NULL 
             ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )

    if not len(patient_data['medications']):
        patient_data['medications'] = fetch_related_data(
            text("""
                 SELECT START, STOP, DESCRIPTION, REASONDESCRIPTION 
                 FROM medications 
                 WHERE PATIENT=:patient_id 
                 AND STOP = (SELECT MAX(STOP) FROM medications WHERE PATIENT=:patient_id)
            """),
            {"patient_id": patient_id}
        )

    patient_data['careplans'] = fetch_related_data(
        text("""SELECT START, STOP, DESCRIPTION, REASONDESCRIPTION 
             FROM careplans 
             WHERE PATIENT=:patient_id and STOP IS NULL 
             ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )

    if not len(patient_data['careplans']):
        patient_data['careplans'] = fetch_related_data(
            text("""SELECT START, STOP, DESCRIPTION, REASONDESCRIPTION 
                 FROM careplans 
                 WHERE PATIENT=:patient_id 
                 AND STOP = (SELECT MAX(STOP) FROM careplans WHERE PATIENT=:patient_id)
            """),
            {"patient_id": patient_id}
        )
    
    patient_data['conditions'] = fetch_related_data(
        text("""SELECT START, STOP, DESCRIPTION 
             FROM conditions 
             WHERE PATIENT=:patient_id and STOP IS NULL 
             ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )
    if not len(patient_data['conditions']):
        patient_data['conditions'] = fetch_related_data(
            text("""SELECT START, STOP, DESCRIPTION 
                 FROM conditions 
                 WHERE PATIENT=:patient_id AND 
                 STOP = (SELECT MAX(STOP) FROM conditions WHERE PATIENT=:patient_id)
            """),
            {"patient_id": patient_id}
        )
    
    patient_data['encounters'] = fetch_related_data(
        text("""SELECT DATE, DESCRIPTION, REASONDESCRIPTION 
             FROM encounters 
             WHERE PATIENT=:patient_id 
             AND DATE = (SELECT MAX(DATE) FROM encounters WHERE PATIENT=:patient_id) 
             ORDER BY DATE DESC"""),
        {"patient_id": patient_id}
    )
    
    patient_data['immunizations'] = fetch_related_data(
        text("""SELECT DATE, DESCRIPTION 
             FROM immunizations 
             WHERE PATIENT=:patient_id 
             AND DATE = (SELECT MAX(DATE) FROM immunizations WHERE PATIENT=:patient_id) 
             ORDER BY DATE DESC
        """),
        {"patient_id": patient_id}
    )

    print('===patient_data====', patient_data)
    
    patient_data['observations'] = fetch_related_data(
        text("""SELECT DATE, DESCRIPTION, VALUE, UNITS 
             FROM observations 
             WHERE PATIENT=:patient_id 
             AND DATE = (SELECT MAX(DATE) FROM observations WHERE PATIENT=:patient_id) 
             ORDER BY DATE DESC"""),
        {"patient_id": patient_id}
    )
    
    patient_data['procedures'] = fetch_related_data(
        text("""SELECT DATE, DESCRIPTION, REASONDESCRIPTION 
             FROM procedures 
             WHERE PATIENT=:patient_id 
             AND DATE = (SELECT MAX(DATE) FROM procedures WHERE PATIENT=:patient_id) 
             ORDER BY DATE DESC
        """),
        {"patient_id": patient_id}
    )

    print("-----patient_data-----", patient_data)

    
    return patient_data


def prepare_prompt(patient_data):
    # prompt = "\n"
    # prompt += f"Name: {patient_data['info'].get('PREFIX', '')} {clean_name(patient_data['info'].get('FIRST'))} {clean_name(patient_data['info'].get('LAST'))}\n"
    # prompt += f"Birthdate: {patient_data['info'].get('BIRTHDATE')}\n"
    # # prompt += f"Deathdate: {patient_data['info'].get('DEATHDATE')}\n"
    # prompt += f"Marital Status: {patient_data['info'].get('MARITAL')}\n"
    # prompt += f"Ethnicity: {patient_data['info'].get('ETHNICITY')}\n"
    # prompt += f"Gender: {patient_data['info'].get('GENDER')}\n"
    # prompt += f"Birthplace: {patient_data['info'].get('BIRTHPLACE')}\n"
    # prompt += f"Address: {patient_data['info'].get('ADDRESS')}\n\n"
    
    # prompt += "Allergies:\n"
    # for allergy in patient_data['allergies']:
    #     prompt += f"- {allergy['DESCRIPTION']} (Start: {allergy['START']}, Stop: {allergy['STOP']})\n"
    
    # prompt += "\nMedications:\n"
    # for medication in patient_data['medications']:
    #     prompt += f"- {medication['DESCRIPTION']} (Start: {medication['START']}, Stop: {medication['STOP']}, Reason: {medication['REASONDESCRIPTION']})\n"
    
    # prompt += "\nCareplans:\n"
    # for careplan in patient_data['careplans']:
    #     prompt += f"- {careplan['DESCRIPTION']} (Start: {careplan['START']}, Stop: {careplan['STOP']}, Reason: {careplan['REASONDESCRIPTION']})\n"
    
    # prompt += "\nConditions:\n"
    # for condition in patient_data['conditions']:
    #     prompt += f"- {condition['DESCRIPTION']} (Start: {condition['START']}, Stop: {condition['STOP']})\n"
    
    # prompt += "\nEncounters:\n"
    # for encounter in patient_data['encounters']:
    #     prompt += f"- {encounter['DESCRIPTION']} (Date: {encounter['DATE']}, Reason: {encounter['REASONDESCRIPTION']})\n"
    
    # prompt += "\nImmunizations:\n"
    # for immunization in patient_data['immunizations']:
    #     prompt += f"- {immunization['DESCRIPTION']} (Date: {immunization['DATE']})\n"
    
    # prompt += "\nObservations:\n"
    # for observation in patient_data['observations']:
    #     prompt += f"- {observation['DESCRIPTION']} (Date: {observation['DATE']}, Value: {observation['VALUE']} {observation['UNITS']})\n"
    
    # prompt += "\nProcedures:\n"
    # for procedure in patient_data['procedures']:
    #     prompt += f"- {procedure['DESCRIPTION']} (Date: {procedure['DATE']}, Reason: {procedure['REASONDESCRIPTION']})\n"
    
    return f"Professionally summarize the recent medical data of a patient for a Doctor: {patient_data}"


def fetch_patient_category_data(patient_id, category):
    patient_data = {}

    if category == 'patients':
        patient_info = session.execute(
            text("""SELECT BIRTHDATE, DEATHDATE, PREFIX, FIRST, LAST, MARITAL, ETHNICITY, GENDER, BIRTHPLACE, ADDRESS 
                FROM patients WHERE Id=:patient_id
            """),
            {"patient_id": patient_id}
        ).fetchone()

        patient_data['patients'] = dict(patient_info._mapping)
    
    elif category == 'allergies':
        patient_data['allergies'] = fetch_related_data(
            text("SELECT START, STOP, CODE, DESCRIPTION FROM allergies WHERE PATIENT=:patient_id ORDER BY START DESC"),
            {"patient_id": patient_id}
        )
    elif category == 'medications':
        patient_data['medications'] = fetch_related_data(
            text("SELECT START, STOP, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION FROM medications WHERE PATIENT=:patient_id ORDER BY START DESC"),
            {"patient_id": patient_id}
        )
    elif category == 'careplans':
        patient_data['careplans'] = fetch_related_data(
            text("SELECT START, STOP, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION FROM careplans WHERE PATIENT=:patient_id ORDER BY START DESC"),
            {"patient_id": patient_id}
        )
    elif category == 'conditions':
        patient_data['conditions'] = fetch_related_data(
            text("SELECT START, STOP, CODE, DESCRIPTION FROM conditions WHERE PATIENT=:patient_id ORDER BY START DESC"),
            {"patient_id": patient_id}
        )
    elif category == 'encounters':
        patient_data['encounters'] = fetch_related_data(
            text("SELECT DATE, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION FROM encounters WHERE PATIENT=:patient_id ORDER BY DATE DESC"),
            {"patient_id": patient_id}
        )
    elif category == 'immunizations':
        patient_data['immunizations'] = fetch_related_data(
            text("SELECT DATE, CODE, DESCRIPTION FROM immunizations WHERE PATIENT=:patient_id ORDER BY DATE DESC"),
            {"patient_id": patient_id}
        )
    elif category == 'observations':
        patient_data['observations'] = fetch_related_data(
            text("SELECT DATE, CODE, DESCRIPTION, VALUE, UNITS FROM observations WHERE PATIENT=:patient_id ORDER BY DATE DESC"),
            {"patient_id": patient_id}
        )
    elif category == 'procedures':
        patient_data['procedures'] = fetch_related_data(
            text("SELECT DATE, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION FROM procedures WHERE PATIENT=:patient_id ORDER BY DATE DESC"),
            {"patient_id": patient_id}
        )

    print("-----patient_data-----", patient_data)

    
    return patient_data


def prepare_category_prompt(patient_data, category):

    prompt = "\n"
    
    prompt = patient_data
    # if category == 'patients':
    #     prompt += f"First Name: {clean_name(patient_data['patients'].get('FIRST',''))}\n"
    #     prompt += f"Last Name: {clean_name(patient_data['patients'].get('LAST',''))}\n"
    #     prompt += f"Marital Status: {patient_data['patients'].get('MARITAL','')}\n"
    #     prompt += f"Gender: {patient_data['patients'].get('GENDER','')}\n"
    #     prompt += f"Birth Date: {patient_data['patients'].get('BIRTHDATE','')}\n"
    #     prompt += f"Address: {patient_data['patients'].get('ADDRESS')}\n"
    #     return f"Generate Summary {prompt}"
    # else:
        # prompt = patient_data[category]
    # elif category == 'allergies':
    #     prompt += "Allergies:\n"
    #     for allergy in patient_data['allergies']:
    #         prompt += f"- Code: {allergy['CODE']} Description: {allergy['DESCRIPTION']} (Start: {allergy['START']}, Stop: {allergy['STOP']})\n"
    # elif category == 'medications':
    #     prompt += "\nMedications:\n"
    #     for medication in patient_data['medications']:
    #         prompt += f"- Code:{medication['CODE']} Description: {medication['DESCRIPTION']} (Start: {medication['START']}, Stop: {medication['STOP']}, Reason Code: {medication['REASONCODE']} Reason: {medication['REASONDESCRIPTION']})\n"
    # elif category == 'careplans':
    #     prompt += "\nCareplans:\n"
    #     for careplan in patient_data['careplans']:
    #         prompt += f"- Code:{careplan['CODE']} Description: {careplan['DESCRIPTION']} (Start: {careplan['START']}, Stop: {careplan['STOP']}, Reason Code: {careplan['REASONCODE']} Reason: {careplan['REASONDESCRIPTION']})\n"
    # elif category == 'conditions':
    #     prompt += "\nConditions:\n"
    #     for condition in patient_data['conditions']:
    #         prompt += f"- Code:{condition['CODE']} Description: {condition['DESCRIPTION']} (Start: {condition['START']}, Stop: {condition['STOP']})\n"
    # elif category == 'encounters':
    #     prompt += "\nEncounters:\n"
    #     for encounter in patient_data['encounters']:
    #         prompt += f"- Code:{encounter['CODE']} Description: {encounter['DESCRIPTION']} (Date: {encounter['DATE']}, Reason Code: {encounter['REASONCODE']}  Reason: {encounter['REASONDESCRIPTION']})\n"
    # elif category == 'immunizations':
    #     prompt += "\nImmunizations:\n"
    #     for immunization in patient_data['immunizations']:
    #         prompt += f"- Code:{immunization['CODE']} Description: {immunization['DESCRIPTION']} (Date: {immunization['DATE']})\n"
    # elif category == 'observations':
    #     prompt += "\nObservations:\n"                                 
    #     for observation in patient_data['observations']:
    #         prompt += f"- Code:{observation['CODE']} Description: {observation['DESCRIPTION']} (Date: {observation['DATE']}, Value: {observation['VALUE']} {observation['UNITS']})\n"
    # elif category == 'procedures':
    #     prompt += "\nProcedures:\n"
    #     for procedure in patient_data['procedures']:
    #         prompt += f"- Code:{procedure['CODE']} Description: {procedure['DESCRIPTION']} (Date: {procedure['DATE']}, Reason Code: {procedure['REASONCODE']} Reason: {procedure['REASONDESCRIPTION']})\n"
    
    return f"Summarize the patient's {category} data from latest to oldest. Identify patterns, make predictions, and provide care plans if necessary.Ignore if any fields have none. {prompt}"


def fetch_all_patient_data(patient_id):
    patient_data = {}
    
    patient_info = session.execute(
        text("""SELECT BIRTHDATE, DEATHDATE, PREFIX, FIRST, LAST, MARITAL, ETHNICITY, GENDER, BIRTHPLACE, ADDRESS 
             FROM patients WHERE Id=:patient_id
        """),
        {"patient_id": patient_id}
    ).fetchone()

    patient_data['info'] = dict(patient_info._mapping)
    
    patient_data['allergies'] = fetch_related_data(
        text("""SELECT START, STOP, CODE, DESCRIPTION
             FROM allergies 
             WHERE PATIENT=:patient_id ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )


    patient_data['medications'] = fetch_related_data(
        text("""SELECT START, STOP, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION
             FROM medications 
             WHERE PATIENT=:patient_id
             ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )

    patient_data['careplans'] = fetch_related_data(
        text("""SELECT START, STOP, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION
             FROM careplans 
             WHERE PATIENT=:patient_id
             ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )
    
    patient_data['conditions'] = fetch_related_data(
        text("""SELECT START, STOP, CODE, DESCRIPTION 
             FROM conditions 
             WHERE PATIENT=:patient_id
             ORDER BY START DESC
        """),
        {"patient_id": patient_id}
    )
    
    patient_data['encounters'] = fetch_related_data(
        text("""SELECT DATE, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION
             FROM encounters 
             WHERE PATIENT=:patient_id 
             ORDER BY DATE DESC"""),
        {"patient_id": patient_id}
    )
    
    patient_data['immunizations'] = fetch_related_data(
        text("""SELECT DATE, CODE, DESCRIPTION
             FROM immunizations 
             WHERE PATIENT=:patient_id 
             ORDER BY DATE DESC
        """),
        {"patient_id": patient_id}
    )
    
    patient_data['observations'] = fetch_related_data(
        text("""SELECT DATE, CODE, DESCRIPTION, VALUE, UNITS 
             FROM observations 
             WHERE PATIENT=:patient_id 
             ORDER BY DATE DESC"""),
        {"patient_id": patient_id}
    )
    
    patient_data['procedures'] = fetch_related_data(
        text("""SELECT DATE, CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION 
             FROM procedures 
             WHERE PATIENT=:patient_id 
             ORDER BY DATE DESC
        """),
        {"patient_id": patient_id}
    )

    return patient_data


def prepare_prompt_all(patient_data):
    prompt = "Personal Details:\n"
    prompt += f"Name: {patient_data['info'].get('PREFIX', '')} {clean_name(patient_data['info'].get('FIRST',''))} {clean_name(patient_data['info'].get('LAST'))}\n"
    prompt += f"Birthdate: {patient_data['info'].get('BIRTHDATE')}\n"
    # prompt += f"Deathdate: {patient_data['info'].get('DEATHDATE')}\n"
    prompt += f"Marital Status: {patient_data['info'].get('MARITAL')}\n"
    prompt += f"Ethnicity: {patient_data['info'].get('ETHNICITY')}\n"
    prompt += f"Gender: {patient_data['info'].get('GENDER')}\n"
    prompt += f"Birthplace: {patient_data['info'].get('BIRTHPLACE')}\n"
    prompt += f"Address: {patient_data['info'].get('ADDRESS')}\n\n"
    
    prompt += "Allergies:\n"
    for allergy in patient_data['allergies']:
        prompt += f"- Code: {allergy.get('CODE')} Description: {allergy['DESCRIPTION']} (Start: {allergy['START']}, Stop: {allergy['STOP']})\n"
    
    # print(patient_data['medications'])
    prompt += "\nMedications:\n"
    for medication in patient_data['medications']:
        prompt += f"- Code:{medication.get('CODE')} Description: {medication['DESCRIPTION']} (Start: {medication['START']}, Stop: {medication['STOP']}, Reason Code: {medication['REASONCODE']} Reason: {medication['REASONDESCRIPTION']})\n"
    
    prompt += "\nCareplans:\n"
    for careplan in patient_data['careplans']:
        prompt += f"- Code:{careplan.get('CODE')} Description: {careplan['DESCRIPTION']} (Start: {careplan['START']}, Stop: {careplan['STOP']}, Reason Code: {careplan['REASONCODE']} Reason: {careplan['REASONDESCRIPTION']})\n"
    
    prompt += "\nConditions:\n"
    for condition in patient_data['conditions']:
        prompt += f"- Code:{condition.get('CODE')} Description: {condition['DESCRIPTION']} (Start: {condition['START']}, Stop: {condition['STOP']})\n"
    
    prompt += "\nEncounters:\n"
    for encounter in patient_data['encounters']:
        prompt += f"- Code:{encounter.get('CODE')} Description: {encounter['DESCRIPTION']} (Date: {encounter['DATE']}, Reason Code: {encounter['REASONCODE']}  Reason: {encounter['REASONDESCRIPTION']})\n"
    
    prompt += "\nImmunizations:\n"
    for immunization in patient_data['immunizations']:
        prompt += f"- Code:{immunization.get('CODE')} Description: {immunization['DESCRIPTION']} (Date: {immunization['DATE']})\n"
    
    prompt += "\nObservations:\n"
    for observation in patient_data['observations']:
        prompt += f"- Code:{observation.get('CODE')} Description: {observation['DESCRIPTION']} (Date: {observation['DATE']}, Value: {observation['VALUE']} {observation['UNITS']})\n"
    
    prompt += "\nProcedures:\n"
    for procedure in patient_data['procedures']:
        prompt += f"- Code:{procedure.get('CODE')} Description: {procedure['DESCRIPTION']} (Date: {procedure['DATE']}, Reason Code: {procedure['REASONCODE']} Reason: {procedure['REASONDESCRIPTION']})\n"
    
    return f"{prompt}"


