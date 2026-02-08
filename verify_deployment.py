import paramiko
import sys

# 配置信息
NAS_HOST = "192.168.31.232"
NAS_PORT = 22
NAS_USER = "leiqy"
NAS_PASS = "L942038441."

def verify():
    try:
        print(f"Connecting to {NAS_HOST} to verify deployment...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(NAS_HOST, port=NAS_PORT, username=NAS_USER, password=NAS_PASS)

        print("Checking running containers...")
        # Check if containers are running
        stdin, stdout, stderr = ssh.exec_command(f"echo '{NAS_PASS}' | sudo -S docker ps --format '{{{{.Names}}}} {{{{.Status}}}}'")
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print("\n--- Remote Docker Containers ---")
        print(output)
        
        if "ops-agent-frontend" in output and "ops-agent-backend" in output and "ops-agent-db" in output:
            print("✅ All services are running!")
        else:
            print("⚠️ Some services might be missing or failed to start.")
            print("Error logs (if any):")
            print(error)
            
            # Fetch logs if failed
            print("\nFetching logs for ops-agent-backend...")
            stdin, stdout, stderr = ssh.exec_command(f"echo '{NAS_PASS}' | sudo -S docker logs --tail 20 ops-agent-backend")
            print(stdout.read().decode())
            print(stderr.read().decode())

        ssh.close()

    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify()
