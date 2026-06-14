# ============================================================
# 小说数据看板 - 后端 Dockerfile
# 多阶段构建: Maven 构建 → JRE Alpine 运行时
# ============================================================

# ---------- 阶段 1: 构建 ----------
FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /build

# 国内 Maven 镜像源(加速依赖下载)
RUN mkdir -p /root/.m2 && \
    echo '<?xml version="1.0" encoding="UTF-8"?>' > /root/.m2/settings.xml && \
    echo '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"' >> /root/.m2/settings.xml && \
    echo '          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' >> /root/.m2/settings.xml && \
    echo '          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 https://maven.apache.org/xsd/settings-1.0.0.xsd">' >> /root/.m2/settings.xml && \
    echo '  <mirrors>' >> /root/.m2/settings.xml && \
    echo '    <mirror>' >> /root/.m2/settings.xml && \
    echo '      <id>aliyunmaven</id>' >> /root/.m2/settings.xml && \
    echo '      <mirrorOf>*</mirrorOf>' >> /root/.m2/settings.xml && \
    echo '      <name>Aliyun Maven Mirror</name>' >> /root/.m2/settings.xml && \
    echo '      <url>https://maven.aliyun.com/repository/public</url>' >> /root/.m2/settings.xml && \
    echo '    </mirror>' >> /root/.m2/settings.xml && \
    echo '  </mirrors>' >> /root/.m2/settings.xml && \
    echo '</settings>' >> /root/.m2/settings.xml

# 1. 先只复制 pom,下载依赖(利用 Docker 缓存,改代码不会重下依赖)
COPY pom.xml .
RUN mvn -B dependency:go-offline

# 2. 复制源码,打包
COPY src ./src
RUN mvn -B clean package -DskipTests

# ---------- 阶段 2: 运行时 ----------
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# 时区设置(与 docker-compose TZ=Asia/Shanghai 配合)
RUN apk add --no-cache tzdata wget && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apk del tzdata

# 从 builder 阶段复制打包好的 jar
COPY --from=builder /build/target/app.jar app.jar

# 暴露端口
EXPOSE 8080

# JVM 容器感知参数
# -XX:+UseContainerSupport: 让 JVM 识别 cgroup 内存限制
# -XX:MaxRAMPercentage=75.0: 最多使用 75% 容器内存
# -Djava.security.egd: 加速 Tomcat 启动(避免阻塞熵池)
ENTRYPOINT ["java", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxRAMPercentage=75.0", \
    "-Djava.security.egd=file:/dev/./urandom", \
    "-jar", "app.jar"]

# 健康检查: 访问 actuator/health(Spring Boot Actuator 端点)
# 注: 当前 application.yml 启用了 actuator,但只暴露 health,info
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD wget -qO- http://localhost:8080/actuator/health || exit 1
