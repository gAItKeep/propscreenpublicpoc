import boto3

def list_s3_buckets():
    s3 = boto3.client('s3')
    response = s3.list_buckets()

    # Output the bucket names
    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')

list_s3_buckets()

def read_s3_bucket(bucket_name):
    # Create a session using your AWS credentials
    s3 = boto3.resource('s3')

    # Access the bucket
    bucket = s3.Bucket(bucket_name)

    # Iterate over the objects in the bucket
    for obj in bucket.objects.all():
        # Get the object
        file_content = obj.get()['Body'].read().decode('utf-8')

        # Print out the file content
        print('File name: ', obj.key)
        print('File content: ', file_content)

# Call the function
read_s3_bucket('uniquebucketforreports')

def add_entry_to_s3_bucket(bucket_name, file_name, data):
    # Create a session using your AWS credentials
    s3 = boto3.resource('s3')

    # Add the entry to the bucket
    s3.Bucket(bucket_name).put_object(Key=file_name, Body=data)

# Call the function
#add_entry_to_s3_bucket('uniquebucket8964', 'testfile2', 'test 456')
