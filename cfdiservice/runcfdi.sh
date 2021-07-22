# install gunicorn
sudo yum install python-gunicorn

# start, stop, service
sudo systemctl status cfdi
sudo systemctl start cfdi
sudo systemctl restart cfdi

# reload changes in source
sudo systemctl daemon-reload
