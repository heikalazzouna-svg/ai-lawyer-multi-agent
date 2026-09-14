FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# We'll run in dev mode for ease of use, but in a real prod scenario we'd do 'npm run build' and 'npm start'
CMD ["npm", "run", "dev"]
