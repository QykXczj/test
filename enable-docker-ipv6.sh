#!/bin/bash

# Docker IPv6配置一键启用脚本
# 此脚本必须在宿主机系统上运行，不是在Docker容器内

# 检查是否有root权限
if [ "$(id -u)" -ne 0 ]; then
    echo "错误: 此脚本需要root权限，请使用sudo运行"
    exit 1
fi

# 设置颜色
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # 恢复默认颜色

echo -e "${YELLOW}开始配置Docker IPv6支持...${NC}"
echo -e "${YELLOW}注意: 此脚本在宿主机系统上执行，不是在Docker容器内${NC}"

# 设置daemon.json路径
DAEMON_JSON="/etc/docker/daemon.json"
BACKUP_FILE="${DAEMON_JSON}.bak.$(date +%Y%m%d%H%M%S)"

# 创建目录（如果不存在）
mkdir -p /etc/docker

# 备份现有配置
if [ -f "$DAEMON_JSON" ]; then
    echo -e "${YELLOW}备份现有配置到 ${BACKUP_FILE}${NC}"
    cp "$DAEMON_JSON" "$BACKUP_FILE"
    EXISTING_CONFIG=$(cat "$DAEMON_JSON")
else
    echo -e "${YELLOW}未找到现有配置，将创建新配置文件${NC}"
    EXISTING_CONFIG="{}"
fi

# 准备IPv6配置
IPV6_CONFIG='{
  "ipv6": true,
  "fixed-cidr-v6": "2001:db8:1::/64",
  "experimental": true,
  "ip6tables": true
}'

# 合并配置（需要安装jq工具）
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}未检测到jq工具，尝试安装...${NC}"
    
    # 尝试使用apt（Debian/Ubuntu）
    if command -v apt &> /dev/null; then
        apt update && apt install -y jq
    # 尝试使用yum（CentOS/RHEL）
    elif command -v yum &> /dev/null; then
        yum install -y jq
    # 尝试使用dnf（Fedora）
    elif command -v dnf &> /dev/null; then
        dnf install -y jq
    # 尝试使用pacman（Arch Linux）
    elif command -v pacman &> /dev/null; then
        pacman -Sy jq --noconfirm
    else
        echo -e "${RED}无法安装jq工具，请手动安装后重试${NC}"
        exit 1
    fi
fi

# 合并配置
echo "$EXISTING_CONFIG" | jq -s '.[0] * .[1]' - <(echo "$IPV6_CONFIG") > "$DAEMON_JSON"

echo -e "${GREEN}已成功更新Docker配置支持IPv6${NC}"
echo -e "${YELLOW}正在重启Docker服务以应用更改...${NC}"

# 重启Docker服务（根据不同的系统）
if command -v systemctl &> /dev/null; then
    systemctl restart docker
    echo -e "${GREEN}Docker服务已重启${NC}"
elif command -v service &> /dev/null; then
    service docker restart
    echo -e "${GREEN}Docker服务已重启${NC}"
else
    echo -e "${YELLOW}无法自动重启Docker服务，请手动重启${NC}"
fi

echo -e "${GREEN}配置完成! Docker现在应该支持IPv6了${NC}"
echo -e "${YELLOW}您可能需要重新创建网络或重启容器以应用IPv6配置${NC}"
echo -e "${YELLOW}如需还原配置，请执行: sudo cp ${BACKUP_FILE} ${DAEMON_JSON} && sudo systemctl restart docker${NC}" 