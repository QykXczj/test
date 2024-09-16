import subprocess

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"命令执行出错: {e}")

# 克隆仓库
run_command("git clone https://github.com/linkease/iStoreNAS.git")

# 进入克隆的仓库目录
run_command("cd iStoreNAS")

# 执行脚本
run_command("./runmynas.sh rk35xx")
