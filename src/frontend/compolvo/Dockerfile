FROM node:21.7

RUN mkdir -p /usr/share/compolvo
WORKDIR /usr/share/compolvo
COPY . .

RUN npm install

ENTRYPOINT ["npm", "run", "dev"]