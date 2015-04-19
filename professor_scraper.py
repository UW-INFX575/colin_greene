

import requests
import lxml
from lxml import etree
from lxml import html
import pandas as pd
import re
import time
import json
import numpy as np
import csv

def get_site_html(url):
    source = requests.get(url).content
    return source

def get_tree(url):
    source = get_site_html(url)
    tree = etree.HTML(source)
    return tree

# Function removes \r, \n, and \t from a string
def remove_special_characters(string):
    return re.sub('[\r\n\t]', '', string)

print "Pulling from UMN Dentistry."
# Site contains list of all faculty at the University of Minnesota school of dentistry
umn_url = get_tree('http://www.dentistry.umn.edu/faculty-staff/bios/alphabetical/index.htm')

base_path = 'http://www.dentistry.umn.edu/'

# List of url endings to add to the base path. 
partial_faculty_url = umn_url.xpath('//span[@class="list_bio_name"]/a/@href')

# Add the url extensions to the base path. Each corresponds to an individual faculty page.
complete_faculty_urls = []
for url in partial_faculty_url:
    complete_url = re.sub(r'../../../', base_path, url)
    complete_faculty_urls.append(complete_url)

# Create an xpath for each of the degree levels. 
base_xpath = "//div[@class='span33 bio_page_container']/p/text()[preceding::strong[contains(text(),"
phd_xpath = base_xpath + "'Ph.D.')]]"
dmd_xpath = base_xpath + "'DMD/DDS')]]"
masters_xpath = base_xpath + "'Master')]]"
bachelors_xpath = base_xpath + "'Bachelor')]]"

umn_array = []
for url in complete_faculty_urls:

    temp_url = get_tree(url)
    
    # This list contains all tags on the page that correspond to the degrees held by the professor.
    # E.g. Ph.D. will only appear in this list if the prof has a Ph.D. 
    list_of_title_headers = temp_url.xpath('//div[@class="span33 bio_page_container"]/p//strong/text()')
    
    # Variable to store the professor's degree. Initialize with not listed. 
    # It will only be replaced if one is listed. 
    degree = 'Not Listed'
    
    # Get the first and last name of the faculty.
    name = temp_url.xpath("//h3[@class='content_title']/text()")[0].split()
    first_name = name[0]
    last_name = name[-1]
    
    # Extract information about highest degree (contains school info and graduation date)
    if 'Ph.D.' in list_of_title_headers:
        degree = temp_url.xpath(phd_xpath)[0]
    elif 'DMD/DDS' in list_of_title_headers:
        degree = temp_url.xpath(dmd_xpath)[0]
    elif "Master's" in list_of_title_headers:
        degree = temp_url.xpath(masters_xpath)[0]
    elif "Bachelor's" in list_of_title_headers:
        degree = temp_url.xpath(bachelors_xpath)[0]
    
    # Extract graducation date corresponding to highest degree.
    date = re.findall('(?<=\d{4}-)?\d{4}',remove_special_characters(degree))
    
    # Replace empty values with 'Not Listed'
    if len(date) != 1:
        date = ['Not Listed']    
    
    # Extract the degree granted e.g. Ph.D, MA, etc...
    degree_granted = re.findall("[DDSTrMPHhd.E]{3,7}|[BM]+\.*[AS]+\.*", degree)
    
    # Replace blank values with "Not Listed"
    if len(degree_granted) != 1:
        degree_granted = ['Not Listed']
    
    # Extract the university or school
    degree_university = re.findall("Not Listed|[^,\d]*(?:University|School|Universidad|Univ\.|Institute|Institutet|College)[^\d,]*", remove_special_characters(degree))
    
    # Extract first (and only) value from the degree list
    date = date[0]
    degree_granted = degree_granted[0]
    degree_university = degree_university[0]
    
    umn_array.append([first_name, last_name, degree_granted, degree_university, date])

umn_array = np.array(umn_array)

# Remove lines with 'Not listed'
cleaned_umn_array = []
for line in umn_array:
    if 'Not Listed' not in line:
        cleaned_umn_array.append(line)

# Convert to data frame
umn_df = pd.DataFrame(cleaned_umn_array)
umn_df.columns = ['firstname', 'lastname', 'title', 'grad_school', 'grad_year']

# Add columns for school name and school code
umn_df['school_of_employment'] = 'University of Minnesota, Twin Cities'
umn_df['school_of_employment_code'] = 186

print "Finished with UMN Dentistry. Moving on to ASU Law."

# Site contains list of all faculty at the Arizona State University law school
asu_law_url = get_tree('http://apps.law.asu.edu/Apps/Faculty/FacultyIndex.aspx?type=allfaculty')

# Remove lines of special characters  
asu_names = [name for name in map(remove_special_characters, asu_law_url.xpath('//td/text()')) if len(name) > 0]

# Split into last and first name and then reverse the order
asu_names = map(lambda x: [x.split(',')[1], x.split(',')[0]], asu_names)

base_asu_url = 'http://apps.law.asu.edu/Apps/Faculty/'
asu_endings = asu_law_url.xpath('//a[@class="FacIndex"]/@href')

# Add the url endings to the base path. Each corresponds to an individual ASU Law faculty member's page.
asu_faculty_urls = []
for ending in asu_endings:
    asu_faculty_urls.append(base_asu_url + ending)

asu_faculty_details = []
for url in asu_faculty_urls:
    
    tree = get_tree(url)
    
    # Education_list is a list of all degrees along with the corresponding school and graduation date, if available
    education_list = tree.xpath("//span[@id='LblEducation']/text()")
    
    # Convert the list to a single string to make it easier to determine 
    # what is the highest degree held by the professor
    education_list_string = '/'.join(education_list)
    
    # Extract information for all PhDs and JDs, otherwise
    if re.search('[Ph]{2}\.*D\.*', education_list_string):
        degree_title = re.findall('[Ph]{2}\.*D\.*', education_list_string)
        degree_school = re.findall('[Ph]{2}\.*D\.*,?([^/()\d]+)',education_list_string)
        degree_year = re.findall('[Ph]{2}\.*D\.*[^/]*(\d{4})/?',education_list_string)
    elif re.search('J\.*D\.*', education_list_string):
        degree_title = re.findall('J\.*D\.*', education_list_string)
        degree_school = re.findall('J\.*D\.*,?([^/()\d]+)', education_list_string)
        degree_year = re.findall('J\.*D\.*[^/]*(\d{4})/?', education_list_string) 
    else:
        # If not a PhD or JD, set all three variables equal to an empty string
        degree_title=degree_school=degree_year=['']
    
    # Convert each list variable to a string
    degree_title = ''.join(degree_title)
    degree_school = ''.join(degree_school)
    degree_year = ''.join(degree_year)
    
    # Additional cleaning. Remove info about honors from school listing.
    degree_school = re.sub('[magnasu]*\scum\slaude,?\s?', '', degree_school)
    
    # Remove comma, space, or comma space from the end of the string
    degree_school = degree_school.rstrip(', | |,')

    asu_faculty_details.append([degree_title, degree_school, degree_year])

# Combine asu faculty names and details into single array
asu_array = np.hstack([asu_names, asu_faculty_details])

# Replace empty strings with nan
asu_array[asu_array == ''] = 'nan'

# Drop all rows with nan values in the degree granting school column
cleaned_asu_array = asu_array['nan' != asu_array[:,3]]

# Convert array to pandas data frame
asu_df = pd.DataFrame(cleaned_asu_array)

# Assign column names to the data frame
asu_df.columns = ['firstname', 'lastname', 'title', 'grad_school', 'grad_year']

# Add columns for school name and school code
asu_df['school_of_employment'] = 'Arizona State University'
asu_df['school_of_employment_code'] = 23

print 'Finished with ASU Law. Cleaning dataframe.'
# Create final data frame containing entries from UMN and ASU.
final_df = umn_df.append(asu_df, ignore_index=True)

# Strip spaces from beginning and end of each grad school
final_df.grad_school = map(lambda x: x.strip(' '), final_df.grad_school)

# Replace nan with None
final_df = final_df.replace({'nan': None})

# Import file containing mapping of schools to code
schools = pd.read_excel('schools.xls')

# Find if any of the grad schools where faculty got their degrees can be found in 
# the schools table, and append the code to the dataframe. 
school_code = []
for grad_school in final_df.grad_school:
    internal_school = None
    for name in schools.name:
        if name in grad_school:
            internal_school = int(schools[schools.name == name].id)
        
    school_code.append(internal_school)

# Create column for grad school code
final_df['grad_school_code'] = school_code

# Save a copy of csv file to current working directory
final_df.to_csv('professors.csv', encoding = 'utf-8', index=False)

print "professors.csv saved to current working directory"

