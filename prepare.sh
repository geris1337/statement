#!/bin/sh
apt update  
apt install wget curl python3 python3-pip firefox-esr -y
pip3 install -U pytest selenium requests
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
wget https://github.com/mozilla/geckodriver/releases/download/v0.28.0/geckodriver-v0.28.0-linux64.tar.gz
tar -xvzf geckodriver-v0.28.0-linux64.tar.gz
rm geckodriver-v0.28.0-linux64.tar.gz
chmod +x geckodriver
cp geckodriver /usr/local/bin/
rm geckodriver
docker-compose up -d