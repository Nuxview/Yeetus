FROM node:20-alpine

WORKDIR /app

COPY . .

RUN npm install

RUN ./node_modules/.bin/next build
EXPOSE 3000

CMD ["npm", "start"]
