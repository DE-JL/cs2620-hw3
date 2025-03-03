import argparse
import subprocess
import time
import random


from config import SERVER_ADDR, SERVER_PORT


def start_server(exp_name):
    """Start the server process."""
    return subprocess.Popen(
        ["python", "server.py", "--exp-name", exp_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def start_client(port, exp_name, clock_speed, prob_internal):
    """Start a client process with the given clock speed and experiment name."""
    return subprocess.Popen(
        ["python", "client.py", "localhost", str(port), "--clock-speed", str(clock_speed), "--exp-name", exp_name, "--prob-internal", str(prob_internal)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def parse_arguments():
    parser = argparse.ArgumentParser(description="Experiment Runner")
    parser.add_argument(
        "--exp-name", type=str, required=True, help="The name of the experiment"
    )
    parser.add_argument(
        "--run-time",
        type=int,
        required=True,
        help="Total time (in seconds) to run the experiment before shutting down",
    )

    parser.add_argument(
        "--prob-internal",
        type=float,
        default=0.7,
        help="The probability of an event being an internal event (default: 0.7)",
    )

    parser.add_argument(
        "--clock-speeds",
        type=int,
        nargs="*",
        help="Exactly 3 clock speeds for the clients. If not provided, 3 random values in range [1,6] will be used.",
    )

    args = parser.parse_args()

    # If no clock speeds are provided, generate exactly 3 random ones
    if args.clock_speeds is None:
        args.clock_speeds = [random.randint(1, 6) for _ in range(3)]
        print(f"No clock speeds provided. Using randomly generated: {args.clock_speeds}")

    # Ensure exactly 3 clock speeds are provided
    elif len(args.clock_speeds) != 3:
        parser.error("Exactly 3 clock speeds must be provided.")

    return args


def main():
    args = parse_arguments()
    ports = [8001, 8002, 8003]

    # Start the server
    server_proc = start_server(args.exp_name)
    time.sleep(2)  # Give the server some time to start

    # Start the clients
    client_procs = [start_client(ports[idx], args.exp_name, speed, args.prob_internal) for idx, speed in enumerate(args.clock_speeds)]

    try:
        print(f"Experiment '{args.exp_name}' running for {args.run_time} seconds...")
        time.sleep(args.run_time)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Shutting down early...")

    print("\nShutting down all processes...")

    # Terminate all clients
    for proc in client_procs:
        proc.terminate()
        proc.wait()

    # Terminate the server
    server_proc.terminate()
    server_proc.wait()

    print("All processes terminated.")


if __name__ == "__main__":
    main()
