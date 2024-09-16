import os
import subprocess

def run_command(command, cwd=None):
    try:
        subprocess.run(command, check=True, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"命令执行出错: {e}")

# 克隆仓库
run_command("git clone https://github.com/linkease/iStoreNAS.git")

# 进入克隆的仓库目录
os.chdir("iStoreNAS")

# 赋予权限
run_command("chmod +x runmynas.sh")

def create_expect_script():
    expect_script = """
#!/usr/bin/expect -f
set timeout -1
spawn ./runmynas.sh rk35xx
expect eof
"""
    with open("runmynas.exp", "w") as file:
        file.write(expect_script)

# 创建 expect 脚本并赋予执行权限
create_expect_script()

# 赋予权限
run_command("chmod +x runmynas.exp")

# 执行 expect 脚本
run_command("./runmynas.exp")
