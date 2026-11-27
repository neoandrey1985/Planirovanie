# --- build stage ---
FROM maven:3.9-eclipse-temurin-26 AS build
WORKDIR /app
COPY pom.xml .
# Retry Maven Central on transient 429 / network blips (CI flake).
RUN set -eux; \
    for i in 1 2 3 4 5; do \
      mvn -q -B -ntp dependency:go-offline && break; \
      echo "mvn go-offline failed (attempt $i), retrying…"; \
      sleep $((i * 15)); \
      if [ "$i" -eq 5 ]; then exit 1; fi; \
    done
COPY src ./src
RUN set -eux; \
    for i in 1 2 3; do \
      mvn -q -B -ntp -DskipTests package && break; \
      echo "mvn package failed (attempt $i), retrying…"; \
      sleep $((i * 15)); \
      if [ "$i" -eq 3 ]; then exit 1; fi; \
    done

# --- run stage ---
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/planirovanie-api-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
