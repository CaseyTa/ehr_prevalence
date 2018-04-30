#!/bin/bash

# Connection settings for MySQL server. 
# You can fill these in or leave them empty to be prompted to enter these settings at runtime.
username=
database=

if [[ -z $database ]] 
then
    echo "Enter database:"
    read database
fi

if [[ -z $username ]] 
then
    echo "Enter username:"
    read username
fi

# Get password
echo "Enter password:"
read -s password

# Export the concept definitions
# Note: use union instead of union all because 0 is in each domain
echo "Exporting concepts"
mysql -u$username -p$password -D$database -e "
SELECT concept.concept_id, concept_name, domain_id, concept_class_id
FROM
	(SELECT DISTINCT condition_concept_id AS concept_id FROM condition_occurrence
	UNION
	SELECT DISTINCT drug_concept_id AS concept_id FROM drug_exposure
	UNION
	SELECT DISTINCT procedure_concept_id AS concept_id FROM procedure_occurrence
	UNION
	SELECT DISTINCT gender_concept_id AS concept_id FROM person
	UNION
	SELECT DISTINCT race_concept_id AS concept_id FROM person
	UNION
	SELECT DISTINCT ethnicity_concept_id AS concept_id FROM person) concept_ids
LEFT JOIN concept ON concept_ids.concept_id = concept.concept_id;" > concepts.txt


# Export demographics from the person table
echo "Exporting persons"
mysql -u$username -p$password -D$database -e "
SELECT person_id, gender_concept_id, race_concept_id, ethnicity_concept_id
FROM person;" > person.txt


# Export person ID, start date, and concept IDs for conditions, drugs, and procedures
echo "Exporting conditions, drugs, and procedures"
mysql -u$username -p$password -D$database -e "
SELECT DISTINCT co.person_id, YEAR(co.condition_start_date) AS date, co.condition_concept_id AS concept_id, 'Condition' AS domain_id
FROM condition_occurrence co
WHERE condition_concept_id != 0
UNION ALL
SELECT DISTINCT de.person_id, YEAR(de.drug_exposure_start_date) AS date, de.drug_concept_id AS concept_id, 'Drug' AS domain_id
FROM drug_exposure de
WHERE drug_concept_id != 0
UNION ALL
SELECT DISTINCT po.person_id, YEAR(po.procedure_date) AS date, po.procedure_concept_id AS concept_id, 'Procedure' AS domain_id
FROM procedure_occurrence po
WHERE procedure_concept_id != 0;" > unique_patient_concept_pairs_date.txt
