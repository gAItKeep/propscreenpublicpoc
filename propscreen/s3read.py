import boto3

def process_list(lst):
    for i in range(len(lst)):
        # Remove leading and trailing single quotes
        lst[i] = lst[i].strip("'")
        # Split the string into a list of values
        lst[i] = lst[i].split(',')
    return lst

def read_s3_bucket(bucket_name) -> list:
    # Create a session using your AWS credentials
    s3 = boto3.resource('s3')

    # Access the bucket
    bucket = s3.Bucket(bucket_name)

    s3_data = []
    """"
     # Iterate over the objects in the bucket
    for obj in bucket.objects.all():
    # Get the object
        file_content = obj.get()['Body'].read().decode('utf-8')
        s3_data.append(file_content)
    """
    count = 1 #Numerical counting for the user
    for obj in bucket.objects.all():
        
        # Get the object from S3
        response = obj.get()
    
        # Read the contents of the file and print it
        file_content = response['Body'].read().decode('utf-8')
        print("Record ", count, ": " + str(file_content), "\n")
        count = count + 1
   

    s3_data = str(s3_data)
    s3_data = s3_data.split('\\r\\n')
    for item in s3_data:
        print(item, "\n\n")
    print(type(s3_data), len(s3_data))
    clean_list = process_list(s3_data)
    for item in clean_list:
        print(item, "\n\n")
    return clean_list

print(read_s3_bucket('uniquebucketforreports'))