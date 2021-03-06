#!/usr/bin/python

# imports
import json
import rospy
import time
from std_msgs.msg import Bool, String

import numbers
import math


class Tac1_Node():
    def __init__(self):
        # ROS init
        self.node_name = self.__class__.__name__
        rospy.init_node(self.node_name, anonymous=True)
        self.rate = rospy.Rate(10)  # 10Hz

        # ROS subscriptions
        self.subscriber = rospy.Subscriber('Biobot_To_Tac1', String, self.callback_biobot_to_tac1)
        self.subscriber = rospy.Subscriber('SerialNode_To_Tac1', String, \
                                           self.callback_serialnode_to_tac1)

        # ROS publishments
        self.tac1_to_biobot = rospy.Publisher('Tac1_To_Biobot', String, queue_size=10)
        self.tac1_to_serialnode = rospy.Publisher('Tac1_To_SerialNode', String, queue_size=10)

        #config parameters
        self.parameters={'P': 7.0, 'I': 1.0, 'D': 0.0, 'Tmin': 0, 'Tmax': 55}
        self.start = False
        self.calib_values = {'turb_0': 0, 'turb_100': 0}
        self.actual_values = {'actual_temperature': 0, 'actual_turbidity': 0}

    # Callback for Biobot_To_Tac1
    def callback_biobot_to_tac1(self, data):
        msg = json.loads(data.data)
        if 'action' in msg:
            if msg['action'] == 'config':
                print('config : ')
                if 'params' in msg:
                    print(msg['params'])
                    self.parameters.update(msg['params'])
                    self.send_parameters()
                else:
                    print('no params in message')
            elif msg['action'] == 'calibrate':
                print('calibrate : ')
                if 'params' in msg:
                    print(msg['params'])
                    if msg['params'] == 100:
                        self.send_calibrate(True)
                    elif msg['params'] == 0:
                        self.send_calibrate(False)
                else:
                    print('no params in message')
            elif msg['action'] == 'start':
                print('start : ')
                if 'params' in msg:
                    print(msg['params'])
                    if msg['params'] == True:
                        self.send_start(True)
                        self.start=True;
                    else:
                        self.send_start(False)
                        self.start=False
                else:
                    print('no params in message')
            else:
                print('invalid action')
        else:
            print('no action in message')

    # Callback for SerialNode_To_Tac1
    def callback_serialnode_to_tac1(self, data):
        msg = json.loads(data.data)
        print(json.dumps(msg))
        if 'action' in msg:
            if msg['action'] == 'calibration_result':
                print('calibration_result : ')
                if 'turb_0' in msg:
                    print("turb_0 : ")
                    print(msg['turb_0'])
                    self.calib_values.update(msg)
                    self.send_calib_values(False)
                elif 'turb_100' in msg:
                    print("turb_100 : ")
                    print(msg['turb_100'])
                    self.calib_values.update(msg)
                    self.send_calib_values(True)

            elif msg['action'] == 'actual_values':
                print('actual_values : ')
                if 'actual_temperature' in msg:
                    print("actual temperature : ")
                    print(msg['actual_temperature'])
                if 'actual_turbidity' in msg:
                    print("actual turbidity : ")
                    print(msg['actual_turbidity'])
                self.actual_values.update(msg)
                self.send_actual_values()
            else:
                print('invalid action')
        else:
            print('no action in message')

    def send_parameters(self):
        send=True
        if not 'target_temperature' in self.parameters:
            send=False
            print('no target temperature')
        if not 'target_turbidity' in self.parameters:
            send=False
            print('no target turbidity')
        if not 'refresh_rate' in self.parameters:
            send=False
            print('no refresh rate')
        if not 'motor_speed' in self.parameters:
            send=False
            print('no motor speed')
        if not 'target_temperature_goal' in self.parameters:
            send=False
            print('no target temperature post goal')
        if not 'target_turbidity_goal' in self.parameters:
            send=False
            print('no target turbidity post goal')
        if not 'refresh_rate_goal' in self.parameters:
            send=False
            print('no refresh rate post goal')
        if not 'motor_speed_goal' in self.parameters:
            send=False
            print('no motor speed post goal')
        if send:
            self.check_parameters_limit()
            json_msg = {
                'a': 'g',
                'params': True
            }
            self.tac1_to_serialnode.publish(json.dumps(json_msg))
            time.sleep(2)
            json_msg = {
                'a': 'p',
                't': self.parameters['target_temperature'],
                'u': self.parameters['target_turbidity'],
                'r': self.parameters['refresh_rate'],
                'm': self.parameters['motor_speed'],
                'tg': self.parameters['target_temperature_goal'],
                'ug': self.parameters['target_turbidity_goal'],
                'rg': self.parameters['refresh_rate_goal'],
                'mg': self.parameters['motor_speed_goal'],
                'p':  self.parameters['P'],
                'i': self.parameters['I'],
                'd': self.parameters['D'],
                'Tmin': self.parameters['Tmin'],
                'Tmax': self.parameters['Tmax']
            }
            self.tac1_to_serialnode.publish(json.dumps(json_msg))
            json_msg = {
                'a': 'g',
                'params': 'False'
            }
            self.tac1_to_serialnode.publish(json.dumps(json_msg))
        else:
            print('one parameters or more not received')

    def check_parameters_limit(self):
        if self.parameters['target_temperature'] > self.parameters['Tmax']:
            self.parameters['target_temperature'] = self.parameters['Tmax']
            print('target_temp higher than Tmax, set to Tmax')
        elif self.parameters['target_temperature'] < self.parameters['Tmin']:
            self.parameters['target_temperature'] = self.parameters['Tmin']
            print('target_temp lower than Tmin, set to Tmin')

        if self.parameters['target_turbidity'] > 100:
            self.parameters['target_turbidity'] = 100
            print('target_turb higher than 100, set to 100')
        elif self.parameters['target_turbidity'] < 0:
            self.parameters['target_turbidity'] = 0
            print('target_turb lower than 0, set to 0')

        if self.parameters['refresh_rate'] > 10000:
            print('Warning: refresh_rate higher than 10s')
        if self.parameters['refresh_rate'] < 100:
            self.parameters['refresh_rate'] = 100
            print('refresh_rate lower than 100ms, set to 100ms')

        if self.parameters['motor_speed'] > 100:
            self.parameters['motor_speed'] = 100
            print('motor_speed higher than 100, set to 100')
        elif self.parameters['motor_speed'] < 0:
            self.parameters['motor_speed'] = 0
            print('motor_speed lower than 0, set to 0')

    def send_calibrate(self, data):
        json_msg = {}
        json_msg['a']='c'
        if data:
            json_msg['params'] = 100
        else:
            json_msg['params'] = 0
        self.tac1_to_serialnode.publish(json.dumps(json_msg))

    def send_start(self, data):
        json_msg = {}
        json_msg['a']='s'
        if data:
            json_msg['params'] = True
        else:
            json_msg['params'] = False
        self.tac1_to_serialnode.publish(json.dumps(json_msg))

    def send_calib_values(self, data):
        json_msg = {}
        json_msg['action']='calibration_result'
        if data:
            json_msg['turb_100'] = self.calib_values['turb_100']
        else:
            print(json_msg)
            json_msg['turb_0'] = self.calib_values['turb_0']
        self.tac1_to_biobot.publish(json.dumps(json_msg))

    def send_actual_values(self):
        json_msg = {
            'action': 'actual_values',
            'time': int(time.time()),
            'target_temperature': self.parameters['target_temperature'],
            'target_turbidity': self.parameters['target_turbidity'],
            'refresh_rate': self.parameters['refresh_rate'],
            'motor_speed': self.parameters['motor_speed'],
            'target_temperature_goal': self.parameters['target_temperature_goal'],
            'target_turbidity_goal': self.parameters['target_turbidity_goal'],
            'refresh_rate_goal': self.parameters['refresh_rate_goal'],
            'motor_speed_goal': self.parameters['motor_speed_goal'],
            'turb_0' = self.calib_values['turb_0'],
            'turb_100' = self.calib_values['turb_100']
        }
        json_msg.update(self.actual_values)
        self.tac1_to_biobot.publish(json.dumps(json_msg))

    def listener(self):
        rospy.spin()

# Main function
if __name__ == '__main__':

    try:
        tn = Tac1_Node()
        tn.listener()

    except rospy.ROSInterruptException as e:
        print(e)

