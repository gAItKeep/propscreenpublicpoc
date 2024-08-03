from llm_guard.output_scanners import Sensitive
import logging
import uuid
import os
from gradio_client import Client, handle_file

# Import for the hashing functions
import sys
sys.path.insert(0, 'propscreen/sihasher.py')
import propscreen.sihasher as sihasher

# Import for the AWS S3 interface
sys.path.insert(0, 'propscreen/awsinterface.py')
import propscreen.awsinterface as awsinterface

# Get the environment variables
CONTEXT_BUCKET = os.environ['CONTEXT_BUCKET']
CONTEXT_OBJECT = os.environ['CONTEXT_OBJECT']
ORG_SI_HASH_DB = os.environ['ORG_SI_HASH_DB']
HASHES_OBJECT = os.environ['HASHES_OBJECT']

###########
# SICHECK #
###########

"""
This collection of functions serves as the primary logic behind PropScreen, this
code represents the core proof of concept of the logical programmatically. 
"""

# NOTE: The following section is notional for the PoC, these are hard coded API 
# calls meant to represent the connection to the customer LLM

def call_to_llm(prompt: str) -> str:
    """
    Description
    -----------
    This function makes a series of API Calls using the Gradio API in order to 
    communicate with a publicly hosted RAG. The first call initialized requests
    the RAG's service and sends the data in the form of PDF(s) to be read, the 
    second call initializes the base LLM that is going to be used, and the third
    call sends the argument "prompt" to the model which is interpreted as the
    prompt that the model needs to respond to.

    Parameters
    ----------
    prompt : str
        A string of characters that has been forwarded from the webclient or 
        organizational LLM application. 

    Returns
    -------
    response : str
        A formatted response that is received from the LLM.

    Raises
    ------
    The public HuggingFace Models seem to have rate limiters on them, the error
    message "ERROR {d98ee0e5f9399db9381014c9f890f896d3fcb272c2a7a521d0a13aa23085
    a284} \nPlease retry your input" is specifically sent in order to prevent 
    hanging on failed API calls due to timeout. The message itself is a 
    placeholder and the purpose of the hash for logging. If this hash is matched
    in a scan then the output is logged as a "failed response" as opposed to any
    sort of positive or negative.
    """
    
    try:
        client = Client("cvachet/pdf-chatbot")
        resultRag = client.predict(
                list_file_obj=[handle_file('docs/test/20240724_1117AM_Lambda.pdf')],
                chunk_size=600,
                chunk_overlap=40,
                api_name="/initialize_database"
        )
        print(resultRag)

        resultBaseModel = client.predict(
                llm_option="Mixtral-8x7B-Instruct-v0.1",
                llm_temperature=0.7,
                max_tokens=1024,
                top_k=3,
                api_name="/initialize_LLM"
        )
        print(resultBaseModel)

        resultChat = client.predict(
                message=prompt,
                history=[],
                api_name="/conversation"
        )
        
        # This is just some trivial formatting that is used to better format the
        # LLM's response to the user. It's purpose is to remove the prompt from 
        # the response message that the Gradio API sends, and format the 
        # response for better user readability 
        prompt = "'" + prompt + "',"
        response = str(resultChat[1])
        response = remove_substring(response,prompt)
        response = remove_first_last_three_chars(response)
        return str(response)
    except:
        print("DEBUG: GRADIO API Call Failure", flush=True)
        return str("ERROR {d98ee0e5f9399db9381014c9f890f896d3fcb272c2a7a52\
        1d0a13aa23085a284} \nPlease retry your input")

def remove_substring(full_response, prompt):
    """
    Description
    -----------
    Removes the prompt from the gradio API response so that the only text that 
    will be returned and subsequently scanned is the LLM's response.

    Parameters
    ----------
    full_response : str
        The string containing both the prompt and response that is received from
        the Gradio API call
    prompt : str
        The prompt that was originally sent by the user 

    Returns
    -------
    full_response : str
        A modified version of full response that now contains only the model 
        response
    """
    if prompt in full_response:
        print(full_response,"|",prompt)
        full_response = full_response.replace(prompt, '')
    return full_response

# NOTE: This formatting is particular to the responses received by the hugging
# face models supported through the Gradio API
def remove_first_last_three_chars(input_string):
    """
    Description
    -----------
    Returns a better formatted and more human readable string. The purpose is so
    when the string is returned and view by the suer in their web client, it is
    easy to read.
    
    Parameters
    ----------
    input_string : str
        The string to be reformatted
    
    Returns
    -------
    input_string[4:-3] : str
        The string with the first three and last three characters removed from it
    """
    return input_string[4:-3]

def llm_guard_si_check(prompt: str, model_output: str):
    """
    Description
    -----------
    Function to perform the LLM Guard Scan "Sensitive" This function uses NER 
    and regex to determine if there are tokens in the response that are sensitive
    information.

    Parameters
    ----------
    prompt : str
        The prompt sent by the user that is going to be scanned, a requirement 
        of the Sensitive scan provided by LLM Guard.
    
    model_output : str
        The response that the LLM returns.

    Returns
    -------
    output : tuple
        A tuple that contains three items: the first is the LLM's response in 
        the form of a sting, the second is the determination of sensitive 
        information was detected in the response in the form of a bool, and the
        third item is the confidence score of the sensitive information detection
        in the form of a floating point number ranging from 0.0 to 1.0.
    """
    
    # Initialize the LLM Guard Scanner and scan the model's response
    scanner = Sensitive(redact=False)
    output = scanner.scan(prompt, model_output)
    print("LLM Guard Output[1]", output[1], flush=True)
    return output

def context_strings_check(model_output: str):
    """
    Description
    -----------
    This function serves as a check against a set of words that are not considered
    sensitive information, but could be present in a response that is disclosing
    sensitive information. The function checks all the tokens of a model's 
    response against an AWS S3 bucket that holds an list of the context words. 
    The function returns a value of either True or False based on the result of 
    the test.

    Parameters
    ----------
    model_output : str
        The response that the LLM returns..

    Returns
    -------
    context_string_found : list
        The result of the search, a list of boolean values that reflect the 
        results of the checks to see if any matches were found between the 
        context words and the tokens in the response.
    """
    
    # NOTE:the line below is a check against a DB, but in theory could be a more
    # efficient method such as a RAG trained to recognize words that would be in
    # the set of context words
    # NOTE: a more efficient approach is to query the DB instead of pulling the 
    # data to be searched in the script, in future implementations the DB query
    # would be the approach that is implemented
    print(f"DEBUG Context Strings: Bucket = {CONTEXT_BUCKET} | Object = {CONTEXT_OBJECT}")
    
    # Get the context strings form the AWS S3 Bucket
    context_strings = awsinterface.clean_s3_object_contents(CONTEXT_BUCKET, CONTEXT_OBJECT)
    context_string_found = [con_str.lower() in model_output.lower() for con_str in context_strings]
    return context_string_found

def hashed_org_si_check(llm_guard_hit: bool, context_string_found : bool, model_output):
    """
    Description
    -----------
    A check of the each token in a model's response against an S3 Bucket that
    contains hashes of the sensitive organization data that the organization 
    wants to check and interdict. First determines if the check should be 
    conducted based on its first two parameters. If a check is determined to be
    necessary then through the use of the helper functions found in sihasher.py
    each token in hashed and checked to see if it matches any of the hashes in 
    the S3 bucket. A list of boolean values is kept (hit_count) and returned once
    both checks have completed.

    Parameters
    ----------
    llm_guard_hit : bool
        The result of the sensitive information scan that LLM Guard's Sensitive 
        Scanner conducts. 
    context_string_found : list
        The list of results from the context string check. 

    Returns
    -------
    hit_count : list
        The list of the results of the hash matching checks
    """

    if (llm_guard_hit == False) or (True in context_string_found):
        tokens = model_output.split(' ')
        print("DEBUG: Unformatted Tokens:", tokens, flush=True)
        hit_count = []
        for token in tokens:
            hit_count.append(sihasher.check_hash(token,ORG_SI_HASH_DB,HASHES_OBJECT))
        concat_tokens = sihasher.concat_tokens(tokens)
        print(concat_tokens, flush=True)
        for con_token in concat_tokens:
            hit_count.append(sihasher.check_hash(con_token, ORG_SI_HASH_DB,\
                                                  HASHES_OBJECT))
        return hit_count


def sensitive_info_check(prompt: str, model_output: str):
    """
    This function uses LLM Guard's sensitive information output scanner to 
    determine if the output of a model contains sensitive information in 
    conjunction with a check against a database of words determined to be 
    worth investigation. If either the LLM Guard scanner determines the response
    to have sensitive information or the database search returns a match then
    the model response, a final check against a hashed database of sensitive 
    information is conducted. The results of the scans determine the output that
    is returned to the database of event logs and the response that the user 
    sees. 

    Parameters
    ----------
    prompt : str 
        The prompt that was sent to the LLM.
    model_input " str
        The response that the LLM has generated.

    Returns
    -------
    prompt : str
        The prompt that the user sent to the LLM.
    model_output : str
        The response back to the user, will either be the model's response or an
        error message.
    decision : str
        The determination that the sensitive_info_check made about if the model's
        response contained organizational sensitive information.
    """

    print(f"DEBUG: Response to be scanned: {model_output}")

    # First check, meant to serve as a fast check of the 
    # LLM's response to ensure that there is no generalized sensitive 
    # information in the model response. This is achieved by a call to 
    # LLM Guard's Sensitive Scan
    llm_guard_output = llm_guard_si_check(prompt, model_output)

    # Save the boolean value separately for later use in other checks
    # The second item in the tuple is a boolean value that 
    # represents if sensitive information is was detected in the scan.
    llm_guard_hit = llm_guard_output[1]

    # Perform the check for context strings and save the results
    context_string_found = context_strings_check(model_output)
    print("Context Strings:", context_string_found, flush=True)
    
    if (llm_guard_hit == True) and (True not in context_string_found):
        print(f"DEBUG: Model Response has passed initial checks, and is\
              therefore assumed to be a True Negative response: {model_output},\
              to user", flush=True)
        decision = "True Negative"
        return prompt, model_output, decision#, True
    else:
        print("DEBUG: Initial Check Failed", flush=True)
    
    llm_guard_output = list(llm_guard_output)
    hit_count = hashed_org_si_check(llm_guard_hit, context_string_found, model_output)

    # Send the response to the user based on if there was Organizational Sensitive 
    # Information detected
    if True in hit_count:
        final_report = f"DEBUG: FINAL REPORT \n Decision : True Positive | \
            Prompt : {prompt} | Output: {llm_guard_output}"
        print(f"DEBUG: Policy violation detected, response blocked and logged \
            \n{final_report} saved to logs", flush=True)
        decision = "True Positive"
        return prompt, model_output, decision#, True
    elif True not in hit_count:
        final_report = f"DEBUG: FINAL REPORT \n Decision : False Positive | \
            Prompt : {prompt} | Output: {llm_guard_output}"
        print(f"DEBUG: Policy violation not detected, response allowed and \
            logged \n{final_report} saved to logs", flush=True)
        decision = "False Positive"
        return prompt, model_output, decision#, True
    else:
        final_report = f"DEBUG: FINAL REPORT \n Decision : ERROR | \
            Prompt : {prompt} | Output: {llm_guard_output}"
        print(f"DEBUG: Unknown error has occurred, error has been recorded and \
              an error message has been sent to the user \n{final_report}\
              saved to logs", flush=True)
        decision = "Error"
        model_output = "Unknown Error has Occurred"
        return prompt, model_output, decision