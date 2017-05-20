NBMON
=====

Network Baseline Monitor - v0.5a
=======

Python 2.7

#### Requires: 

- appdirs==1.4.3
- asn1crypto==0.22.0
- cffi==1.10.0
- click==6.7
- cryptography==1.8.1
- enum34==1.1.6
- idna==2.5
- ipaddress==1.0.18
- netmiko==1.4.0
- packaging==16.8
- paramiko==2.1.2
- pkg-resources==0.0.0
- pyasn1==0.2.3
- pycparser==2.17
- pyparsing==2.2.0
- PyYAML==3.12
- scp==0.10.2
- six==1.10.0
- SQLAlchemy==1.1.9

#### Purpose:
1. Create copies of the configuration files running on your network devices
1. Track periodic changes in those configurations
1. Provide an alert when changes do occur

#### Setup:
1. setup virtualenv
	- virtualenv nbmon
	- source nbmon/bin/activate
1. git clone
	- git clone https://github.com/ronwellman/nbmon.git
1. pip install
	- pip install -r requirements.txt
1. build and database
	- python nbmon.py --inputfile sample_file.json
1. run nbmon
	- python nbmon.py --daemon
1. run nbmon with logging
	- python nbmon.py --daemon --logfile nbmon.log --verbose

