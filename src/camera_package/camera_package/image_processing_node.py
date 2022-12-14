import time
from ctypes import Array

import rclpy
import cv2
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import torch
from std_msgs.msg import Float32MultiArray


class ImageProcessingNode(Node):
    # simple node to process the images
    tflitemodel = "weights/best-int8 (2).tflite"
    yolov5model600 = "weights/best_ep600_batch50.pt"
    yolov5model300 = "weights/best_ep300_batch50.pt"
    model = torch.hub.load("ultralytics/yolov5", 'custom', path=yolov5model300)

    def __init__(self):
        super().__init__('image_processing_node')
        self.bridge = CvBridge()
        self.publisher_ = self.create_publisher(Image, '/images/processed', 10)
        self.publisher_labels = self.create_publisher(Float32MultiArray, '/images/labels', 10)
        self.subscription_ = self.create_subscription(Image, '/images/raw', self.process_image_callback, 10)

    def process_image_callback(self, data):
        start = time.time()
        self.get_logger().info('<- raw image')
        frame = self.bridge.imgmsg_to_cv2(data)
        # downsize the image and convert to grayscale, to save bandwidth
        new_size = (640, 480)
        x_scale = new_size[0] / frame.shape[0]
        y_scale = new_size[1] / frame.shape[1]
        frame = cv2.resize(frame, dsize=new_size, fx=x_scale, fy=y_scale)

        cvtFrame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        output = self.model(cvtFrame)
        output.render()

        npOut = output.pandas().xyxy[0].to_numpy()
        npflat = npOut[:, :npOut.shape[1] - 1].flatten()

        npmsg = Float32MultiArray()
        for i in range(len(npflat)):
            npmsg.data.append(npflat[i])
        self.publisher_labels.publish(npmsg)
        frame = cv2.cvtColor(cvtFrame, cv2.COLOR_BGR2RGB)
        print((time.time() - start) * 1000)
        self.publisher_.publish(self.bridge.cv2_to_imgmsg(frame))
        self.get_logger().info('processed image ->')


def main(args=None):
    rclpy.init(args=args)
    image_processing_node = ImageProcessingNode()
    rclpy.spin(image_processing_node)
    image_processing_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
