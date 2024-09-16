import subprocess

def create_expect_script():
    expect_script = """
#!/usr/bin/expect -f
set timeout -1
spawn ./runmynas.sh rk35xx
expect eof
"""
    with open("runmynas.exp", "w") as file:
        file.write(expect_script)
    subprocess.run(["chmod", "+x", "runmynas.exp"], check=True)

def run_expect_script():
    subprocess.run(["./runmynas.exp"], check=True)

def main():
    # 创建 expect 脚本并赋予执行权限
    create_expect_script()
    
    # 运行 expect 脚本
    run_expect_script()

if __name__ == "__main__":
    main()
