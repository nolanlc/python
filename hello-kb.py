'''
https://github.com/aws-samples/amazon-bedrock-samples/blob/main/knowledge-bases/1_managed-rag-kb-retrieve-generate-api.ipynb
'''

import boto3
import json

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


query = "How long has Todd Pond, AWS Director of Strategic Sales, been working in the tech industry?"
#query = "Why did AWS acquire Annupura Labs?"
#query = "What is the title of the AWS reThink episode where Todd Pond tells us how long he has been working in tech?"

print ("Query: "+ query + "\n")


response = retrieveAndGenerate(query, kb_id,model_id=model_id,region_id=region_id)
print("Reponse:")
print(response)

print("\n")
generated_text = response['output']['text']
print ("Query Response:")
pp.pprint(generated_text)
print ("\n")


chunk_text = response['citations'][0]['retrievedReferences'][0]['content']['text']

output = "\n" + chunk_text
print(output)


#Find Start Time


def find_start_time(chunk_text, dict):
    print("finding the start time...")

    output = dict["results"]["items"]
    for key in output:

        token = key['alternatives'][0]['content']

        start_time =""
        start_time = key['start_time']


        print(token + " "+ start_time)

    f = open("a.json", 'w')
    json.dump(output,f)
    f.close()
    #print(output)



transcript_file = response['citations'][0]['retrievedReferences'][0]['location']['s3Location']['uri']
filename = 'AI-Accelerators.json'

print ("\nLocation:\n")
f = open(filename)
dict  = json.load(f)
f.close()
print(dict)

find_start_time(chunk_text,dict)










