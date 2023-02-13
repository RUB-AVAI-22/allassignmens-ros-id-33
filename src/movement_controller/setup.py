from setuptools import setup

package_name = 'movement_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='avai@unconfigured.de',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'controller_node = movement_controller.controller_node:main',
            'autonomous_node = movement_controller.autonomous:main',
            'path_integration_node = movement_controller.path_integration:main'
        ],
    },
)
