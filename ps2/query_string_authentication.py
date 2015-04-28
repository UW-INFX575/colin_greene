from boto.s3.connection import S3Connection

# Keys
access_key = 'insert_key_here'
secret_key = 'insert_secret_key_here'

# Create a connection to S3 using the keys from above
conn = S3Connection(
        aws_access_key_id = access_key,
        aws_secret_access_key = secret_key,
        is_secure=False
        )

# Access bucket called colin-greene
bucket = conn.get_bucket('colin-greene') 

# Store path to the desired file
unigram_summary = 'ngramcounts/all_unigrams.csv' 

# Generate a key for the file 
key = bucket.get_key(unigram_summary) 

# URL that makes link available for 24 hours
url = key.generate_url(86400) 

print url