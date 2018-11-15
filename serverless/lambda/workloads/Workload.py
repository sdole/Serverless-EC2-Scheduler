import json
import logging
from utils.DataServices import DataServices

# setup logging service
logLevel = os.environ['LOG_LEVEL']
logger = logging.getLogger(__name__)
logger.setLevel(logLevel);


# setup services
dynamoDBRegion = os.environ['DYNAMODB_REGION']

# Instantiation of these services provide boto3 connection pools across lambda invocations
dataService =  DataServices(dynamoDBRegion, logLevel);


def lambda_handler(event, context):
  # Informational logging
  logger.info("Received event: " + json.dumps(event, indent=2));

  # Extract workload identifier from APIG Proxy event type
  workloadSpecName = event['params']['path']['workload'];
  logger.info("Scheduler: workload = " + workloadSpecName);

  # get data services
  # global dataService
  # if (dataService == None):
  #   dataService = DataServices(dynamoDBRegion, logLevel);

  # Lookup workload details
  workloadSpec = dataService.lookupWorkloadSpecification(workloadSpecName);

  # return workload details
  return (
    {
      'statusCode': 200,
      'headers': {
        'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'
      },
      'body': workloadSpec,
    }
  );
