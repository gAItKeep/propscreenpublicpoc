import boto3

def get_s3_object_contents(bucket_name, object_key):
    # Initialize the S3 client
    s3 = boto3.client('s3')

    # Get the object
    response = s3.get_object(Bucket=bucket_name, Key=object_key)

    # The entries of the object are in the 'Body' of the response
    entries_in_bytes = response['Body'].read()

    # Decode the bytes to string and split it into a list
    entries = entries_in_bytes.decode('utf-8').split('\n')

    return entries

# Specify the bucket and object key
bucket_name = 'fakeorgsi'
object_key = 'fakedata.csv'

# Get the entries
def clean_s3_object_contents(bucket_name, object_key):
    entries = get_s3_object_contents(bucket_name, object_key)

    divied_data = []

    for item in entries:
        temp = item.split(',')
        temp = item.split('\r')
        print(temp)
        divied_data.append(temp)

    final_list = []
    for inner_list in divied_data:
        final_list.extend(inner_list)


    true_final_list = []
    for item in final_list:
        temp = item.split(',')
        true_final_list.append(temp)

    really_the_final_list = []
    for inner_list in true_final_list:
        really_the_final_list.extend(inner_list)

    print(entries)
    print(divied_data)
    print(final_list)
    print(true_final_list)
    print(really_the_final_list)
    return really_the_final_list