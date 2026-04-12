import sys

from data_ingestor import (
    SIMULATOR_MODE,
    generate_training_data,
    run_online_simulator,
    run_replay_simulator,
    run_secure_simulator,
    run_simulator,
)


if __name__ == "__main__":
    print("[Notice] simulator.py is kept for compatibility. Preferred entrypoint: data_ingestor.py")

    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_training_data(10000)
    elif len(sys.argv) > 1 and sys.argv[1] == "secure":
        run_secure_simulator()
    elif len(sys.argv) > 1 and sys.argv[1] == "replay":
        run_replay_simulator()
    elif len(sys.argv) > 1 and sys.argv[1] == "online":
        run_online_simulator()
    elif SIMULATOR_MODE == "online":
        run_online_simulator()
    elif SIMULATOR_MODE == "replay":
        run_replay_simulator()
    else:
        run_simulator()
