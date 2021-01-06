#!/usr/bin/python

"""
==========
ROS node to drive a differential drive robot (Jetbot2) from twist messages. It assumes Adafruit MotorHat libraries have already been installed
This code implements the following functionality:
  > Subscribes to twist messages
  > Configures the open loop controller based on the parameters from the parameter server
  > Sets output PWM values for the motors, option to publish it as an array (see drive_ackermann.py)
by Aditya Kamath
adityakamath.github.io
github.com/adityakamath
==========
"""
import rospy
from Adafruit_MotorHAT import Adafruit_MotorHAT
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
import time

class DriveDifferential():
    def __init__(self):

        rospy.init_node('drive_differential')
        rospy.loginfo("[DFF] Differential Drive application initialized")
        
        if rospy.has_param('/drive'):
            self.max_pwm = rospy.get_param('/drive/max_pwm')
            self.k_speed = rospy.get_param('/drive/k_speed')
            self.k_angular = rospy.get_param('/drive/k_angular')
            rospy.loginfo("[DFF] Loaded config paramters: /drive")
        else:
            rospy.logerr("[DFF] Config parameter not found: /drive")
                    
        # setup motor controller
        motor_driver = Adafruit_MotorHAT(i2c_bus=1)
        self.motor_left_ID = 1
        self.motor_right_ID = 2
        self.motor_left = motor_driver.getMotor(self.motor_left_ID)
        self.motor_right = motor_driver.getMotor(self.motor_right_ID)
        rospy.loginfo("[DFF] Actuators initialized")

        #--- Create the Subscriber to read Twist commands
        self.ros_sub_twist = rospy.Subscriber("/cmd_vel", Twist, self.set_actuators_from_cmdvel, queue_size=1)
        rospy.loginfo("[DFF] Twist Subscriber initialized")
        
        #--- Create the Subscriber to read IMU data
        self.ros_sub_imu = rospy.Subscriber("/imu", Imu, self.imu_sub_callback, queue_size=1)
        self.imu_msg = Imu()
        rospy.loginfo("[DFF] IMU Subscriber initialized")
        
        #--- Create the motor array publisher if needed
        #self.ros_pub_servo_array = rospy.Publisher("/servos_absolute", ServoArray, queue_size=1)
        #rospy.loginfo("[ACK] Servo Publisher initialized")

        #--- Get the last time e got a commands
        self._last_time_cmd_rcv = time.time()
        self._timeout_s = 5

        rospy.loginfo("[DFF] Initialization complete")
        
    def set_actuators_from_cmdvel(self, msg):
        """
        Get a message from cmd_vel, assuming a maximum input of 1
        """
        #-- Save the time
        self._last_time_cmd_rcv = time.time()
        
        ## rospy.loginfo("[DFF] cmd_anglev: %f   measured_anglev: %f" %(msg.angular.z, self.imu_msg.angular_velocity.z))
        ## ADD PID CONTROLLER HERE
        #rospy.loginfo("[DFF] Received command: Linear = %2.1f , Angular = %2.1f"%(msg.linear.x, msg.angular.z))
        
        lmotor_speed = self.k_speed*(msg.linear.x - 0.5*self.k_angular*msg.angular.z)
        rmotor_speed = self.k_speed*(msg.linear.x + 0.5*self.k_angular*msg.angular.z)
            
        self.send_motor_msg(self.motor_left_ID,  lmotor_speed)
        self.send_motor_msg(self.motor_right_ID,  rmotor_speed)
        
    def imu_sub_callback(self, msg):
        self.imu_msg = msg

    # sets motor speed between [-1.0, 1.0]
    def send_motor_msg(self, motor_ID, value):
        max_pwm = self.max_pwm
        speed = int(min(max(abs(value * max_pwm), 0), max_pwm))

        if motor_ID == 1:
            motor = self.motor_left
            #m_name = "L"
        elif motor_ID == 2:
            motor = self.motor_right
            #m_name = "R"
        else:
            rospy.logerror('[DFF] set_speed(%d, %f) -> invalid motor_ID=%d', motor_ID, value, motor_ID)
            return

        motor.setSpeed(speed)

        if value > 0:
            motor.run(Adafruit_MotorHAT.FORWARD)
            #rospy.loginfo("[DFF] Sending PWM: %s Motor = %d"%(m_name, speed))
        else:
            motor.run(Adafruit_MotorHAT.BACKWARD)
            #rospy.loginfo("[DFF] Sending PWM: %s Motor = %d"%(m_name, -1*speed))
                                                               
    def set_actuators_idle(self):
        self.motor_left.setSpeed(0)
        self.motor_right.setSpeed(0)

        self.motor_left.run(Adafruit_MotorHAT.RELEASE)
        self.motor_right.run(Adafruit_MotorHAT.RELEASE)     

    @property
    def is_controller_connected(self):
        #print time.time() - self._last_time_cmd_rcv
        return(time.time() - self._last_time_cmd_rcv < self._timeout_s)

    def run(self):

        #--- Set the control rate
        rate = rospy.Rate(1000)

        while not rospy.is_shutdown():
            #print self._last_time_cmd_rcv, self.is_controller_connected
            if not self.is_controller_connected:
                self.set_actuators_idle()

            rate.sleep()

if __name__ == "__main__":
    jetbot2 = DriveDifferential()
    jetbot2.run()
