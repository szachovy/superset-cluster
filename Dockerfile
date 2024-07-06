# Stage 1: Build
# FROM ubuntu:latest AS builder

# # Install dependencies
# RUN apt-get update && apt-get install -y \
#     mysql-client \
#     libssl-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# # Stage 2: Final
FROM mysql:8.0-debian

# # Copy mysql_config_editor from the builder stage
# COPY --from=builder /usr/bin/mysql_config_editor /usr/bin/mysql_config_editor
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libcrypto.so.3 /usr/lib64/libcrypto.so.3
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libssl.so.3 /usr/lib64/libssl.so.3
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libstdc++.so.6 /usr/lib64/libstdc++.so.6

# # Verify the installation
# RUN mysql_config_editor --help

ENTRYPOINT ["sleep", "infinity"]
