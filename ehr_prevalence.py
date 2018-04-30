"""Calculates EHR prevalence and co-occurrence frequencies"""

import os
import sys
import csv
import numpy
import random
import datetime
from collections import defaultdict
from collections import namedtuple
import codecs

"""Stores data on concepts and patients per year

named tuple
-----------
concept_year_patient: nested dictionary[concept_id][year] -> set(patient_ids)
year_patient: dictionary[year] -> set(patient_ids)
year_numpatients: dictionary[year] -> # patients
"""
ConceptPatientData = namedtuple('ConceptPatientData', 
    ['concept_year_patient', 'year_patient', 'year_numpatients'])
    
"""Stores data on concepts and patients over a range of years

named tuple
-----------
concept_year_patient: dictionary[concept_id] -> set(patient_ids)
patient: set(patient_ids) observed in the year range
num_patients: # patients observed in the year range
year_min: earliest year in year range
year_max: latest year in year range
"""
ConceptPatientDataMerged = namedtuple('ConceptPatientDataMerged', 
    ['concept_patient', 'patient', 'num_patients', 'year_min', 'year_max'])


def _unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    """Read a CSV file encoded in Unicode
    
    The native csv.reader does not read Unicode. Encode the data source
    as UTF-8
    """
    return csv.reader(_utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
                            
        
def _utf_8_encoder(unicode_csv_data):
    """Encodes Unicode source as UTF-8"""
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def _open_csv_reader(file, database):
    """Opens a CSV reader compatible with the specified database
    
    Parameters
    ----------
    file: string - file name 
    database: string - database which the file was generated from
        "ssms" - SQL Server Management Studio
        "mysql" - MySQL
    """
    if database == 'ssms':
        # Microsoft SQL Server Management Studio output
        fh = codecs.open(file, 'r', encoding='utf-8-sig')  
        reader = _unicode_csv_reader(fh, delimiter='\t')
    elif database == 'mysql':
        # MySQL output
        fh = open(file)  
        reader = csv.reader(fh, delimiter='\t') 
    else:
        fh = open(file) 
        reader = csv.reader(fh, delimiter='\t') 

    return fh, reader
  
  
def _open_csv_writer(file):
    """Opens a CSV writer
    
    Opens a CSV writer compatible with the current OS environment
    """
    # OS dependent parameters
    csv_writer_params = {}
    if sys.platform == 'win32':
        # Windows needs lineterminator specified for csv writer
        csv_writer_params['lineterminator'] = '\n'
        
    # Open file handle and csv_writer
    fh = open(file,'w')
    writer = csv.writer(fh, delimiter='\t', **csv_writer_params)
    return fh, writer
    

def _find_columns(header, column_names):
    """Finds the index of the column names in the header"""
    return [[i for i in range(len(header)) if header[i] == column_name][0] \
        for column_name in column_names]

    
def load_patient_data(file, database, extra_header_lines_skip=0):
    """Load patient demographics data extracted from the OMOP person table
    
    Parameters
    ----------
    file: string - Patient data file
    database: string - Originating database. See _open_csv_reader
    extra_header_lines_skip - int - Number of lines to skip after the header
    
    Returns
    -------
    Dictionary[concept_id] -> [ethnicity, race, gender]
    """
    print "Loading patient data..."

    # Open csv reader
    fh, reader = _open_csv_reader(file, database)
 
    # Read header line to get column names
    header = reader.next()
    columns = _find_columns(header, ['person_id', 'ethnicity_concept_id', 'race_concept_id', 'gender_concept_id'])
    table_width = len(header)

    # Skip extra formatting lines after header
    for i in range(extra_header_lines_skip):
        reader.next()

    # Read in each row
    patient_info = defaultdict(list)
    for row in reader:
        # Display progress
        if reader.line_num % 1000000 == 0: 
            print reader.line_num
            
        if len(row) == table_width:
            # Get ethnicity, race, and gender
            person_id, ethnicity, race, gender = [row[i] for i in columns]
            patient_info[person_id] = [ethnicity, race, gender] 

    print "%d persons loaded" % len(patient_info)
            
    fh.close()
    return patient_info

    
def load_concept_patient_data(file, database, patient_info, extra_header_lines_skip=0):
    """Load concept-year-patient data
    
    Parameters
    ----------
    file: string - data file with concept_id, year, patient_id, and domain
    database: string - Originating database. See _open_csv_reader
    patient_info: object - Returned from load_patient_data
    extra_header_lines_skip - int - Number of lines to skip after the header
    
    Returns
    -------
    ConceptPatientData object
    """
    print "Loading condition, drug, and procedure data..."

    # Open csv reader
    fh, reader = _open_csv_reader(file, database)

    # Read header
    header = reader.next()
    columns = _find_columns(header, ['person_id', 'date', 'concept_id', 'domain_id'])
    table_width = len(header)

    # Skip extra formatting lines after header
    for i in range(extra_header_lines_skip):
        reader.next()

    # Read in each row of the file
    concept_year_patient = defaultdict(lambda: defaultdict(set))
    year_patients = defaultdict(set)
    for row in reader:
        # Display progress
        if reader.line_num % 1000000 == 0:
            print reader.line_num 
            
        if len(row) == table_width:
            person_id, date_str, concept_id, domain_id = [row[i] for i in columns]
            
            # Skip when concept_id is 0
            if concept_id == '0':
                continue
            
            # Track concepts and patients by year
            # date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            # year = date.year
            year = int(date_str)
            concept_year_patient[concept_id][year].add(person_id)
            year_patients[year].add(person_id)

    # For each patient seen in each year, add the patient's demographics (race, ethnicity, gender)
    for year in year_patients:
        patients_in_year = year_patients[year]
        for person_id in patients_in_year:
            pt_info = patient_info[person_id]
            for concept_id in pt_info:
                if concept_id != '0':
                    concept_year_patient[concept_id][year].add(person_id)                     
    
    # Count how many patients in each year
    year_numpatients = defaultdict(lambda: 0)
    for year, pts in year_patients.items():
        year_numpatients[year] = float(len(pts))
    
    print "Loaded data for %d patients and %d concepts from %d rows." % \
        (len(patient_info), len(concept_year_patient), reader.line_num)

    fh.close()   
    return ConceptPatientData(concept_year_patient, year_patients, year_numpatients)
    

def load_concepts(file, database, extra_header_lines_skip=0):
    """Load concept definitions
    
    Parameters
    ----------
    file: string - Concepts data file
    database: string - Originating database. See _open_csv_reader
    extra_header_lines_skip - int - Number of lines to skip after the header
    
    Returns
    -------
    Dictionary[concept_id] -> Dictionary, keys: {concept_name, domain_id, concept_class_id}
    """
    print "Loading concepts..."
    
    # Open csv reader
    fh, reader = _open_csv_reader(file, database)

    # Read header
    header = reader.next()
    columns = _find_columns(header, ['concept_id', 'concept_name', 'domain_id', 'concept_class_id'])
    table_width = len(header)

    # Skip extra formatting lines after header
    for i in range(extra_header_lines_skip):
        reader.next()

    # Read in each row of the file
    concepts = dict()
    for row in reader:
        if len(row) == table_width:
            concept_id, concept_name, domain_id, concept_class_id = [row[i] for i in columns]
            concepts[concept_id] = {'concept_name': concept_name, 'domain_id': domain_id, 'concept_class_id': concept_class_id}
    
    print "%d concept definitions loaded" % len(concepts)
    
    fh.close()
    return concepts
    
    
def merge_concepts_years(cp_data, year_min, year_max):
    """Merge data over the specified year range
    
    Parameters
    ----------
    cp_data: ConceptPatientData
    year_min: int - First year in the range (inclusive)
    year_max: int - Last year in the range (inclusive)
    
    Returns
    -------
    ConceptPatientDataMerged
    """
    print 'Merging concepts in range %d - %d' % (year_min, year_max)
    
    # How often to display progress message
    concept_year_patient = cp_data.concept_year_patient
    n_concepts = len(concept_year_patient)
    progress_interval = round(n_concepts / 10)

    # Collect all patients for each concept across the range of years
    concepts_ranged = defaultdict(set)
    for counter, concept_id in enumerate(concept_year_patient):
        # Progress message
        if counter % progress_interval == 0:
            print '%d%%' % round(counter / float(n_concepts) * 100)
            
        pts_merged = set()
        for year, pts in concept_year_patient[concept_id].items():
            # Skip if this is not in the desired year range
            if year < year_min or year > year_max:
                continue
            
            pts_merged = pts_merged.union(pts)
            
        if len(pts_merged) > 0:
            concepts_ranged[concept_id] = pts_merged
    
    # Merge the set of all patients across the years
    year_patient = cp_data.year_patient
    pts_merged = set()
    for year, pts in year_patient.items():
        if year >= year_min and year <= year_max:
            pts_merged = pts_merged.union(year_patient[year])
    n_patients = float(len(pts_merged))
    
    print '%d concepts, %d patients' % (len(concepts_ranged), len(pts_merged))
        
    return ConceptPatientDataMerged(concepts_ranged, pts_merged, n_patients, year_min, year_max)

    
def single_concept_yearly_counts(output_dir, cp_data, randomize=True, min_count=11):
    """Writes concept counts and frequencies on an annual basis
    
    Writes results to file <output_dir>\concept_counts_yearly_<settings>.txt
    
    Parameters
    ----------
    output_dir: string - Path to folder where the results should be written
    cp_data: ConceptPatientData
    randomize: logical - True to randomize counts using Poisson (default: True)
    min_count: int - Minimum count to be included in results (inclusive, default: 11)
    """
    print "Writing single concept yearly counts..."
    
    concept_year_patient = cp_data.concept_year_patient
    year_numpatients = cp_data.year_numpatients
    
    # Generate the filename based on parameters
    randomize_str = '_randomized' if randomize else '_unrandomized'
    min_count_str = '_mincount=%d' % min_count
    filename = 'concept_counts_yearly' + randomize_str + min_count_str + '.txt'
    
    # Open csv_writer and write header
    output_file = os.path.join(output_dir, filename)
    fh, writer = _open_csv_writer(output_file)
    writer.writerow(['concept_id', 'year', 'count', 'frequency'])
    
    # How often to display progress message
    n_concepts = len(concept_year_patient)
    progress_interval = round(n_concepts / 10)

    # Write out each concept-year's count and frequency
    for counter, concept_id in enumerate(concept_year_patient):   
        # Progress message
        if counter % progress_interval == 0:
            print '%d%%' % round(counter / float(n_concepts) * 100)
            
        for year, pts in concept_year_patient[concept_id].items():
            # Exclude concepts with low count for patient protection
            npts = len(pts)        
            if npts < min_count:
                continue        
            
            # Randomize counts to protect patients
            if randomize:
                npts = numpy.random.poisson(npts)

            writer.writerow([concept_id, year, npts, npts/year_numpatients[year]])

    fh.close()
    

def single_concept_ranged_counts(output_dir, cp_ranged, randomize=True, min_count=11):  
    """Writes concept counts and frequencies observed from a year range
    
    Writes results to file <output_dir>\concept_counts_<settings>.txt
    
    Parameters
    ----------
    output_dir: string - Path to folder where the results should be written
    cp_ranged: ConceptPatientDataMerged
    randomize: logical - True to randomize counts using Poisson (default: True)
    min_count: int - Minimum count to be included in results (inclusive, default: 11)
    """
    print "Writing single concept ranged counts..."
    
    # Generate the filename based on parameters
    randomize_str = '_randomized' if randomize else '_unrandomized'
    min_count_str = '_mincount=%d' % min_count
    range_str = '_%d-%d' % (cp_ranged.year_min, cp_ranged.year_max)
    filename = 'concept_counts' + range_str + randomize_str + min_count_str + '.txt'
    
    # Open csv_writer and write header
    output_file = os.path.join(output_dir, filename)
    fh, writer = _open_csv_writer(output_file)
    writer.writerow(['concept_id', 'count', 'frequency'])
        
    # Write count and frequency of each concept    
    concept_patient = cp_ranged.concept_patient
    n_patients = cp_ranged.num_patients
    for concept_id, pts in concept_patient.items():
        # Exclude concepts with low count for patient protection
        npts = len(pts)        
        if npts < min_count:
            continue        
        
        # Randomize counts to protect patients
        if randomize:
            npts = numpy.random.poisson(npts)

        writer.writerow([concept_id, npts, npts/n_patients])

    fh.close()

    
def paired_concept_yearly_counts(output_dir, cp_data, randomize=True, min_count=11):
    """Writes paired concept counts and frequencies on an annual basis
    
    Writes results to file <output_dir>\concept_pair_counts_yearly_<settings>.txt
    
    Warning: This may produce a very large file (100+ GB) 
    
    Parameters
    ----------
    output_dir: string - Path to folder where the results should be written
    cp_data: ConceptPatientData
    randomize: logical - True to randomize counts using Poisson (default: True)
    min_count: int - Minimum count to be included in results (inclusive, default: 11)
    """
    print "Writing concept pair counts..."
    
    concept_year_patient = cp_data.concept_year_patient
    year_numpatients = cp_data.year_numpatients
    
    # Generate the filename based on parameters
    randomize_str = '_randomized' if randomize else '_unrandomized'
    min_count_str = '_mincount=%d' % min_count
    filename = 'concept_pair_counts_yearly' + randomize_str + min_count_str + '.txt'

    # Open csv_writer and write header
    output_file = os.path.join(output_dir, filename);
    fh, writer = _open_csv_writer(output_file)
    writer.writerow(['concept_id1', 'concept_id2', 'year', 'count', 'frequency'])
    
    # How often to display progress message
    n_concepts = len(concept_year_patient)
    progress_interval = round(n_concepts / 100)

    # Write out each concept-year's count and frequency
    for counter, concept_id_1 in enumerate(concept_year_patient):
        # Progress message
        if counter % progress_interval == 0:
            print '%d%%' % round(counter / float(n_concepts) * 100)
        
        for year, pts_1 in concept_year_patient[concept_id_1].items():
            n_patients_year = float(year_numpatients[year])
            
            # Skip this iteration if the single concept count is less than the minimum
            if len(pts_1) < min_count:
                continue
            
            for concept_id_2 in concept_year_patient:
                # Write each concept pair only once, i.e., include 
                # (concept1, concept2) but not (concept2, concept1)
                if concept_id_2 <= concept_id_1:
                    continue
                    
                # Skip this iteration if the single concept count is less than the minimum
                pts_2 = concept_year_patient[concept_id_2][year]
                if len(pts_2) < min_count:
                    continue
                    
                # Count the number of shared patients
                npts = len(pts_1 & pts_2)

                # Exclude concepts with low count for patient protection
                if npts < min_count:
                    continue

                # Randomize counts to protect patients
                if randomize:
                    npts = numpy.random.poisson(npts)
                
                writer.writerow([concept_id_1, concept_id_2, year, npts, npts/n_patients_year])

    fh.close()

    
def paired_concept_ranged_counts(output_dir, cp_ranged, randomize=True, min_count=11):
    """Writes paired concept counts and frequencies observed from a year range
    
    Writes results to file <output_dir>\concept_pair_counts_<settings>.txt
    
    Parameters
    ----------
    output_dir: string - Path to folder where the results should be written
    cp_ranged: ConceptPatientDataMerged
    randomize: logical - True to randomize counts using Poisson (default: True)
    min_count: int - Minimum count to be included in results (inclusive, default: 11)
    """
    print "Writing concept pair counts..."
    
    concept_patient = cp_ranged.concept_patient
    n_patients = cp_ranged.num_patients
    year_min = cp_ranged.year_min
    year_max = cp_ranged.year_max
    
    # Generate the filename based on parameters
    randomize_str = '_randomized' if randomize else '_unrandomized'
    min_count_str = '_mincount=%d' % min_count
    range_str = '_%d-%d' % (year_min, year_max)
    filename = 'concept_pair_counts' + range_str + randomize_str + min_count_str + '.txt'

    # Open csv_writer and write header
    output_file = os.path.join(output_dir, filename)
    fh, writer = _open_csv_writer(output_file)
    writer.writerow(['concept_id1', 'concept_id2', 'count', 'frequency'])
    
    # How often to display progress message
    n_concepts = len(concept_patient)
    progress_interval = round(n_concepts / 100)

    # Write out each concept-year's count and frequency
    for counter, concept_id_1 in enumerate(concept_patient):
        # Progress message
        if counter % progress_interval == 0:
            print '%d%%' % round(counter / float(n_concepts) * 100)
        
        # Skip this concept if the single concept count is less than min_count
        pts_1 = concept_patient[concept_id_1]
        if len(pts_1) < min_count:
            continue
        
        for concept_id_2 in concept_patient:
            # Write each concept pair only once, i.e., include 
            # (concept1, concept2) but not (concept2, concept1)
            if concept_id_2 <= concept_id_1:
                continue

            # Skip this concept if the single concept count is less than min_count
            pts_2 = concept_patient[concept_id_2]
            if len(pts_2) < min_count:
                continue
                
            # Count the number of shared patients
            npts = len(pts_1 & pts_2)

            # Exclude concepts with low count for patient protection
            if npts < min_count:
                continue

            # Randomize counts to protect patients
            if randomize:
                npts = numpy.random.poisson(npts)
            
            writer.writerow([concept_id_1, concept_id_2, npts, npts/n_patients])

    fh.close()
    

def quality_analysis(output_dir, cp_data, concepts, min_count=11):
    """Performs and writes the results of several basic data quality checks
    
    dq_domain_year_num_concepts.txt
    Number of unique concepts (concept_ids) in each domain per year
    
    dq_domain_year_total_counts.txt
    Sum of counts of each concept in each domain per year
    
    dq_patients_year.txt
    Number of patients observed in each year
    
    Parameters
    ----------
    output_dir: string - Path to folder where the results should be written
    cp_data: ConceptPatientData
    concepts: Concepts definitions returned from load_concepts
    min_count: int - Minimum count reported in results (inclusive, default: 11)
    """
    print 'Data quality analysis...'
    
    concept_year_patient  = cp_data.concept_year_patient
    year_patient = cp_data.year_patient
    
    # Count the number of concepts seen each year and the total count each year per domain
    domain_year_concepts = defaultdict(lambda: defaultdict(lambda: 0))
    domain_year_counts = defaultdict(lambda: defaultdict(lambda: 0))
    for concept_id in concept_year_patient:   
        domain_id = concepts[concept_id]['domain_id']
        
        for year, pts in concept_year_patient[concept_id].items():
            domain_year_concepts[domain_id][year] += 1
            domain_year_counts[domain_id][year] += len(pts)
    
    # Write out the number of concepts per year per domain
    output_file = os.path.join(output_dir, 'dq_domain_year_num_concepts.txt')
    fh, writer = _open_csv_writer(output_file)
    writer.writerow(['domain_id', 'year', 'num_concepts'])
    for domain_id, year_concepts in domain_year_concepts.items():
        for year, num_concepts in year_concepts.items():
            writer.writerow([domain_id, year, num_concepts])
    fh.close()

    # Write out the total concept count per year per domain
    output_file = os.path.join(output_dir, 'dq_domain_year_total_counts.txt')
    fh, writer = _open_csv_writer(output_file)
    writer.writerow(['domain_id', 'year', 'total_count'])
    for domain_id, year_counts in domain_year_counts.items():
        for year, total_count in year_counts.items():
            total_count = max(total_count, min_count)
            writer.writerow([domain_id, year, total_count])
    fh.close()
    
    # Write out the number of patients per year
    output_file = os.path.join(output_dir, 'dq_patients_year.txt')
    fh, writer = _open_csv_writer(output_file)
    writer.writerow(['year', 'num_patients'])
    for year, pts in year_patient.items():
        count = max(len(pts), min_count)
        writer.writerow([year, count])
    fh.close()
    
    return
