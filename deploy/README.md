# How to Deploy this app by hand
Because I haven't got it automated yet

1. Change the name of the project in `supervisor.conf`
2. Run this script as sudo and let it copy all of the information
3. Make sure everything is started and running
   1. `sudo supervisorctl status <project-name>`
   2. `tail /var/log/nginx/error.log`