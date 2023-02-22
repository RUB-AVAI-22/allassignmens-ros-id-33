import rclpy
import tf_transformations
from rclpy.node import Node
import numpy as np
import math

from avai_messages.msg import Track
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import tf_transformations
from std_msgs.msg import Bool


class AutonomousController(Node):
    def __init__(self):
        super().__init__('controller_node')

        self.speed_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.track_subscriber = self.create_subscription(Track, '/track', self.received_track_callback, 10)
        self.odom_subscriber = self.create_subscription(Odometry, '/codom', self.received_odom_callback, 10)
        self.drive_publisher = self.create_publisher(Bool, '/drive', 10)

        self.sign = -1

        self.start_position = None
        self.next_target = None
        self.target_queue = None
        self.distance_threshold = 0.08 # 8cm
        self.angular_threshold = np.deg2rad(.05) # 0,5° Abweichung
        self.lin_vel = 0

    def received_track_callback(self, track):
        self.get_logger().info("<- new track")
        self.start_position = track.start
        goal_x = track.x
        goal_y = track.y
        self.target_queue = [[x, goal_y[idx]] for idx, x in enumerate(goal_x)]
        print(self.target_queue)
        if len(self.target_queue) > 0:
            self.next_target = self.target_queue.pop(0)

    def received_odom_callback(self, odom):
        if not self.next_target is None:
            # if position is given relative have to check that
            target_distance = np.sqrt((self.next_target[0] + odom.pose.pose.position.x) ** 2 + (self.next_target[1] + odom.pose.pose.position.y) ** 2)
            if target_distance <= self.distance_threshold:
                self.get_logger().info("reached next target point")
                if len(self.target_queue) >= 1:
                    self.next_target = self.target_queue.pop()
                else:
                    self.next_target = None
                    self.speed_publisher.publish(Twist()) # values should all be zero
                    msg_bool = Bool()
                    msg_bool.data = True
                    self.drive_publisher.publish(msg_bool)

                    self.get_logger().info("completed track")
                    return

            _, _, new_yaw = tf_transformations.euler_from_quaternion(
                [odom.pose.pose.orientation.x, odom.pose.pose.orientation.y, odom.pose.pose.orientation.z,
                 odom.pose.pose.orientation.w])
            _, _, old_yaw = tf_transformations.euler_from_quaternion(
                [self.start_position.pose.pose.orientation.x, self.start_position.pose.pose.orientation.y, self.start_position.pose.pose.orientation.z,
                 self.start_position.pose.pose.orientation.w])
            delta_yaw = new_yaw + np.pi

            angle_to_target = self.angle_from_points([odom.pose.pose.position.x, odom.pose.pose.position.y], self.next_target)


            twist = Twist()
            if abs(self.normalize_radians(delta_yaw - angle_to_target)) > self.angular_threshold:
                print("drehen")
                angular_vel = self.target_dynamic(delta_yaw, angle_to_target, 1.)*2
                twist.angular.z = angular_vel
                self.lin_vel = .0
            else:
                print("vorwärts")
                self.lin_vel = .05

            print("distance:", target_distance)
            print("angle:", self.normalize_radians(abs(((delta_yaw - angle_to_target) % (np.pi*2)))))
            twist.linear.x = self.lin_vel
            self.speed_publisher.publish(twist)

            """
            angular_vel = self.target_dynamic(delta_yaw, angle_to_target, 1.) * 2
            twist = Twist()
            twist.linear.x = 0.1
            twist.angular.z = angular_vel
            self.speed_publisher.publish(twist)
            """

    @staticmethod
    def target_dynamic(robot_orientation, target_orientation, turning_speed):
        # to avoid being stuck at 180deg relative to the target. Because rate of change directly on a repeller is 0.
        if abs(AutonomousController.normalize_radians(robot_orientation - target_orientation) - np.pi) < 0.01:
            return np.pi * .25
        return -turning_speed * np.sin(robot_orientation - target_orientation)

    @staticmethod
    def normalize_radians(radians):
        rad = radians
        if rad > np.pi:
            rad -= 2. * np.pi
        elif rad < -np.pi:
            rad += 2. * np.pi
        return rad

    @staticmethod
    def angle_from_points(a, b):
        z = a[0] - b[0]
        x = a[1] - b[1]
        return (math.atan2(x, z) - np.pi)


def main(args=None):
    rclpy.init(args=args)
    node = AutonomousController()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
