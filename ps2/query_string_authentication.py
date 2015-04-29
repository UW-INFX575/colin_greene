from boto.s3.connection import S3Connection

# Import keys into a dict from txt document
amazon_keys = {}
with open('../keys.txt', 'r') as f:
        for line in f:
            line = line.strip()
            splitLine = line.split(',')
            amazon_keys[splitLine[0]] = splitLine[-1]


# Create a connection to S3 using the keys from above
conn = S3Connection(
        aws_access_key_id = amazon_keys['access_key'],
        aws_secret_access_key = amazon_keys['secret_key'],
        is_secure=False
        )

# Access bucket called colin-greene
bucket = conn.get_bucket('colin-greene') 

# Store path to the desired file
unigram_summary = 'ngramcounts/all_unigrams.csv' 

# Generate a key for the file 
key = bucket.get_key(unigram_summary) 

# URL that makes link available for 3 weeks
url = key.generate_url(86400*21) 

f = open('protected_url.txt', 'w')

f.write(url)
f.close()