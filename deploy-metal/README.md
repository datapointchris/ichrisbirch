# deploy-metal

The configs and scripts the app ran under before it was containerized: nginx as
the reverse proxy, supervisor as the process manager, and redis on the host.
Nothing reads them, and no deploy runs them. Traefik routes and Docker
supervises, and [Blue/Green Deployment](../docs/blue-green-deployment.md) is the
deploy that replaced them.

They are kept for the port layout and worker counts the container deploy had to
reproduce. [NGINX](../docs/devops/nginx.md) and
[Supervisor](../docs/devops/supervisor.md) describe what each one set.
