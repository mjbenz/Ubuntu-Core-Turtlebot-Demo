#!/usr/bin/env python

import roslib; roslib.load_manifest('move_confined')
import rospy
import random
from geometry_msgs.msg import Twist
from kobuki_msgs.msg import BumperEvent
from kobuki_msgs.msg import ButtonEvent
from kobuki_msgs.msg import Led
from kobuki_msgs.msg import SensorState
from kobuki_msgs.msg import Sound


class move_demo():

    # Defaults
    action_duration = 0.1
    buttonPress = 'B3'
    bump = False
    duration = 3
    neg_min_movement_speed = -0.15
    max_movement_speed = 0.2
    min_turn_duration = 3.5
    max_turn_duration = 10.5
    sensor = 9
    neg_turn_speed = -0.5
    pos_turn_speed = 0.5
    wait_for_b0_press = True
    # Sensor threshold values
    lsig = 2100
    csig = 2400
    rsig = 2150


    def __init__(self): 
        rospy.init_node('Ubuntu_Demo', anonymous=True)

        # How to stop Turtlebot
        rospy.loginfo("To stop Turtlebot CTRL + c")

        # What to do on CTRL + C
        rospy.on_shutdown(self.shutdown)

        self.cmd_vel = rospy.Publisher('/cmd_vel_mux/input/navi', Twist, queue_size=10)
        self.pub1 = rospy.Publisher('/mobile_base/commands/led1', Led, queue_size=1)
        self.pub2 = rospy.Publisher('/mobile_base/commands/led2', Led, queue_size=1)
        self.led1 = Led()
        self.led2 = Led()

        rospy.Subscriber('/mobile_base/events/bumper', BumperEvent, self.processBumperEvent)
        rospy.Subscriber('/mobile_base/events/button', ButtonEvent, self.processButtonEvent)
        rospy.Subscriber('/mobile_base/sensors/core', SensorState, self.processSensorState)


    def processButtonEvent(self, data):
        global bump
        global buttonPress
        global wait_for_b0_press

        if (data.state == ButtonEvent.RELEASED):
           state = 'released'
        else:
            state = 'pressed'

        if (data.button == ButtonEvent.Button0):
           self.wait_for_b0_press = False
           self.buttonPress = 'B0'
           # Set LED to green
           self.led1.value = 1
           self.pub1.publish (self.led1.value)
           self.bump = False

        elif (data.button == ButtonEvent.Button1):
             self.buttonPress = 'B1'
             self.wait_for_b0_press = True
             # Set LED to red
             self.led1.value = 3
             self.pub1.publish (self.led1.value)

        else:
             self.buttonPress = 'B2'
             self.wait_for_b0_press = True
             # Set LED to red
             self.led1.value = 3
             self.pub1.publish (self.led1.value)


    def processBumperEvent(self, data):
        global bump
        global wait_for_b0_press
    
        # data.bumper: LEFT (0), CENTER (1), RIGHT (2)
        # data.state: RELEASED (0), PRESSED (1)
        #rospy.loginfo("processBumperEvent called")
        if (data.state == BumperEvent.PRESSED):
           self.wait_for_b0_press = True
           self.bump = True

           if (data.bumper == BumperEvent.LEFT):
              rospy.loginfo("Left Bumper activated")
           elif (data.bumper == BumperEvent.RIGHT):
                rospy.loginfo("Right Bumper activated")
           else:
                rospy.loginfo("Center Bumper activated")


    def processSensorState(self, data):
        global sensor
        global lsig, csig, rsig
 
        # LEFT (0), CENTER (1), RIGHT (2)
        #rospy.loginfo("processSensorState called")
        #rospy.loginfo("kobuki's bottom measurement is: " + str(data.bottom))
        tup = data.bottom
        l_sig = tup[0] # Left Sensor
        c_sig = tup[1] # Center Sensor
        r_sig = tup[2] # Right Sensor

        if (l_sig > self.lsig):
           #rospy.loginfo("kobuki's left sensor tripped.")
           self.sensor = 0
        if (c_sig > self.csig):
           #rospy.loginfo("kobuki's center sensor tripped.")
           self.sensor = 1
        if (r_sig > self.rsig):
           #rospy.loginfo("kobuki's right sensor tripped.")
           self.sensor = 2


    def random_duration(self):
        # Calcutlate a random amount of time for the Turtlebot to turn
        duration = int(self.min_turn_duration + random.random() * (self.max_turn_duration - self.min_turn_duration))
        #str = "Random duration: %s"%duration
        #rospy.loginfo(str)
        return duration


    def turn(self, duration, weight):
        twist = Twist()

        # Stop and prepare to back up 
        # Send default Twist() to stop robot
        self.cmd_vel.publish(Twist())
        rospy.sleep(0.5)

        # Back up a little then move
        twist.linear.x = self.neg_min_movement_speed; twist.linear.y = 0; twist.linear.z = 0
        twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 0
        self.cmd_vel.publish(twist)
        rospy.sleep(1)
        #rospy.sleep(self.action_duration)

        # Stop and prepare to turn
        # Send default Twist() to stop robot
        self.cmd_vel.publish(Twist())
        rospy.sleep(0.5)

        # Turn until the end of specified duration
        stopTime = rospy.get_time() + duration
        while (rospy.get_time() < stopTime):
              # turn if we hit the line
              #rospy.loginfo("Turning %s"%rospy.get_time())
              #rospy.loginfo("Time %s"%rospy.get_time() + "StopTime %s"%stopTime)
              twist.linear.x = 0.0; twist.linear.y = 0; twist.linear.z = 0
              twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = weight
              self.cmd_vel.publish(twist)
              rospy.sleep(self.action_duration)

        # Stop turning
        self.cmd_vel.publish(Twist())
        rospy.sleep(0.35)
        return 0


    def wait_for_b0(self):
        while self.wait_for_b0_press:
              rospy.loginfo ("Waiting for button B0 to be pressed.")
              rospy.sleep(1)
              return


    def move_around(self):
        global sensor
        global bump
        global buttonPress
        twist = Twist()

        # Set LED to yellow
        self.led1.value = 2
        self.pub1.publish (self.led1.value)

        while self.wait_for_b0_press:
              rospy.loginfo ("Waiting for button B0 to be pressed.")
              rospy.sleep(1)

        while not self.wait_for_b0() and not rospy.is_shutdown():
              if (self.sensor == 0):
                 rospy.loginfo("Turning Left")
                 self.turn(self.random_duration(), self.pos_turn_speed)
                 rospy.sleep(self.action_duration)
                 self.sensor = 9
                 rospy.sleep(self.action_duration)

              elif (self.sensor == 1):
                   rospy.loginfo("Turning Around")
                   self.turn(self.random_duration(), self.neg_turn_speed)
                   rospy.sleep(self.action_duration)
                   self.sensor = 9
                   rospy.sleep(self.action_duration)

              elif (self.sensor == 2):
                   rospy.loginfo("Turning Right")
                   self.turn(self.random_duration(), self.neg_turn_speed)
                   rospy.sleep(self.action_duration)
                   self.sensor = 9
                   rospy.sleep(self.action_duration)
 
              elif (self.bump == True or self.buttonPress in ['B1', 'B2']):
                   rospy.loginfo ("Hit Something or B1 or B2 pressed, Stopping")
                   twist.linear.x = 0; twist.linear.y = 0; twist.linear.z = 0
                   twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 0
                   self.cmd_vel.publish(twist)
                   # Turn on LED in red
                   self.led1.value = 3
                   self.pub1.publish(self.led1.value)
                   rospy.sleep(self.action_duration)

              else:
                   #rospy.loginfo("Moving Straight")
                   twist.linear.x = self.max_movement_speed; twist.linear.y = 0; twist.linear.z = 0
                   twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 0
                   # Publish the message and delay
                   self.cmd_vel.publish(twist)
                   rospy.sleep(self.action_duration)


    def shutdown(self):
        # Stop Turtlebot
        rospy.loginfo("Stopping Turtlebot")
        # Send a default twist
        self.cmd_vel.publish(Twist())
        # Sleep to make sure Turtlebot receives stop command before shutting down
        rospy.sleep(1)


if __name__ == '__main__':
    count = 0
    try:
        move = move_demo()
        while (move.move_around() and not rospy.is_shutdown()):
              count = count + 1

    except rospy.ROSInterruptException:
        rospy.loginfo("Exception thrown")
