# build env
FROM node:22.9.0-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build
CMD cp -r build result_build
