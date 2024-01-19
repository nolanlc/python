

import boto3
import pprint
from botocore.client import Config

pp = pprint.PrettyPrinter(indent=2)

bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client("bedrock-agent-runtime",
                              config=bedrock_config)

model_id = 'anthropic.claude-instant-v1' # try with both claude instant as well as claude-v2. for claude v2 - "anthropic.claude-v2"
model_id = 'anthropic.claude-v2'

region_id = "us-west-2" # replace it with the region you're running sagemaker notebook
kb_id = "1HB3UXF6LJ" # replace it with the Knowledge base id.

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



#query = "What is Amazon's doing in the field of generative AI?"
query = "What is the most fundamental and all-inclusive of all the sciences?"
response = retrieveAndGenerate(query, kb_id,model_id=model_id,region_id=region_id)
generated_text = response['output']['text']
pp.pprint(generated_text)