import os
from ehr_prevalence import *


# Settings
# Directory where data are stored
data_dir = r'C:\Users\XXXX\Documents\cohd_data\data'  
# Directory where results will be stored
results_dir = r'C:\Users\XXXX\Documents\cohd_data\results'  
# File names of database dump files
person_file = 'person.txt'
concept_patient_file = 'unique_patient_concept_pairs_date.txt' 
concept_file = 'concepts.txt' 
# Where were the database dump files generated from? 
# Affects how the dump files are read. Options:
#     ssms: Microsoft SQL Server Management Studio
#     mysql: MySQL
database = 'ssms'  
# Range of years to include to calculate the 5-year dataset
range_5year = (2013, 2017)
# Range of years to include to calculate the  lifetime dataset
range_lifetime = (0, 9999)
# Randomize
randomize = True
# Minimum count for a concept to be included
min_count = 11

# Load the data    
concept_file = os.path.join(data_dir, concept_file)
concepts = load_concepts(concept_file, database)
person_file = os.path.join(data_dir, person_file)
patient_info = load_patient_data(person_file, database)
concept_patient_file = os.path.join(data_dir, concept_patient_file)
cp_data = load_concept_patient_data(concept_patient_file, database, patient_info)

# Basic quality analysis
quality_analysis(results_dir, cp_data, concepts, min_count=0)

# Single concept analyses
# 5-year dataset
cp_data_5year = merge_concepts_years(cp_data, range_5year[0], range_5year[1])
single_concept_ranged_counts(results_dir, cp_data_5year, randomize, min_count)
# Lifetime dataset
cp_data_lifetime = merge_concepts_years(cp_data, range_lifetime[0], range_lifetime[1])
single_concept_ranged_counts(results_dir, cp_data_lifetime, randomize, min_count)

# Paired concept analyses
# 5-year dataset
paired_concept_ranged_counts(results_dir, cp_data_5year, randomize, min_count)
# Lifetime dataset
paired_concept_ranged_counts(results_dir, cp_data_lifetime, randomize, min_count)

# Annual counts
# single_concept_yearly_counts(results_dir, cp_data, randomize, min_count)
# paired_concept_yearly_counts(results_dir, cp_data, randomize, min_count)  

