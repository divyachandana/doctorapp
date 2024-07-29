import subprocess
import re

def get_gpu_metrics():
    try:
        # Run rocm-smi and capture the output
        result = subprocess.run(['rocm-smi'], capture_output=True, text=True)
        output = result.stdout

        # Clean the output to remove escape sequences and unnecessary lines
        cleaned_output = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', output)
        lines = cleaned_output.splitlines()
        
        for line in lines:
            if line.startswith("0"):  # Adjust this to parse other GPUs if necessary
                parts = re.split(r'\s+', line.strip())
                temp = parts[4]
                power = parts[5]
                mem_usage = parts[8]
                fan = parts[11]
                pwr_cap = parts[13]
                vram = parts[14]
                gpu = parts[15]

                # Clean and convert to appropriate types
                temp = float(temp.replace("°C", ""))
                power = float(power.replace("W", ""))
                fan = float(fan.replace("%", ""))
                pwr_cap = float(pwr_cap.replace("W", "")) if pwr_cap != "Unsupported" else None
                vram = int(vram.replace("%", ""))
                gpu = int(gpu.replace("%", ""))
                mem_usage = int(mem_usage.replace("%", ""))

                return gpu, temp, vram, fan, pwr_cap, mem_usage

        return None, None, None, None, None
    except Exception as e:
        print(f"Error fetching GPU metrics: {e}")
        return None, None, None, None, None

# if __name__ == "__main__":
#     gpu_utilization, gpu_temp, vram_usage, fan_speed, power_cap = get_gpu_metrics()
#     if gpu_utilization is not None:
#         print(f"GPU Utilization: {gpu_utilization}%")
#         print(f"GPU Temperature: {gpu_temp}°C")
#         print(f"VRAM Usage: {vram_usage}%")
#         print(f"Fan Speed: {fan_speed}%")
#         print(f"Power Cap: {power_cap}W")
#     else:
#         print("Failed to retrieve GPU metrics.")

