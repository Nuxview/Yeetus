FROM node:20-alpine


WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN ./node_modules/.bin/next build
ENV NODE_ENV=production

RUN chown -R node:node /app
USER node

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

CMD ["npm", "start"]
