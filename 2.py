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
    print("Created expect script with content:")
    with open("runmynas.exp", "r") as file:
        print(file.read())
    # 确保赋予执行权限
    subprocess.run(["chmod", "+x", "runmynas.exp"], check=True)

def run_expect_script():
    try:
        subprocess.run(["./runmynas.exp"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running expect script: {e}")

def main():
    # 创建 expect 脚本并赋予执行权限
    create_expect_script()
    
    # 运行 expect 脚本
    run_expect_script()

if __name__ == "__main__":
    main()
