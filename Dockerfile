# Yapa en un solo contenedor (Render u otro host con Docker): la web construida y el motor que la sirve
FROM node:22-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY public public
COPY src src
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/api
COPY api/src src
COPY --from=web /app/dist /app/dist
ENV PYTHONPATH=src PYTHONUNBUFFERED=1
# el disco del plan gratis se borra en cada reinicio: la base de demostración se vuelve a sembrar al arrancar (S-253)
CMD python -m yapa_sdd.web --base /tmp/yapa.db --sembrar-demo --escuchar 0.0.0.0 --puerto ${PORT:-8000} --estaticos /app/dist
