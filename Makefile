app_name = flask-prod-app
host_img_folder=/home/ubuntu/images
container_img_folder=/flaskAppServer/images
host_file_folder=/home/ubuntu/files
container_file_folder=/flaskAppServer/files

build:
	docker build -t $(app_name) .

run:
	docker run --name $(app_name) \
		--detach -p 8003:8003 \
		--mount type=bind,source=$(host_file_folder),target=$(container_file_folder) \
	       --mount type=bind,source=$(host_img_folder),target=$(container_img_folder) \
	       --mount type=bind,source=/var/log/cnt,target=/var/log \
	       $(app_name)

kill:
	docker stop $(app_name)
	docker container prune -f
	docker rmi -f $(app_name)

