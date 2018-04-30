-- Set file output format to tab delimited:
--     In SQL Server Management Studio: Tools > Options > Query Results > SQL Server > Results to Text >
-- 	       Output format: tab delimited
--         Include column headers in the result set: enabled
--     Restart SSMS for new settings to take effect

-- Prevent the count from showing up in the text file results
SET NOCOUNT ON;

-- Export person ID, start date, and concept IDs for conditions, drugs, and procedures
:OUT C:\Users\XXXX\Documents\cohd_data\data\unique_patient_concept_pairs_date.txt
SELECT DISTINCT co.person_id, YEAR(co.condition_start_date) AS date, co.condition_concept_id AS concept_id, 'Condition' AS domain_id
FROM dbo.condition_occurrence co
WHERE condition_concept_id != 0
UNION ALL
SELECT DISTINCT de.person_id, YEAR(de.drug_exposure_start_date) AS date, de.drug_concept_id AS concept_id, 'Drug' AS domain_id
FROM dbo.drug_exposure de
WHERE drug_concept_id != 0
UNION ALL
SELECT DISTINCT po.person_id, YEAR(po.procedure_date) AS date, po.procedure_concept_id AS concept_id, 'Procedure' AS domain_id
FROM dbo.procedure_occurrence po
WHERE procedure_concept_id != 0;

-- Export demographics from the person table
:OUT C:\Users\XXXX\Documents\cohd_data\data\person.txt
SELECT person_id, gender_concept_id, race_concept_id, ethnicity_concept_id
FROM dbo.person;

-- Export the concept definitions
-- Note: use union instead of union all because 0 is in each domain
:OUT C:\Users\XXXX\Documents\cohd_data\data\concepts.txt
SELECT concept.concept_id, concept_name, domain_id, concept_class_id
FROM
	(SELECT DISTINCT condition_concept_id AS concept_id FROM dbo.condition_occurrence
	UNION
	SELECT DISTINCT drug_concept_id AS concept_id FROM dbo.drug_exposure
	UNION
	SELECT DISTINCT procedure_concept_id AS concept_id FROM dbo.procedure_occurrence
	UNION
	SELECT DISTINCT gender_concept_id AS concept_id FROM dbo.person
	UNION
	SELECT DISTINCT race_concept_id AS concept_id FROM dbo.person
	UNION
	SELECT DISTINCT ethnicity_concept_id AS concept_id FROM dbo.person) concept_ids
LEFT JOIN dbo.concept ON concept_ids.concept_id = concept.concept_id;

-- Return to normal settings
SET NOCOUNT OFF;

