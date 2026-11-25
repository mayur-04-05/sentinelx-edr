FROM node:20-alpine

WORKDIR /app

# Copy packages configuration
COPY package*.json ./
RUN npm install

# Copy frontend source files
COPY . .

EXPOSE 3000

# Run Vite dev server bound to port 3000 on all interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
