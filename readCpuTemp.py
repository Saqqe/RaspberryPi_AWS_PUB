import asyncio
import subprocess

async def get_cpu_temp():
    """
    Asynchronously fetches the CPU temperature using vcgencmd.
    """
    process = await asyncio.create_subprocess_shell(
        'vcgencmd measure_temp',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        temp_output = stdout.decode().strip()
        temp_value = temp_output.split('=')[1].split("'")[0]
        print(f"CPU temp: {temp_value} °C")
    else:
        print(f"Error fetching CPU temperature: {stderr.decode().strip()}")

async def main():
    while True:
        await get_cpu_temp()
        await asyncio.sleep(5)  # Fetch temperature every 5 seconds

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTerminated by user")

