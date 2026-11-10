"""Repast4Py smoke test: five agents per MPI rank, each taking three steps.

Run with an environment containing repast4py and mpi4py:
    python main.py
    mpiexec -n 2 python main.py
"""

from mpi4py import MPI
from repast4py import context, core, schedule


class TestAgent(core.Agent):
    def __init__(self, agent_id, rank):
        super().__init__(agent_id, 0, rank)
        self.steps = 0

    def step(self):
        self.steps += 1


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    agents = context.SharedContext(comm)
    for agent_id in range(5):
        agents.add(TestAgent(agent_id, rank))

    def step():
        for agent in agents.agents():
            agent.step()

    runner = schedule.init_schedule_runner(comm)
    runner.schedule_repeating_event(1, 1, step)
    runner.schedule_stop(3.5)
    runner.execute()

    local_agents = list(agents.agents())
    local_ok = len(local_agents) == 5 and all(a.steps == 3 for a in local_agents)
    assert comm.allreduce(local_ok, op=MPI.LAND), "Agent or scheduler test failed"
    if rank == 0:
        print(f"PASS: {5 * comm.Get_size()} agents completed three steps.")


if __name__ == "__main__":
    main()
