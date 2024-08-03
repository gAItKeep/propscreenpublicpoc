import boto3
from botocore.exceptions import ClientError

def get_s3_object_contents(bucket_name, object_key) -> list:
    """
    Description
    -----------
    
    Gets the entries in an S3 object, decodes them, and formats them into a list
    that is returned

    Parameters
    ----------
    bucket_name : str
        The name of the AWS S3 Bucket that the target object resides in
    object_key : str
        The name of the particular object that is going to be read 

    Returns
    -------
    entires : list
        The list of all the individual elements of the S3 object
    """
    # Initialize the S3 client
    s3 = boto3.client('s3')

    # Get the object
    response = s3.get_object(Bucket=bucket_name, Key=object_key)

    # The entries of the object are in the 'Body' of the response
    entries_in_bytes = response['Body'].read()

    # Decode the bytes to string and split it into a list
    entries = entries_in_bytes.decode('utf-8').split('\n')

    return entries

def clean_s3_object_contents(bucket_name, object_key):    
    """
    Cleans and formats the data of a CSV S3 object to be read 

    Parameters
    ----------
    bucket_name : str
        The name of the S3 bucket that is going to be accessed
    object_key : str
        The name of the S3 object that is going to be accessed
    Returns
    -------
    really_the_final_list : list
        The of the items of the S3 bucket
    """
    entries = get_s3_object_contents(bucket_name, object_key)

    divided_data = []

    for item in entries:
        temp = item.split(',')
        temp = item.split('\r')
        divided_data.append(temp)

    final_list = []
    for inner_list in divided_data:
        final_list.extend(inner_list)


    true_final_list = []
    for item in final_list:
        temp = item.split(',')
        true_final_list.append(temp)

    really_the_final_list = []
    for inner_list in true_final_list:
        really_the_final_list.extend(inner_list)

    really_the_final_list = list(filter(None,really_the_final_list))

    return really_the_final_list

def add_entry_to_s3_bucket(bucket_name, file_name, data) -> bool:
    """
    adds a record to the S3 bucket specified in the first argument, this record
    consists of a name specified by the second argument and the data populating 
    the body of the record is provided by the third argument

    Parameters
    ----------
    bucket_name : str
        The name of the S3 Bucket that is currently deployed and will be
        receiving the entry
    file_name : str
        The name of the file that will be transmitted to the S3 Bucket
    data : str
        The output generated from the report that will be saved inside of the
        new entry

    Returns
    -------
    bool
        a value used to denote the success of the operation

    Raises
    ------
    No direct error raising, but a return of False is meant to denote failure in
    the call
    """
    try:
        s3 = boto3.resource('s3')
        s3.Bucket(bucket_name).put_object(Key=file_name, Body=data)
        return True
    except:
        return False