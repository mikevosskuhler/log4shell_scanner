#!/bin/sh
# Use this to install software packages
echo "Userdata script did run" >> /tmp/script_confirmation.txt
yum install -y amazon-cloudwatch-agent
amazon-cloudwatch-agent-ctl -a start
amazon-cloudwatch-agent-ctl -a fetch-config -s -m ec2 -c ssm:AmazonCloudWatch-log4shell-stack-dns-conf
pip install requests termcolor PyCryptodome dnslib
systemctl enable ddnsserver
systemctl start ddnsserver