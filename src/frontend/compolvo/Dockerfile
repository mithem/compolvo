FROM node:21.7

RUN mkdir -p /usr/share/compolvo
WORKDIR /usr/share/compolvo

COPY package*.json .
RUN npm install

COPY . .

ENTRYPOINT ["npm", "run"]
CMD ["dev"]