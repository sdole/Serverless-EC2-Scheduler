#!/usr/bin/python
import boto3
import logging
from distutils.util import strtobool

class Worker(object):
	def __init__(self, region, instance):

		self.region=region
		self.ec2Resource = boto3.resource('ec2', region_name=self.region)
		self.instance=instance

		self.instanceStateMap = {
			"pending" : 0, 
			"running" : 16,
			"shutting-down" : 32,
			"terminated" : 48,
			"stopping" : 64,
			"stopped" : 80
		}
		self.initLogging()  

	def initLogging(self):
		# Setup the Logger
		self.logger = logging.getLogger('Worker')  #The Module Name
		self.logger.setLevel(logging.INFO)
		logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s==>%(message)s', filename='Worker' + '.log', filemode='w', level=logging.INFO)
		
		###
		#Currently, this adds another logger everytime a subclass instantiated.

		# Setup the Handlers
		# create console handler and set level to debug
		# consoleHandler = logging.StreamHandler()
		# consoleHandler.setLevel(logging.INFO)
		# self.logger.addHandler(consoleHandler)



	''' probably add some convenience methods to update DynamoDB or Log Files with progress/status '''


class StartWorker(Worker):
	def __init__(self, region, instance):
		super(StartWorker, self).__init__(region, instance)
	
	def startInstance(self):
		#EC2.Instance.start()
		result=self.instance.start()
		self.logger.info('startInstance() for ' + self.instance.id + ' result is %s' % result)

	def execute(self):
		self.startInstance()





class StopWorker(Worker):
	def __init__(self, region, instance):
		super(StopWorker, self).__init__(region, instance)
		
		# MUST convert string False to boolean False
		self.waitFlag=strtobool("False")

		
	def stopInstance(self):

		self.logger.info('Worker::stopInstance() called')
		
		#EC2.Instance.stop()
		result=self.instance.stop()

		# If configured, wait for the stop to complete prior to returning
		self.logger.info('The bool value of self.waitFlag %s, is %s' % (self.waitFlag, bool(self.waitFlag)))

		
		# self.waitFlag has been converted from str to boolean via set method
		if( self.waitFlag ):
			self.logger.info(self.instance.id + ' :Waiting for Stop to complete...')
			
			# Need the Client to get the Waiter
			ec2Client=self.ec2Resource.meta.client
			waiter=ec2Client.get_waiter('instance_stopped')	

			# Waits for 40 15 second increments (e.g. up to 10 minutes)
			waiter.wait( )

		else:
			self.logger.info(self.instance.id + ' No wait for Stop to complete requested')

		self.logger.info('stopInstance() for ' + self.instance.id + ' result is %s' % result)
		
	def setWaitFlag(self, flag):

		# MUST convert string False to boolean False
		self.waitFlag = strtobool(flag)

	def getWaitFlag(self):
		return( self.waitFlag )
	
	def isOverrideFlagSet(self):
		''' Use SSM to check for existence of the override file in the guest OS.  If exists, don't Stop instance but log'''
		return False

	def execute(self):
		if( self.isOverrideFlagSet() ):
			self.logger.info('Override set for instance %s, NOT Stopping the instance' % instance.id)
		else:
			self.stopInstance()

class ScalingWorker(Worker):
	def __init__(self, region, instance, newInstanceType):
		super(ScalingWorker, self).__init__(region, instance)
		self.newInstanceType=newInstanceType

	def modifyInstanceType(self):
		#EC2.Instance.modify_attribute()
		result=self.instance.modify_attribute(
			InstanceType={
		        'Value': self.newInstanceType
		    },
		)
		self.logger.info(self.instance.id + ' :Scaling')
		self.logger.debug(result)

	def execute(self):
		instanceState = self.instance.state
		
		if( instanceState['Name'] == 'stopped' ):
			self.modifyInstanceType()
			self.logger.debug('Instance ' + self.instance.id + 'State changed to ' + self.newInstanceType)
		else:
			logMsg = 'ScalingWorker requested to change instance type for non-stopped instance ' + self.instance.id + ' no action taken'
			self.logger.warning(logMsg)
			self.logger.debug(logMsg)


