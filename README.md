# EHR Prevalence and Co-occurrence Frequencies

This project analyzes an OMOP database to measure EHR prevalence and co-occurrence frequencies of all observed conditions, drugs, procedures and patient demographics (ethnicity, race, and gender). 

Count is determined as the number of patients with the given concept or pair of concepts. EHR prevalence and co-occurrence frequency are calculated as count / number of patients in the time range. 

Options are available to exclude concepts with counts below a specified threshold (e.g., <= 10 patients for HIPAA protection) and to randomize counts for additional protection. 

This is the analysis performed to generate the [Columbia Open Health Data (COHD)](cohd.nsides.io).

## Pre-requisites

* Python 2
* Numpy: ```pip install numpy```


## Running

Analyses involve patient identifiable information (PII) and should be handled in accordance with your institution's rules and regulations. 

### Export from OMOP tables 

Export data from the OMOP database to tab-delimited data files for further processing in Python. Code is provided to extract from SQL Server and MySQL. See ```cohd_omop_export_sql_server.sql``` or ```cohd_omop_export_mysql.sql```. 

SQL Server (using SQL Server Management Studio):
1. Update settings in SQL Server Manangement Studio so that Results to Text saves tab-delimited files  
Tools > Options > Query Results > SQL Server > Results to Text  
Output format: tab delimited  
Include column headers in the result set: enabled  
Restart SSMS for new settings to take effect
2. Open ```cohd_omop_export_sql_server.sql```
3. Enable SQLCMD mode:  
Query > SQLCMD Mode
4. Update the output paths in the :OUT command
5. Execute

MySQL (using mysql command line):
1. Optional: Open ```cohd_omop_export_mysql.sh``` and update the connection settings (user and database)
2. Execute ```./cohd_omop_export_mysql.sh```

The following files are produced. All files should be tab-delimited and include a header. 

1. ```concepts.txt```  
Extract from the OMOP concept table. Does not contain PII. Columns: concept_id, concept_name, domain_id, concept_class_id
2. ```person.txt```  
Extract from the OMOP person table. **Contains PII**. Columns: person_id, gender_concept_id, race_concept_id, ethnicity_concept_id
3. ```unique_patient_concept_pairs_date.txt```  
Extract and union from the OMOP condition_occurrence, drug_exposure, and procedure_occurrence tables. **Contains PII**. Columns:   
person_id  
date: year of condition_start_date, drug_exposure_start_date, or procedure_date  
concept_id: condition_concept_id, drug_concept_id, or procedure_concept_id  
domain_id: "Condition", "Drug", or "Procedure"

Synthetic example files can be found in the ```synthetic_example_files``` folder. 


### EHR prevalence and co-occurrence analyses
Occurrence and co-occurrence analyses are performed in Python    
1. Open ```ehr_prevalence_script.py```
2. Update the settings (paths, file names, database, year ranges, etc) as needed.  
The default configuration produces a set of basic data quality analyses, the EHR prevalence analysis restricted to data from a 5-year range ("5-year dataset"), and the EHR prevalence analyses over the entire dataset ("lifetime dataset").  
For the 5-year dataset, we suggest using the most recent 5 complete years in the OMOP database, e.g., if the OMOP database covers up to mid-2017, then use the range ```range_5year = (2012, 2016)```  
To share data: we recommend ```min_count = 11``` and ```randomize = True``` (default).  
3. If needed, update the code for reading in the text files if your database writes the text files in a different format
4. run ```python ./ehr_prevalence_script.py```

## Results

Exporting from the OMOP database produces files containing PII (```person.txt``` and ```unique_patient_concept_pairs_date.txt```). Please do not share these files. 

Running ```ehr_prevalence_script.py``` with default settings will produce the following files.

Data quality files: these files contain annual counts of patients, concepts, and prevalence counts for basic consistency checks.
1.  ```dq_patients_year.txt```  
The number of patients per year
2.  ```dq_domain_year_total_count.txt```  
The sum of all counts within each domain per year
3.  ```dq_domain_year_num_concepts.txt```  
The number of distinct concepts in each domain per year

Concept counts files: these files contain the prevalence data of each concept or pair of concepts. 
1. ```concept_counts_<settings>.txt```  
Single concept counts and frequencies (1 file for the 5-year dataset and 1 file for the lifetime dataset)
2. ```concept_pair_counts_<settings>.txt```  
Paired concept counts and frequencies (1 file for the 5-year dataset and 1 file for the lifetime dataset)
3. ```concept_counts_yearly_<settings>.txt```  
Counts and frequencies of each single concept per year (default settings do not generate this analysis)

Synthetic example files can be found in the ```synthetic_example_files``` folder. 
