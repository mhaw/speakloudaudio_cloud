import subprocess
import time

def stop_docker_container(container_name):
    try:
        # Use docker kill instead of stop
        result = subprocess.run(
            ["sudo", "docker", "kill", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            print(f"Successfully killed container '{container_name}'")
            return True
        else:
            print(f"Error killing container '{container_name}': {result.stderr.strip()}")
            if "permission denied" in result.stderr.lower():
                print("Permission denied: You might need to run the script with elevated privileges (e.g., using sudo).")
            return False
    except Exception as e:
        print(f"Exception occurred while killing container '{container_name}': {str(e)}")
        return False

def remove_docker_container(container_name, force=False):
    try:
        # Run docker rm command to remove the container with sudo
        cmd = ["sudo", "docker", "rm", container_name]
        if force:
            cmd.append("-f")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            print(f"Successfully removed container '{container_name}'")
        else:
            print(f"Error removing container '{container_name}': {result.stderr.strip()}")
            if "permission denied" in result.stderr.lower():
                print("Permission denied: You might need to run the script with elevated privileges (e.g., using sudo).")
    except Exception as e:
        print(f"Exception occurred while removing container '{container_name}': {str(e)}")

if __name__ == "__main__":
    container_name = "speakloudaudio_cloud"

    # Stop the container first
    stopped_successfully = stop_docker_container(container_name)

    if not stopped_successfully:
        print("Attempting force removal of the container...")
        remove_docker_container(container_name, force=True)
    else:
        # Allow some time for Docker to register the container as stopped
        time.sleep(1)
        # Remove the container
        remove_docker_container(container_name)