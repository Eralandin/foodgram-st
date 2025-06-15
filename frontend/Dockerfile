FROM node:20 as build

WORKDIR /frontend
COPY . .
RUN npm install && npm run build
