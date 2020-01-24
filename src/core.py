#!/usr/bin/env python

import numpy as np
import rospy
import time
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2
from autonomy.msg import motors, lines, distance, servos #, leds


class autonomy(object):

	def __init__(self):
		##USER PARAMETERS
		self.dummyParam = 30


		##Initiate variables
		self.leftLine = 0
		self.midLine = 0
		self.rightLine = 0
		self.distance = 0
		self.leftSpeed = 0
		self.rightSpeed = 0
		self.pan = 0
		self.tilt = 0
		self.bridge = CvBridge()

                self.errorSum = 0
                self.errorLast = 0
                self.distanceLast1 = 0
                self.distanceLast2 = 0


		#Setup Publishers
		self.motorPub = rospy.Publisher('motors', motors, queue_size=10)
		self.servoPub = rospy.Publisher('servos', servos, queue_size=10)
		#self.LEDpub = rospy.Publisher('leds', leds, queue_size=10)


		#Create Subscriber callbacks
		def lineCallback(data):
			self.leftLine = data.leftLine
			self.midLine = data.midLine
			self.rightLine = data.rightLine

		def distanceCallback(data):
			self.distance = data.distance


		def imageProcessing(data):
			try:
				frame=self.bridge.imgmsg_to_cv2(data,desired_encoding="passthrough")
			except CvBridgeError as e:
				print(e)

			##Place image processing code here!
			#cv2.imwrite('test.jpg',frame)


		#Subscribe to topics
		rospy.Subscriber('raspicam_node/image',Image,imageProcessing)
		rospy.Subscriber('lines', lines, lineCallback)
		rospy.Subscriber('distance', distance, distanceCallback)

		rospy.init_node('core', anonymous=True)
		self.rate = rospy.Rate(10)

	def publishMotors(self):
		motorMsg = motors()
		motorMsg.leftSpeed = self.leftSpeed
		motorMsg.rightSpeed = self.rightSpeed
		rospy.loginfo(motorMsg)
		self.motorPub.publish(motorMsg)

	def publishServo(self):
		servoMsg = servos()
		servoMsg.pan = self.pan
		servoMsg.tilt = self.tilt
		rospy.loginfo(servoMsg)
		self.servoPub.publish(servoMsg)

#	def publishLED(self):
#		LEDmsg = leds()
#		LEDmsg.r1 = 255
#		LEDmsg.g1 = 0
#		LEDmsg.b1 = 0
#		LEDmsg.r2 = 0
#		LEDmsg.g2 = 255
#		LEDmsg.b2 = 0
#		LEDmsg.r3 = 0
#		LEDmsg.g3 = 0
#		LEDmsg.b3 = 255
#		rospy.loginfo(LEDmsg)
#		self.LEDpub.publish(LEDmsg)
        
        def distanceMaintenance(self):
        
			## Place code here
                    speed  = 0
                    errorCurr = 0
                    
                    ## ********** Config paremeter ******** 
                    kp = 0.35
                    ki = 0.6
                    kd = 0.020
                    targetUltr = 0.195
                    ## ************************************
                    
                    ## ****** Distance average filter *****
                    distanceCurr = self.distance
                    distanceAver = (distanceCurr + self.distanceLast1 + self.distanceLast2)/3
                    errorCurr = distanceAver - targetUltr
                    self.distanceLast2 = self.distanceLast1
                    self.distanceLast1 = distanceCurr
                    # *************************************

                    self.errorSum += errorCurr * 0.01

                    integralBound = 0.3
                    if self.errorSum > integralBound:
                        self.errosrSum = integralBound
                    if self.errorSum < (-1 * integralBound):
                        self.errorSum = -1 * integralBound

                    speed  = kp * errorCurr + ki * self.errorSum + kd * (errorCurr - self.errorLast) / 0.01 # Calculate PID output
                                       
                                        
                    ## ******* Add speed setpoint *********
                    # Minimum speed for the car to start moving
                    if speed > 0:
                        speed += 0.11
                    if speed < 0:
                        speed -= 0.155
                    ## ************************************ 
                    
                    ## ******** Restrict output ***********
                    #if speed > 0.3:
                    #    speed  = 0.3
                    #if speed < -0.3:
                    #    speed = -0.3
                    # *************************************
                   
                    ## *** Measure setpoint (for debug) ***
                    #speed  = -0.13
                    ## ************************************
                    self.errorLast = errorCurr # Update errorLast

                    return speed


	def runner(self):
		while not rospy.is_shutdown():
                    self.leftSpeed = self.distanceMaintenance()
                    self.rightSpeed = self.distanceMaintenance()

                    

			##Leave these lines at the end
		    self.publishMotors()
		    self.publishServo()
#			self.publishLED()
		    self.rate.sleep()


if __name__ == '__main__':
	autonomy().runner()
