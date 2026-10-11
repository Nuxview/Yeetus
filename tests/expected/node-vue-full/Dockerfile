FROM node:20-alpine


WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ENV NODE_ENV=production

RUN chown -R node:node /app
USER node

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8080/', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

CMD ["npm", "run", "serve"]
