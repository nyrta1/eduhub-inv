FROM node:22-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
root@ip-172-31-47-139:/home/ubuntu/edu/ui# cat docker-compose.yml 
services:
  ui:
    build: .
    container_name: edu-ui
    restart: unless-stopped
    ports:
      - "80:8080"