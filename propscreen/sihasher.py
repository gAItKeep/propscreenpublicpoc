import boto3
import hashlib

############
# SIHASHER #
############
"""
sihasher is a set of functions whose purpose is to conduct the hashing of the 
tokens that are present in the LLM's response and perform a check of those 
tokens against the hashes of the sensitive information.
"""

def check_hash(token: str, bucket_name: str, object_key: str) -> bool:
    """
    Description
    -----------
    Hashes the token and checks the hashed token against the array of hashed
    sensitive information. The function then checks if the hash exists inside 
    the loaded list of the hashes. 
    
    Parameters
    ----------
    token : str 
        A token taken from the LLM response
    bucket_name : str
        The name of the AWS S3 bucket that will be accessed
    object_key : 
        The name of the S3 object that will be accessed, this object should be
        where the list of hashes is stored
    
    Returns
    -------
    A boolean value that is determined depending on if the hashed value of the
    exists inside the array of hashed values
    """
    
    # Trivial formatting of the token
    token = token.strip(",<>./?!'}{][|")
    token = token.replace('"','')

    # Hashes the token 
    encoded_token = bytes(token, 'utf-8')
    token_hash = hashlib.sha256(encoded_token).hexdigest()

    # Call helper function to get the hashed data
    hash_si_list = list_s3_objects(bucket_name, object_key) 

    try:
        #print("DEBUG: hash check findings, ", token_hash in hash_si_list, flush=True)
        return token_hash in hash_si_list
    except Exception as e:
        print(f"Error: {str(e)}")

def list_s3_objects(bucket_name, object_key):
    """
    Description
    -----------
    Reads and formats all contents of an object in an AWS S3 bucket and stores 
    those contents in a list that is returned. In this circumstance specifically 
    it will be a list of hashes that will be checked against a tokens in an 
    LLM's response.
    
    Parameters
    ----------
    bucket_name : str
        The name of the AWS S3 bucket that will be accessed
    object_key : 
        The name of the S3 object that will be accessed, this object should be
        where the list of hashes is stored

    Returns
    -------
    si_hashes : list
        The list of all the hashes, properly formatted
    """
    try:
        # Initialize the Boto3 S3 client
        s3_client = boto3.client('s3')

        # List all objects in the specified prefix
        csv_obj = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')
        
        csv_string = csv_string.replace("\n", "").replace("\r", "").replace("\ufeff", "")
        si_hashes = csv_string.split(',')

        # NOTE: What would be beneficial here for robustness, but detrimental to
        # performance would be a validation mechanism to ensure that all the 
        # data in the list are valid SHA 256 Hashes 
        
        return (si_hashes)
    
    except Exception as e:
        print(f"Error: {str(e)}")

def concat_tokens(tokens: list) -> list:
    """
    Description
    -----------
    Concatenates adjacent items in a list. This function is meant to increase 
    range of hashes that are checked against the list of hashes in the S3 bucket

    Arguments
    ---------
        my_list : list
            The input list, will be the array of tokens from the LLM's response

    Returns:
        concatenated_list : list
            List of items where each item is the token concatenated with the 
            and empty space and the subsequent token
    """
    concatenated_list = []
    for i in range(len(tokens) - 1):
        temp = tokens[i] + " " + tokens[i + 1]
        temp = str(temp)
        # Trivial sanitization of the tokens 
        temp = temp.strip(",<>./?!'}{][|")
        temp = temp.replace('"','')
        concatenated_list.append(temp)
    return concatenated_list