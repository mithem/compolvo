FROM debian:12

RUN apt-get update && apt-get install nodejs npm nginx -y

RUN mkdir -p /usr/share/compolvo
WORKDIR /usr/share/compolvo

COPY package*.json .
RUN npm install

COPY nginx.conf /etc/nginx/nginx.conf
COPY . .

RUN npm run build

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]