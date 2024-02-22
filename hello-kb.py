'''
https://github.com/aws-samples/amazon-bedrock-samples/blob/main/knowledge-bases/1_managed-rag-kb-retrieve-generate-api.ipynb
'''

import boto3
import json
import numpy as np

import pprint
from botocore.client import Config

pp = pprint.PrettyPrinter(indent=2)

bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client("bedrock-agent-runtime",
                              config=bedrock_config)

#model_id = 'anthropic.claude-instant-v1' # try with both claude instant as well as claude-v2. for claude v2 - "anthropic.claude-v2"
model_id = 'anthropic.claude-v2'

region_id = "us-west-2" # replace it with the region you're running sagemaker notebook


kb_id = "XCCECUI94P"   #OpenSearch Serverless
#kb_id="WCK7HE4CFO"  #pinecone

def retrieveAndGenerate(input, kbId, sessionId=None, model_id = "anthropic.claude-instant-v1", region_id = "us-east-1"):
    model_arn = f'arn:aws:bedrock:{region_id}::foundation-model/{model_id}'
    if sessionId:
        return bedrock_agent_client.retrieve_and_generate(
            input={
                'text': input
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kbId,
                    'modelArn': model_arn
                }
            },
            sessionId=sessionId
        )
    else:
        return bedrock_agent_client.retrieve_and_generate(
            input={
                'text': input
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kbId,
                    'modelArn': model_arn
                }
            }
        )



print ("Hello KB!")


#query = "How long has Todd Pond, AWS Director of Strategic Sales, been working in the tech industry?"
query = "Why did AWS acquire Annupura Labs?"
#query = "What is the title of the AWS reThink episode where Todd Pond tells us how long he has been working in tech?"

print ("Query: "+ query + "\n")


response = retrieveAndGenerate(query, kb_id,model_id=model_id,region_id=region_id)
#print("Reponse:")
#print(response)

print("\n")
generated_text = response['output']['text']
print ("Query Response:")
pp.pprint(generated_text)
print ("\n")


chunk_text = response['citations'][0]['retrievedReferences'][0]['content']['text']

f = open("chunk_text.txt", "w")
f.write(chunk_text)
f.close()

#output = "\n" + chunk_text
#print(output)


#Find Start Time


def find_start_time(chunk_text, dict):
    print("finding the start time...")
    start_time ="0:00"

    items = dict["results"]["items"]

    for key in items:

        token = key['alternatives'][0]['content']
        #print(token)

        if 'start_time' in key.keys():   #punctuations don't have start_time
            start_time = key['start_time']

        #print(start_time)

    f = open("start_times.json", 'w')
    output = items
    #output = items['alternatives'][0]['content']
    json.dump(output,f)
    f.close()
    #print(output)



transcript_file = response['citations'][0]['retrievedReferences'][0]['location']['s3Location']['uri']
filename = 'AI-Accelerators.json'



#print ("\nLocation:\n")
f = open(filename)
dict  = json.load(f)
f.close()


transcript_text = dict['results']['transcripts'][0]['transcript']
f = open("transcript_text.txt", "w")
f.write(transcript_text)
f.close()


print("find start time for chunk:")
print(chunk_text)
pos = transcript_text.find(chunk_text)
#print(pos)

#print(transcript_text[8])
#print(len(transcript_text))

#print(dict)
#find_start_time(chunk_text,dict)


#Initialize Array of Start Time for Each Character Position

transcript_length = len(transcript_text)
start_times = []
start_time = "0.00"
for i in range(transcript_length):
    
    start_times.append(start_time)
    #print(str(i) + ": " + start_times[i])

start_times_np = np.array(start_times)
#print(start_times_np)



character_count = 0
items = dict["results"]["items"]
for key in items:

    token = key['alternatives'][0]['content']
    type = key['type']

  

    token_length = len(token)

    if (type == 'pronunciation'):       
        start_time = key['start_time']
        #print("character_count: " + str(character_count))
        start_times_np[character_count] = start_time
        #start_times = np.assign(start_times, character_count, start_time)
        #print("setting start time! "+ str(character_count)+ " " + start_times[character_count])
    
    if (character_count < 200):
        print(type + " " + str(character_count)+ ": " +token  + " "+ start_time)    

    if ((character_count + token_length + 1) <= transcript_length):
        character_count = character_count + token_length + 1

    if (type=='punctuation'):
        character_count = character_count - 1   



for i in range(20):
    print(str(i) + ": " + start_times_np[i])


#print("setting start time! "+ str(character_count)+ " " + start_times[character_count])  





#print(start_times)
#chunk_start_time = start_times[pos]

#print("chunk start time: " + chunk_start_time)

f = open("start_times.json", 'w')
output = items
#output = items['alternatives'][0]['content']
json.dump(output,f)
f.close()
#print(output)






