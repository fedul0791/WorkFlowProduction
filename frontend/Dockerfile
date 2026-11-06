FROM node:24-alpine

WORKDIR /app
LABEL org.opencontainers.image.title="WorkFlow Production Frontend" \
      com.workflowproduction.project="workflow-production"
ENV WORKFLOW_FRONTEND_PROJECT=workflow-production

COPY package.json package-lock.json ./
RUN npm ci

COPY next.config.ts tsconfig.json next-env.d.ts ./
COPY src ./src
RUN node -e "const p=require('./package.json'); if(p.name!=='workflow-production-frontend') process.exit(1)" \
    && test -f src/app/de/anmelden/page.tsx \
    && test -f src/app/ru/login/page.tsx \
    && test -f src/app/en/login/page.tsx

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
